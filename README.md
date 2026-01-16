# web-services
Siradel Web Services API offers an easy integration of simulation capabilities, including access to Volcano propagation model and high accuracy 3D maps. You can integrate it in your custom application, or scripting environment.

# Siradel Web Services web client
A web client integrates our API, to enable easy coverage simulation on a network.
You can watch the workflow overview on the video :
https://www.youtube.com/watch?v=c9_HQC2iPx4

# API documentation
API documentation is published in a Postman environment
https://docs.bloonetws.siradel.com

# Sample codes

## Jupyter Notebook sample
A Jupyter notebook is available for you to perform point-to-point calculations and generate a matrix grouping the received power results between transmitters and receivers.  
To launch this notebook, simply enter your credentials in the AUTHENTICATION constant and launch the notebook cells.  
A user interface allowing you to enter the calculation elements is displayed in the last cell of the Notebook :
1. Select a list of transmitters in CSV format (see transmitters.csv for field details).
2. Select a list of receivers in CSV format (see receivers.csv for field details).
3. Select a propagation model to use from the public models provided.
4. Select an antenna to use from the public antennas provided.
5. Click on the “Start the calculation” button.

## Python sample
You can find an API integration sample code in python.
To ease the usage, this integration summarized inputs into two files : input.json and a network.csv file
1. Request API access to contact@siradel.com
2. Configure input.json file (see sample file) with provided credentials and your custom information
3. Configure network.csv file (see sample file)
4. run client_simulation.py with input.json as argument

python3 client_simulation.py -i input.json

# Want to test our API
Simply request for a trial access to contact@siradel.com, you will receive from our team trial credentials.
It will enable access to the API :
- for your integration tests
- through ou web client
