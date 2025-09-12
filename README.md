# web-services
Siradel simulation web services
Siradel Web Services API offers an easy integration of simulation capabilities, including access to Volcano propagation model and high accuracy 3D maps. You can integrate it in your custom application, or scripting environment.

# Siradel Web Services web client
A web client integrates our API, to enable easy coverage simulation on a network.
You can watch the worklow overview on the video :
https://www.youtube.com/watch?v=c9_HQC2iPx4

# API documentation
API documentation is published in a Postman environment
https://docs.bloonetws.siradel.com

# Sample codes
This repository exposes an API integration sample code in python.
To ease the usage, this integration summarized inputs into two files : input.json and a network.csv file
1. Request API access to contact@siradel.com
2. Configure input.json file (see sample file) with provided credentials and your custom information
3. Configure network.csv file (see sample file)
4. run client_simulation.py with input.json as argument

python3 client_simulation.py -i input.json

# Want to test our API
Simply request for a trial access to contact@siradel.com, you will receive from our team trial credentials.
Il will enable access to the API :
- for your integration tests
- through ou web client
