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

## ESRI Notebook sample
ESRI Notebook file (EsriBloonetNotebookSample.ipynb) enables to easily run a coverage from your ArcGIS Online environment.  
This script communicates with the Siradel Web Services API to launch the coverage calculations and import the results into your map and environment.  
1. Import the Notebook into an ArcGIS Online environment
2. Create a web map in ArcGIS containing a feature layer representing transmitters built from the seattle-network.csv CSV file, a shapefile, or manually, with required fields (see csv file)
3. Launch the Notebook, you will have to indicate the map to use, the propagation model and antenna.
4. At the end of the Notebook execution, check that the Web Map contains two new raster layers: best signal and best server

## Jupyter Notebook sample
Jupyter notebook allows you to perform point-to-point calculations and generate a matrix with all simulated Tx-Rx links received powers.  
To run this notebook, simply enter your credentials in the AUTHENTICATION and run the notebook.
Last cell import a widget to upload transmitters.csv and receivers.csv date :
1. Select a list of transmitters in CSV format (see transmitters.csv for field details).
2. Select a list of receivers in CSV format (see receivers.csv for field details).
3. Select a propagation model to use from the public models provided.
4. Select an antenna to use from the public antennas provided.
5. Click on the “Start the calculation” button.

## Python sample
You can find an API integration sample code in python.
To ease the usage, this integration summarized inputs into two files : input.json and a network.csv file
1. Configure input.json file (see sample file) with provided credentials and your custom information
2. Configure network.csv file (see sample file)
3. run client_simulation.py with input.json as argument

python3 client_simulation.py -i input.json

# Want to test our API
Simply auto register on https://www.bloonetws.siradel.com/, or reach out to contact@siradel.com if you have advanced request.
It will enable access to the API :
- for your integration tests
- through ou web client
