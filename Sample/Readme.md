# How works the python client ?
## Run Python script on Linux environment
    python3 client.py –i input.json -p
## Run Python script on Windows environment
    py client.py –i input.json -p
	
# Details on arguments

## input.json content

## network.csv content

# How to run a simulation using latlong transmitter coordinates
1. Build your csv file, based on network_4326.csv sample
2. In input.json, set the mapdata UTM zone EPSG code. World is splitted into UTM zones. For US, it goes from UTM zone 10N on West coast (EPSG : 32610) to UTM zone 19N on East coast (EPSG : 32619).	
3. Run client_simulation.py

# How to run a simulation using metric transmitter coordinates
1. Build your csv filr, based on network_metric.csv sample
2. In input.json, set the EPSG code you are using. It must correspond to a UTM zone (32610, 32611, ...)
3. Run client_simulation.py

# How to exploit results
Results are written in geotiff format (.tif), and can be post processed in python using dedicated libraries, or in any GIS tool.
Note of TIF specificities :
> -10 000 value is used to define non requested area. To visualiser the TIF properly, you need to adjust color palette (in some tools, it can be automately set based on min value)

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
