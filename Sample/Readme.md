# How to run the python client ?
You can run python client through any python 3 environement.

### Run Python script on Linux environment
    python3 client.py –i input.json -p
### Run Python script on Windows environment
    py client.py –i input.json -p
	
# Details on arguments

### input.json content
You can set in input.json all simulation parameters. Main parameters to adjust and check are :
- credential : insert your LOGIN and PASSWORD
- antenna
- network file (.csv)
- mapdata EPSG code
  
### network.csv content
network file (.csv) must reference antenna and propagation model defined in input.json file

	transmitter id;transmitter name;transmitter easting;transmitter northing;transmitter height;azimuth;downtilt;frequency;antenna;propagation model;calculation resolution;calculation radius;emitting power;comments
	1;tx1;550097;5272898;10;0;1;900;Dir_H68_V7_tilt4_PolV_19dBi;propagLR;10;2000;0;

 ### Per transmitter prediction
 If you add -p argument to the command line (optional), it will extract to your local result folder per transmitter coverage prediction, additionnally to best signal output

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
First, update configuration files input.json + newtwork file (.csv), based on what you have set up on the web client.
You can use input_4326.json and network_4326.cv files.

### Modify your credential info in input.json
Insert your user LOGIN and PASSWORD in the credential section of input.json

	"serverUrl": "https://api.bloonetws.siradel.com/",
	"downloadUrl": "https://dl.bloonetws.siradel.com/",
	"authentication": {
 	"required": true,
	"publicPrediction": false,
	"url": "https://keycloak.bloonetws.siradel.com/realms/volcanoweb/protocol/openid-connect/token",
	"clientId": "volcano-web-cli",
	"clientSecret": "9QZGszL6HzkGmjrMaUNyakWfqIdyZyqa",
	"username": "LOGIN",
	"password": "PASSWORD"

### Transmitters
You can directly reuse transmitter from the transmitter table into the network file (.csv).

### Antenna
-> input.json : add antenna you want to use

	"antennas": [
	{
		"name": " Tarana_BN_3GHz_Compact_R0 ",
		"antennaFile": "./ Tarana_BN_3GHz_Compact_R0.xml"

  -> network file (.csv) : use this antenna name for antenna field
  
### Receiver height  
-> input.json (receptionHeights)
### Receiver antenna gain (dBi) and Simulation margin (dB)
-> in network file (.csv), as described below.
  
	e.g if you consider following parameters in the web client configuration :
		Emitting power (dB) : 25
		Receiver antenna gain (dBi) : 10
		Simulation margin (dB) : 5
		Set your transmitter emitting power (in network.csv file) at : 25 + 10 -5 = 30

### Frequency
-> network file (.csv) (frequency)
### Transmitters antenna
-> add antenna in input.json and use this antenna in netwok file (.csv)
### Computation radius and Resolution
-> network file (.csv) (computation radius and computation resolution)
### Propagation model
-> network file (.csv) (propagation model)
- For Fixed wireless access -> input.json (set models/name to Fixed Wireless Access) and network file (.csv) (set propagation model to Fixed Wireless Access)
- For mobility -> input.json (set models/name to Mobility) and network file (.csv) (set propagation model to Mobility)

Then, you can run the python client and retrived your results locally.

	python3 client.py -i input_4326.json
