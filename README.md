# OasisLMF Complex Model Integration of HailAUS 7

## Run the complex model using the API & UI
1) install git, docker and docker-compose

For example on an Ubuntu/Debian based Linux system use:
```
sudo apt update && sudo apt install git docker docker-compose
```

2) Clone this repository
```
git clone https://github.com/risk-frontiers/OasisComplexModel.git
cd OasisComplexModel
```
3) Extract the model data archive and copy your license.txt into the model_data root folder
4) Copy model_data inside OasisComplexModel. The folder structure should be as follows
```
user@ubuntu:/var/oasis/OasisComplexModel$ tree
.
├── complex_model
│   └── Risk.Platform.Core
├── rf_install.sh
├── model_data
│   ├── license.txt
```
5) Run the deployment script
```
./rf_install.sh
```

6) Access via localhost, using the default `user: admin` `pass: password`
* [OasisUI Interface](http://localhost:8080/app/BFE_RShiny) - *localhost:8080/app/BFE_RShiny* 
* [API Swagger UI](http://localhost:8000/) - *localhost:8000*
* [API Admin Panel](http://localhost:8000/admin) - *localhost:8000/admin*


### Notes: 
* More detailed documentation can be found [here](https://github.com/risk-frontiers/OasisComplexModel/manual.pdf).
* A valid Risk Frontiers license is required to run the integrated model. Please contact 
[Risk Frontiers](mailto:info@riskfrontiers.com) for more information. 
