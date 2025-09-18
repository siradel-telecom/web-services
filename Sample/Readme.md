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

# You have run simulation through Siradel Web Services client and want to go further from the API ?
If you have run first simulations from the client, and want to retrieved your results and go further, you have to move on the steps below.
In you input.json, specify the Tarana antenna you have used through the webclient.
	"antennas": [
	{
		"name": " Tarana_BN_3GHz_Compact_R0 ",
		"antennaFile": "./ Tarana_BN_3GHz_Compact_R0.xml"
For the two simulation configuration parameters "Receiver antenna gain (dBi)" and "Simulation margin (dB)", you need to integrate these values onto transmitters transmit power in the csv file.
e.g if you consider following parameters in the web client configuration :
- Emitting power (dB) : 25
- Receiver antenna gain (dBi) : 10
- Simulation margin (dB) : 5
Set your transmitter emitting power (in network.csv file) at : 25 + 10 -5 = 30
