
node {
    hasFailed = false
    sh 'sudo /var/lib/jenkins/jenkins-chown'
    deleteDir() // wipe out the workspace

    properties([
      parameters([
        //[$class: 'StringParameterDefinition',  name: 'BUILD_BRANCH', defaultValue: 'master'],
        [$class: 'StringParameterDefinition',  name: 'BUILD_BRANCH', defaultValue: 'master'],
        [$class: 'StringParameterDefinition',  name: 'MODEL_NAME', defaultValue: 'HailAUS'],
        [$class: 'StringParameterDefinition',  name: 'MODEL_SUPPLIER', defaultValue: 'RiskFrontiers'],
        [$class: 'StringParameterDefinition',  name: 'MODEL_BRANCH', defaultValue: BRANCH_NAME],
        [$class: 'StringParameterDefinition',  name: 'OASISLMF_BRANCH', defaultValue: ''],
        [$class: 'StringParameterDefinition',  name: 'DATA_VER', defaultValue: ''],
        [$class: 'StringParameterDefinition',  name: 'DATA_MNT', defaultValue: '/mnt/efs/riskfrontiers/model_data'],
        [$class: 'StringParameterDefinition',  name: 'TAG_RELEASE', defaultValue: BRANCH_NAME.split('/').last() + "-${BUILD_NUMBER}"],
        [$class: 'StringParameterDefinition',  name: 'TAG_OASIS', defaultValue: ''],
        [$class: 'StringParameterDefinition',  name: 'RUN_TESTS', defaultValue: '0_case'],
        [$class: 'BooleanParameterDefinition', name: 'PURGE', defaultValue: Boolean.valueOf(true)],
        [$class: 'BooleanParameterDefinition', name: 'PUBLISH', defaultValue: Boolean.valueOf(false)],
        [$class: 'BooleanParameterDefinition', name: 'SLACK_MESSAGE', defaultValue: Boolean.valueOf(false)]
      ])
    ])

    // Build vars
    String build_repo = 'git@github.com:OasisLMF/build.git'
    String build_branch = params.BUILD_BRANCH
    String build_workspace = 'oasis_build'
    String build_sh        = '/buildscript/utils.sh'
    String script_dir = env.WORKSPACE + "/" + build_workspace
    String PIPELINE = script_dir + "/buildscript/pipeline.sh"
    String git_creds = "8b00f5fd-31c7-4a78-8120-e5632bdb9c5f"

    // Model vars
    String model_supplier   = params.MODEL_SUPPLIER
    String model_varient    = params.MODEL_NAME
    String model_branch     = params.MODEL_BRANCH
    String model_git_url    = "git@github.com:risk-frontiers/OasisComplexModel.git"
    String model_workspace  = "${model_varient}_workspace"
    String model_image      = "coreoasis/rf_hail"
    String model_dockerfile = "Dockerfile.custom_model_worker"
    String model_test_dir  = "${env.WORKSPACE}/${model_workspace}/tests/"

    try {
        parallel(
            clone_build: {
                stage('Clone: ' + build_workspace) {
                    dir(build_workspace) {
                       git url: build_repo, credentialsId: git_creds, branch: build_branch
                    }
                }
            },
            clone_model: {
                stage('Clone Model') {
                    dir(model_workspace) {
                        git url: model_git_url, credentialsId: git_creds, branch: model_branch
                    }
                }
            }
        )
        stage('Shell Env'){
            // Set Pipeline helper script
            env.PIPELINE_LOAD =  script_dir + build_sh

            // TESTING VARS
            env.TEST_MAX_RUNTIME = '3600'
            env.TEST_DATA_DIR    = model_test_dir
            env.MODEL_SUPPLIER   = model_supplier
            env.MODEL_VARIENT    = model_varient
            env.MODEL_ID         = '7.0.0.0'
            env.MODEL_MOUNT_TARGET = '/var/oasis/model_data'
            env.COMPOSE_PROJECT_NAME = UUID.randomUUID().toString().replaceAll("-","")

            // SELECT MODEL DATA
            def vers_data = readJSON file: "${env.WORKSPACE}/${model_workspace}/data_version.json"
            if (params.DATA_VER?.trim()) {
                env.OASIS_MODEL_DATA_DIR = "${params.DATA_MNT}/${params.DATA_VER}"
            } else {
                env.OASIS_MODEL_DATA_DIR = "${params.DATA_MNT}/${vers_data['DATA_VER']}"
            }

            // RUN PLATFORM
            if (params.TAG_OASIS?.trim()) {
                env.TAG_RUN_PLATFORM = params.TAG_OASIS
            } else {
                env.TAG_RUN_PLATFORM = vers_data['OASIS_API_VER']
            }

            // RUN WORKER
            env.IMAGE_WORKER     = model_image
            env.TAG_RUN_WORKER   = params.TAG_RELEASE

            // Print ENV
            sh  PIPELINE + ' print_model_vars'
        }

        stage('Build:'){
            dir(model_workspace) {
                 if (params.OASISLMF_BRANCH?.trim()) {
                     sh "sed -i 's|.*oasislmf.*|-e git+git://github.com/OasisLMF/OasisLMF.git@${params.OASISLMF_BRANCH}#egg=oasislmf|g' requirements.txt"
                 }
                 sh "docker build --no-cache -f ${model_dockerfile} --build-arg worker_ver=${env.TAG_RUN_PLATFORM} -t ${model_image}:${env.TAG_RELEASE} ."
            }
        }

        stage('Run: API Server') {
            dir(build_workspace) {
                sh PIPELINE + " start_model"
            }
        }

        api_server_tests = params.RUN_TESTS.split()
        for(int i=0; i < api_server_tests.size(); i++) {
            stage("Run : ${api_server_tests[i]}"){
                dir(build_workspace) {
                    sh PIPELINE + " run_test --test-case ${api_server_tests[i]}"
                }
            }
        }

        if(params.PUBLISH){
            // GIT TAG

            // NOTE: tagging not working -> either change relationship (publish if tagged build) or fix here
            //sshagent (credentials: [git_creds]) {
            //    dir(model_workspace) {
            //        sh PIPELINE + " git_tag ${env.TAG_RELEASE}"
            //    }
            //}

            // DOCKER PUSH    
            stage ("Publish: ${model_image}:${params.TAG_RELEASE}") {
                dir(build_workspace) {
                    sh PIPELINE + " push_image ${model_image}  ${params.TAG_RELEASE}"
                }
            }
        }


    } catch(hudson.AbortException | org.jenkinsci.plugins.workflow.steps.FlowInterruptedException buildException) {
        hasFailed = true
        error('Build Failed')
    } finally {
        //Docker house cleaning
        dir(build_workspace) {
            sh 'docker-compose -f compose/oasis.platform.yml -f compose/model.worker.yml logs server-db      > ./stage/log/server-db.log '
            sh 'docker-compose -f compose/oasis.platform.yml -f compose/model.worker.yml logs server         > ./stage/log/server.log '
            sh 'docker-compose -f compose/oasis.platform.yml -f compose/model.worker.yml logs celery-db      > ./stage/log/celery-db.log '
            sh 'docker-compose -f compose/oasis.platform.yml -f compose/model.worker.yml logs rabbit         > ./stage/log/rabbit.log '
            sh 'docker-compose -f compose/oasis.platform.yml -f compose/model.worker.yml logs worker         > ./stage/log/worker.log '
            sh 'docker-compose -f compose/oasis.platform.yml -f compose/model.worker.yml logs worker-monitor > ./stage/log/worker-monitor.log '
            sh PIPELINE + " stop_docker ${env.COMPOSE_PROJECT_NAME}"
        }
        //Notify on slack
        if(params.SLACK_MESSAGE && (params.PUBLISH || hasFailed)){
            def slackColor = hasFailed ? '#FF0000' : '#27AE60'
            SLACK_GIT_URL = "https://github.com/OasisLMF/${model_name}/tree/${model_branch}"
            SLACK_MSG = "*${env.JOB_NAME}* - (<${env.BUILD_URL}|${env.RELEASE_TAG}>): " + (hasFailed ? 'FAILED' : 'PASSED')
            SLACK_MSG += "\nBranch: <${SLACK_GIT_URL}|${model_branch}>"
            SLACK_MSG += "\nMode: " + (params.PUBLISH ? 'Publish' : 'Build Test')
            SLACK_CHAN = (params.PUBLISH ? "#builds-release":"#builds-dev")
            slackSend(channel: SLACK_CHAN, message: SLACK_MSG, color: slackColor)
        }
        //Store logs
        dir(build_workspace) {
            archiveArtifacts artifacts: 'stage/log/**/*.*', excludes: '*stage/log/**/*.gitkeep'
            archiveArtifacts artifacts: "stage/output/**/*.*"
        }
    }
}
