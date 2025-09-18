# How works the python client ?
Python client is a sample code that enables running a simulation, by defining inputs into a csv file and input.json file.
It relies on Siradel Web Services API.

## Run Python script on Linux environment
    python3 client.py –i input.json -p
## Run Python script on Windows environment
    py client.py –i input.json -p
	
# Details on arguments
## input.json content
You can set antenna in input.json file, modify mapdata EPSG code
## network.csv content
- network csv file must reference antenna and propagation model defined in input.json file
	transmitter id;transmitter name;transmitter easting;transmitter northing;transmitter height;azimuth;downtilt;frequency;antenna;propagation model;calculation resolution;calculation radius;emitting power;comments
	1;tx1;550097;5272898;10;0;1;900;Dir_H68_V7_tilt4_PolV_19dBi;propagLR;10;2000;0;
 
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

