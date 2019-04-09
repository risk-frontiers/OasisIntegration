# OasisLMF Complex Model Integration of HailAUS 7

## Run the complex model using the API & UI
1) install tree, git, docker and docker-compose

For example on an Ubuntu/Debian based Linux system use:
```
user@ubuntu:/home/user$ sudo apt update && sudo apt install tree git docker docker-compose
```
2) Add user to the `docker` group and switch user to obtain a shell where `user` is actively a member of that group
```
user@ubuntu:/home/user$ sudo usermod -aG docker user
user@ubuntu:/home/user$ su - $USER
```
3) Clone this repository
```
user@ubuntu:/home/user$ git clone https://github.com/risk-frontiers/OasisComplexModel.git
```
4) Extract the model data archive and copy your license.txt into the model_data root folder. You can use 
[WinSCP](https://winscp.net/eng/download.php) to copy files from windows to linux.
5) Copy model_data inside OasisComplexModel. The folder structure should be as follows
```
user@ubuntu:/home/user$ tree -L 1 OasisComplexModel/
OasisComplexModel/
├── api_evaluation_notebook
├── complex_model <---------------------- this contains Risk Frontiers' executables
├── conf.ini
├── db-data
├── docker-compose.yml
├── Dockerfile.custom_model_worker
├── docker-shared-fs
├── install.sh
├── model_data    <---------------------- model_data contains license.txt and Risk Frontiers data
├── model_resource.json
├── OasisUI
├── README.md
├── requirements.txt
├── rf_install.sh <---------------------- Risk Frontiers complex model installation script
├── setup.py
└── tests
```
6) Run the deployment script
```
cd OasisComplexModel
./rf_install.sh
```

7) Access via localhost, using the default `user: admin` `pass: password`
* [OasisUI Interface](http://localhost:8080/app/BFE_RShiny) - *localhost:8080/app/BFE_RShiny* 
* [API Swagger UI](http://localhost:8000/) - *localhost:8000*
* [API Admin Panel](http://localhost:8000/admin) - *localhost:8000/admin*


### Notes: 
* A more detailed documentation can be found in [oasis_integration.pdf](https://github.com/risk-frontiers/OasisComplexModel/blob/master/oasis_integration.pdf).
* A valid Risk Frontiers license is required to run the integrated model. Please contact 
[Risk Frontiers](mailto:info@riskfrontiers.com) for more information. 
