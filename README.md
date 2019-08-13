# OasisLMF Complex Model Integration of HailAUS 7

## Run the complex model using the API & UI
The following deployment instruction assumes that a linux system has been deployed with a Debian based distribution (preferably Ubuntu 18.04).
> Azure: you will need to create inbound rules for port 22 (SSH) and 8080 (HTTP). The former will be used to connect to the instance via SSH for deployment, file transfer and configuration. The later is used by the Oasis UI to serve the flamingo web interface. The rules can be added in the Networking setting page on the Azure web portal. This page will also show the public IP of your instance.

> Azure: you will need to use [putty](https://www.chiark.greenend.org.uk/~sgtatham/putty/latest.html) (or a similar connection tool) to connect to the Azure instance via ssh and run the following commands.

1) Connect to the deployment machine then install p7zip, git, docker and docker-compose

For example on an Ubuntu/Debian based Linux system use:
```
sudo apt update && sudo apt install p7zip-full git docker docker-compose -y
```
2) Add `$USER` to the `docker` group and switch user to obtain a new shell
```
sudo usermod -aG docker $USER
sudo su - $USER
```
> Azure: you may need to perform the following in `/mnt` as we require at least 35GB of storage for the hazard and a lot more for temporary storage (see the *oasis_integration.pdf* for more information about the hardware requirement and an example Azure specification). You can also work in a more persistent storage. In the following step, double check that `/mnt` has enough free space (e.g. `df -h /mnt`)

> Azure: by default, the drive containing the Operating System is 30GB. You will need to expand this drive for larger analysis. See the documentation for more information.
3) Create working directory and clone the latest Oasis integration release
```
sudo mkdir /mnt/oasis
sudo chown $USER: /mnt/oasis
cd /mnt/oasis
git clone https://github.com/risk-frontiers/OasisIntegration.git
cd OasisIntegration
```
5) Transfer model_data.7z into the *OasisIntegration* folder. You can use [WinSCP](https://winscp.net/eng/download.php) or [pscp](https://www.chiark.greenend.org.uk/~sgtatham/putty/latest.html) to transfer files from windows to linux. Then extract and remove the compressed archive:
```
7z x model_data_x.y.7z
rm model_data_x.y.7z
```
6) Transfer the *license.txt* into *OasisIntegration/model_data/x.y* folder. The folder structure should be as follows:
```
OasisIntegration/
├── api_evaluation_notebook 
├── complex_model <---------------------- this contains Risk Frontiers' executables
├── conf.ini
├── docker-compose.yml
├── Dockerfile.custom_model_worker
├── install.sh   <---------------------- installation script
├── jenkins
├── model_data   <---------------------- model_data contains revisions of Risk Frontiers' data
│   └── x.y  <---------------------- each version folder contains license.txt
├── model_resource.json
├── README.md
├── requirements.txt
├── reset.sh    <------------------------ removes all containers and, optionaly, stored analysis data
├── setup.py
├── tasks.py
├── tests
└── tools

```
7) Run the installation script and follow the instructions. 
```
chmod +x install.sh
./install.sh
```
>You will be asked to confirm the value for `KTOOLS_BATCH_COUNT`, model data path and license file.
8) Access via the accessible IP (Public IP for Azure) using the default `user: admin` `pass: password` 
* [OasisUI Interface](http://localhost:8080/app/BFE_RShiny) - *localhost:8080/app/BFE_RShiny* 
* [API Swagger UI](http://localhost:8000/) - *localhost:8000* 
* [API Admin Panel](http://localhost:8000/admin) - *localhost:8000/admin*
> Azure: you will also need to add an inbound firewall rule for port 8000 if you need direct access to the Oasis API

10) To update/upgrade the framework, do
```
git pull
chmod +x reset.sh
./reset.sh  # type y to start reset, then type y when asked about prunning, then type no when asked to delete data
./install.sh
``` 
### Notes: 
* A valid Risk Frontiers license is required to run the integrated model. Please contact 
[Risk Frontiers](mailto:info@riskfrontiers.com) for more information. 
