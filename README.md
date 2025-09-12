# web-services
Siradel simulation web services
Siradel Web Services API offers an easy integration of simulation capabilities, including access to Volcano propagation model and high accuracy 3D maps. You can integrate it in your custom application, or scripting environment.

# API documentation
API documentation is published in a Postman environnement
https://docs.bloonetws.siradel.com

# Sample codes
This repositery exposes an API integration sample code in python.
To ease the usage, this integration summarized inputs into two files : input.json and a network.csv file
1. Request API access to contact@siradel.com
2. Configure input.json file (see sample file) with provided credentials and your custom information
3. Configure network.csv file (see sample file)
4. run client_simulation.py with input.json as argument

python3 client_simulation.py -i input.json

