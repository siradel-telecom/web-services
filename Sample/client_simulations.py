"""
Author: SIRADEL
Copyright: Copyright (C) 2025 SIRADEL
License: Private Domain
Date: 08-09-2025
Version: 2.9.0.0

Description: Module used to launch simulation calculations
Options: -h provide all options available, -i Json input file
Running command: python3 client_simulations.py -i tests/[...].json
"""

import argparse
import csv
import errno
import json
import logging
import math
import os
import re
import zipfile
import requests
import sys
import time
import uuid
from enum import Enum
from pathlib import Path
from typing import Union, List, Optional, cast, Any

SCRIPT_VERSION = "2.9.0.0"
LAST_DATE_MODIF = "08-09-2025"


class NetworkFields(str, Enum):
    """List of csv network fields"""
    TRANSMITTER_ID = ("transmitter id", True)
    TRANSMITTER_NAME = ("transmitter name", True)
    TRANSMITTER_EASTING = ("transmitter easting", False)
    TRANSMITTER_NORTHING = ("transmitter northing", False)
    TRANSMITTER_LONGITUDE = ("transmitter longitude", False)
    TRANSMITTER_LATITUDE = ("transmitter latitude", False)
    TRANSMITTER_HEIGHT = ("transmitter height", True)
    PROPAGATION_MODEL = ("propagation model", True)
    FREQUENCY = ("frequency", True)
    AZIMUTH = ("azimuth", False)
    DOWNTILT = ("downtilt", False)
    ADDITIONAL_ELECTRICAL_DOWNTILT = ("additional electrical downtilt", False)
    ANTENNA = ("antenna", False)
    EMITTING_POWER = ("emitting power", False)
    COMMENTS = ("comments", False)
    TERRAIN_ALTITUDE = ("terrain altitude", False)
    CALCULATION_RADIUS = ("calculation radius", False)
    CALCULATION_RESOLUTION = ("calculation resolution", False)
    EPRE_OFFSET_SS_VS_RS = ("epre offset ss vs rs", False)
    EPRE_OFFSET_PBCH_VS_RS = ("epre offset pbch vs rs", False)
    EPRE_OFFSET_PDCCH_VS_RS = ("epre offset pdcch vs rs", False)
    EPRE_OFFSET_PDSCH_VS_RS = ("epre offset pdsch vs rs", False)
    NB_ANTENNA_PORTS = ("number antenna ports", False)
    MULTI_ANTENNA_INTERFERENCE_FACTOR = ("multi antenna interference factor", False)
    DONOR_LOSS = ("donor loss", False)
    TECHNO = ("techno", False)
    TRAFFICLOAD = ("trafficload", False)
    ANTENNA_CSI = ("antenna CSI", False)
    ANTENNA_SSB = ("antenna SSB", False)
    RECEIVER_NAME = ("receiver name", False)
    RECEIVER_EASTING = ("receiver easting", False)
    RECEIVER_NORTHING = ("receiver northing", False)
    RECEIVER_LONGITUDE = ("receiver longitude", False)
    RECEIVER_LATITUDE = ("receiver latitude", False)
    RECEIVER_HEIGHT = ("receiver height", False)
    RECEIVER_AZIMUTH = ("receiver azimuth", False)
    RECEIVER_DOWNTILT = ("receiver downtilt", False)
    RECEIVER_ANTENNA = ("receiver antenna", False)

    def __new__(cls, value, mandatory):
        """
        @summary: network field enum constructor
        @parameter: {str} network field string value
        @parameter: {bool} network field mandatory flag
        """
        obj = str.__new__(cls, value)
        obj._value_ = value
        obj._mandatory_ = mandatory
        return obj

    @property
    def mandatory(self):
        """
        @summary: Get network field mandatory property
        @return: {bool} is network field mandatory
        """
        return self._mandatory_

    def __str__(self) -> str:
        """
        @summary: Format enum representation for print and log
        @return: {str} enum string representation
        """
        return f"'{self.value}'"

    @classmethod
    def list(cls) -> list:
        """
        @summary: Get all network fields with regexes for parametrized fields
        @return: {list} a list of network fields with regexes for parametrized fields
        """
        fields = []
        for field in cls:
            placeholders = re.findall(r'{(.*?)}', field)
            if 'number' in placeholders:
                fields.append(field.format(number="[1-9]\\d*"))
            else:
                fields.append(field)
        return fields

    @classmethod
    def list_mandatory(cls) -> set:
        """
        @summary: Get all mandatory network fields
        @return: {list} a list of mandatory network fields
        """
        return {field for field in cls if field.mandatory}


NB_RECEIVER_LIMIT = 10000
SINR5G = "5G"
SINR4G = "4G"
CUSTOM = "Custom"

NAME = "name"
COMPUTATION_ZONE = "computationZone"
FILTER_SHAPE = "filterShape"

ERROR_POST_PROCESSING = "Error post processing"
ERROR_PREDICTION_GROUP = "Error prediction group"
ERROR_SIMULATION = "Error simulation"
ERROR_LOG = "Error : %s"
ERROR_PREDICTION_LOG = "Error prediction %s"
ERROR_SIMULATION_LOG = "Error simulation %s"

APPLICATION_JSON = "application/json"
APPLICATION_OCTET_STEAM = "application/octet-stream"
APPLICATION_ZIP = "application/zip"
TEXT_XML = "text/xml"
JSON_PARAM = "json"
DATA_PARAM = "data"
SHAPEFILE_ARCHIVE_PARAM = "shapefileArchive"
SHAPE_FILE_EXT_MANDATORY = [".shp", ".shx", ".dbf"]
SHAPE_FILE_EXT_OPTIONAL = [".prj", ".sbn", ".sbx", ".fbn", ".fbx", ".ain", ".aih", ".ixs",
                           ".mxs", ".atx", ".cpg", ".qix", ".qmd"]
SHAPE_FILE_EXT_OPTIONAL_XML = ".shp.xml"

SESSION_UUID = uuid.uuid4()
SIMULATION_UUID = uuid.uuid4()
MAPDATA_MAP = {}
ANTENNA_MAP = {}
MODEL_MAP = {}
ACCESS_TOKEN = None
REFRESH_TOKEN = None
AUTHENTICATION = None

LOGGER = logging.getLogger(__name__)
FORMATTER = logging.Formatter(
    "%(asctime)s | %(funcName)-45s | %(levelname)-7s | %(message)s",
    datefmt="%d-%m-%Y | %H:%M:%S"
)
HANDLER = logging.StreamHandler(sys.stdout)
HANDLER.setFormatter(FORMATTER)
LOGGER.setLevel(logging.INFO)
LOGGER.addHandler(HANDLER)


def get_script_information(logger: logging.Logger) -> None:
    """
    @summary: Log the script information
    @param logger: {logging.Logger} used to trace output log
    """
    logger.info("* Software name: client.py")
    logger.info(f"* Version: {SCRIPT_VERSION}")
    logger.info(f"* Date: {LAST_DATE_MODIF}")
    logger.info("* Editor: SIRADEL-ENGIE")



def get_computation_type(data_dict: dict) -> str:
    """
    @summary: Get type of computation
    @param data_dict: {dict} dictionary of parameters
    @return: {str} type of computation
    """
    if "network" in data_dict.keys() and "computationType" in data_dict["network"]:
        computation_type = data_dict["network"]["computationType"]
    else:
        computation_type = ""
    return computation_type


def get_prediction_type(prediction_settings: dict) -> str:
    """
    @summary: Get type of prediction
    @param prediction_settings: {dict} dictionary of prediction settings
    @return: {str} type of prediction
    """
    prediction_type = "AREA"
    if "type" in prediction_settings.keys():
        prediction_type = prediction_settings["type"]
    return prediction_type


def get_from_dict(data_dict: dict, key: str, default: str | None = None) -> Any:
    """
    @summary: Get value from dictionary
    @param data_dict: {dict} dictionary
    @param key: {str} key in dictionary
    @param default: {str} default value (optional)
    @return: {Any} value from dictionary
    """
    value = data_dict.get(key, default)
    if value is None and default is None:
        LOGGER.error('Failed to get value of %s, value not found', key)
        sys.exit(errno.EINVAL)
    return value


def get_float_from_dict(data_dict: dict, key: str, default: float | None = None) -> float:
    """
    @summary: Get float value from dictionary
    @param data_dict: {dict} dictionary
    @param key: {str} key in dictionary
    @param default: {str} default value (optional)
    @return: {float} float value from dictionary
    """
    try:
        default_value = None
        if default is not None:
            default_value = str(default)
        return float(get_from_dict(data_dict, key, default_value))
    except ValueError as e:
        LOGGER.error('Failed to get value of %s, %s', key, e)
        sys.exit(errno.EINVAL)


def sorting_json(item: dict) -> Union[list, dict]:
    """
    @summary: recursively sort json item
    @param item: {dict} json item
    @return: {any} json item sorted
    """
    json_sorted: Union[list, dict] = item
    if isinstance(item, dict):
        json_sorted = sorted((key, sorting_json(values)) for key, values in item.items())
    elif isinstance(item, list):
        json_sorted = sorted(sorting_json(x) for x in item)

    return json_sorted


def update_progress(progress: int) -> None:
    """
    @summary: Update the display of the treatment progress
    @param progress: {int} download progress
    """
    sys.stdout.write(f"[{'#' * int(progress / 10)}] {progress}% \r")
    sys.stdout.flush()


def create_directory(path: str) -> None:
    """
    @summary: Create the directory if it doesn't exist
    @param path: {str} path of the directory to create
    @return: {str} the file url correctly prefixed
    """
    if not os.path.exists(path):
        os.makedirs(path)


def parse_args() -> argparse.Namespace:
    """
    @summary: Parse input parameters
    @return: {dict} the arguments parsed
    """
    parser = argparse.ArgumentParser(description="Script helper")

    parser.add_argument(
        "-i", "--file", "--ifile",
        help="JSON input file",
        dest="inputFile",
        type=argparse.FileType("r"),
        required=True
    )

    parser.add_argument(
        "-p", "--download-prediction",
        help="Download prediction results",
        dest="downloadPrediction",
        action="store_true",
        default=False,
        required=False
    )

    args = parser.parse_args()

    if not args.inputFile:
        parser.print_usage()
        sys.exit(2)
    return args


def get_resource_uuid_from_cache(resource_type: str, resource_cache: dict, resource_name: str,
                                 logger: logging.Logger) -> uuid.UUID:
    """
    @summary: Get the resource uuid from cache or exit the process with error message if not found
    @param resource_type: {str} resource type (eg. Antenna, Mapdata...)
    @param resource_cache: {dict} cache as dict for name to uuid mapping
    @param resource_name: {str} resource name to get in cache
    @param logger: {logging.Logger} used to trace output log
    @return: {uuid.UUID} resource uuid retrieved from cache
    """
    resource_uuid = resource_cache.get(resource_name)
    if resource_uuid is None:
        logger.error("Error %s %s : not found", resource_type, resource_name)
        sys.exit(errno.EINVAL)
    return resource_uuid


def create_antennas(antenna_list: list, authentication_data: Optional[dict], server: str,
                    logger: logging.Logger) -> dict:
    """
    @summary: Create antennas from list
    @param antenna_list: {list} list of antenna
    @param authentication_data: {dict} authentication data
    @param server: {str} server url
    @param logger: {logging.Logger} used to trace output log
    @return: {dict} dict of antennas for name to uuid mapping
    """
    logger.info("Creation antenna")

    # Validate antennas
    validate_antennas(antenna_list, logger)

    antenna_dict = {}
    for antenna in antenna_list:
        antenna["uuid"] = str(uuid.uuid4())
        antenna_filename = os.path.basename(antenna["antennaFile"])
        with open(antenna["antennaFile"], "rb") as antenna_file:
            multipart_form_data = [
                (JSON_PARAM, (None, json.dumps(antenna), APPLICATION_JSON)),
                (DATA_PARAM, (antenna_filename, antenna_file, TEXT_XML))
            ]
            res = call_request("POST", get_resource_uri(server, "antennas", authentication_data),
                               authentication_data, logger, files=multipart_form_data)
            result = res.json()
            if res.status_code != 201:
                if res.status_code == 202:
                    logger.warning("Antenna name %s : already exist", antenna_filename)
                else:
                    logger.error("Error antenna %s : %s",
                                 antenna[NAME], get_error_message(result))
                    sys.exit(errno.EINVAL)
            antenna_dict[antenna[NAME]] = result["uuid"]
    return antenna_dict


def validate_antennas(antenna_list: list, logger: logging.Logger) -> None:
    """
    @summary: Validate antennas from list
    @param antenna_list: {list} list of antenna
    @param logger: {logging.Logger} used to trace output log
    """
    antenna_validated: Union[list, dict] = {}
    for antenna in antenna_list:
        if antenna[NAME] in antenna_validated \
                and antenna_validated[antenna[NAME]] != sorting_json(antenna):
            logger.error("Error antenna %s : %s", antenna[NAME],
                         "two antennas have the same name but different contents")
            sys.exit(errno.EINVAL)
        else:
            antenna_validated[antenna[NAME]] = sorting_json(antenna)



def create_gobs(gob_list: list, antenna_dict: dict, authentication_data: Optional[dict],
                server: str, logger: logging.Logger) -> dict:
    """
    @summary: Create gobs from list
    @param gob_list: {list} list of gob
    @param antenna_dict: {dict} dict of antenna for name to uuid mapping
    @param authentication_data: {dict} authentication data
    @param server: {str} server url
    @param logger: {logging.Logger} used to trace output log
    @return: {dict} dict of gob for name to uuid mapping
    """
    logger.info("Creation gob")

    # Validate antennas
    validate_antennas(gob_list, logger)

    created_gob_dict = {}
    for gob in gob_list:
        gob["uuid"] = str(uuid.uuid4())
        for beam in gob["beams"]:
            beam["uuid"] = get_resource_uuid_from_cache("Antenna", antenna_dict, beam[NAME], logger)

        res = call_request("POST", get_resource_uri(server, "antennas/gob", authentication_data),
                           authentication_data, logger, json_content=gob)

        result = res.json()
        if res.status_code != 201:
            if res.status_code == 202:
                logger.warning("Gob name %s : already exist", gob[NAME])
            else:
                logger.error("Error gob %s : %s", gob[NAME], get_error_message(result))
                sys.exit(errno.EINVAL)
        created_gob_dict[gob[NAME]] = result["uuid"]
    return created_gob_dict


def delete_scenarii_dir(authentication_data: Optional[dict], server: str,
                        logger: logging.Logger) -> None:
    """
    @summary: Delete volcanoweb scenarii folders
    @param authentication_data: {dict} authentication data
    @param server: {str} server url
    @param logger: {logging.Logger} used to trace output log
    """
    # predictions
    res = call_request("DELETE", server + "predictions/allPredictionsFolders",
                       authentication_data, logger)
    if res.status_code != 200:
        result = res.json()
        logger.error(ERROR_LOG, get_error_message(result))

    # postprocessings
    res = call_request("DELETE", server + "postprocessings/folders",
                       authentication_data, logger)
    if res.status_code != 200:
        result = res.json()
        logger.error(ERROR_LOG, get_error_message(result))


def fill_base_station(network: dict, computation_type: str, session_uuid: uuid.UUID,
                      antenna_dict: dict, logger: logging.Logger) -> dict:
    """
    @summary: Fill a base station object according to network datas
    @param network: {dict} network datas
    @param computation_type: {str} type of computation
    @param session_uuid: {uuid.UUID} uuid of the current session
    @param antenna_dict: {dict} dict of antenna for name to uuid mapping
    @param logger: {logging.Logger} used to trace output log
    @return: {dict} the base station object
    """
    transmitter_long_lat_coordinate = (NetworkFields.TRANSMITTER_LONGITUDE in network
                                       and NetworkFields.TRANSMITTER_LATITUDE in network)
    base_station = {
        "x": get_float_from_dict(network, NetworkFields.TRANSMITTER_LONGITUDE)
        if transmitter_long_lat_coordinate else get_float_from_dict(network, NetworkFields.TRANSMITTER_EASTING),
        "y": get_float_from_dict(network, NetworkFields.TRANSMITTER_LATITUDE)
        if transmitter_long_lat_coordinate else get_float_from_dict(network, NetworkFields.TRANSMITTER_NORTHING),
        "z": get_float_from_dict(network, NetworkFields.TRANSMITTER_HEIGHT),
        "epsgCode": 4326 if transmitter_long_lat_coordinate else None,
        "zmeaning": "ZMEANING_GROUND",
        "azimuth": get_float_from_dict(network, NetworkFields.AZIMUTH, 0),
        "downtilt": get_float_from_dict(network, NetworkFields.DOWNTILT, 0),
        "carrierFrequency": get_float_from_dict(network, NetworkFields.FREQUENCY),
        "description": get_from_dict(network, NetworkFields.COMMENTS, ""),
        "sessionUuid": str(session_uuid),
        "name": get_from_dict(network, NetworkFields.TRANSMITTER_NAME),
        "networkId": get_from_dict(network, NetworkFields.TRANSMITTER_ID),
        "transmitPower": get_float_from_dict(network, NetworkFields.EMITTING_POWER, 0)
    }

    if NetworkFields.ADDITIONAL_ELECTRICAL_DOWNTILT in network.keys():
        base_station["additionalElectricalDowntilt"] = \
            get_float_from_dict(network, NetworkFields.ADDITIONAL_ELECTRICAL_DOWNTILT, 0)

    # check terrain altitude
    if NetworkFields.TERRAIN_ALTITUDE in network.keys() and network.get(NetworkFields.TERRAIN_ALTITUDE):
        base_station["zmeaning"] = "ZMEANING_ALTITUDE"
        base_station["z"] = (get_float_from_dict(network, NetworkFields.TRANSMITTER_HEIGHT)
                             + get_float_from_dict(network, NetworkFields.TERRAIN_ALTITUDE))

    if NetworkFields.ANTENNA in network.keys() and network.get(NetworkFields.ANTENNA):
        antenna_name = get_from_dict(network, NetworkFields.ANTENNA)
        base_station["antennaUuid"] = get_resource_uuid_from_cache("Antenna", antenna_dict,
                                                                   antenna_name, logger)


    if computation_type in (SINR5G, SINR4G):
        base_station["techno"] = get_from_dict(network, NetworkFields.TECHNO)
        base_station["trafficload"] = get_from_dict(network, NetworkFields.TRAFFICLOAD, "0")
        if computation_type == SINR5G:
            antenna_ssb_name = get_from_dict(network, NetworkFields.ANTENNA_SSB)
            base_station["antennaSsbUuid"] = get_resource_uuid_from_cache("Antenna", antenna_dict,
                                                                          antenna_ssb_name, logger)
            antenna_csi_name = get_from_dict(network, NetworkFields.ANTENNA_CSI)
            base_station["antennaCsiUuid"] = get_resource_uuid_from_cache("Antenna", antenna_dict,
                                                                          antenna_csi_name, logger)
        if computation_type == SINR4G:
            mandatory_advanced_sinr_fields = [NetworkFields.EPRE_OFFSET_SS_VS_RS,
                                              NetworkFields.EPRE_OFFSET_PBCH_VS_RS,
                                              NetworkFields.EPRE_OFFSET_PDCCH_VS_RS,
                                              NetworkFields.EPRE_OFFSET_PDSCH_VS_RS,
                                              NetworkFields.NB_ANTENNA_PORTS]
            found_advanced_sinr_fields = \
                list(x in network.keys() and network.get(x) != '' for x in mandatory_advanced_sinr_fields)
            if all(found_advanced_sinr_fields):
                base_station["epreOffsetSSVSRS"] = \
                    get_from_dict(network, NetworkFields.EPRE_OFFSET_SS_VS_RS)
                base_station["epreOffsetPBCHVSRS"] = \
                    get_from_dict(network, NetworkFields.EPRE_OFFSET_PBCH_VS_RS)
                base_station["epreOffsetPDCCHVSRS"] = \
                    get_from_dict(network, NetworkFields.EPRE_OFFSET_PDCCH_VS_RS)
                base_station["epreOffsetPDSCHVSRS"] = \
                    get_from_dict(network, NetworkFields.EPRE_OFFSET_PDSCH_VS_RS)
                base_station["nbAntennaPorts"] = (
                    get_from_dict(network, NetworkFields.NB_ANTENNA_PORTS))
                # Add optional multi antenna interference factor if available
                if NetworkFields.MULTI_ANTENNA_INTERFERENCE_FACTOR in network:
                    base_station["multiAntennaInterferenceFactor"] = (
                        get_from_dict(network, NetworkFields.MULTI_ANTENNA_INTERFERENCE_FACTOR))
            elif any(found_advanced_sinr_fields):
                logger.error("Error base station: All or none values must be configured among %s",
                             mandatory_advanced_sinr_fields)
                sys.exit(errno.EINVAL)

        # Check for 5G repeaters
        if "techno" in base_station \
                and base_station["techno"] == SINR5G \
                and "repeatBaseStationNetworkId" in base_station \
                and base_station["repeatBaseStationNetworkId"] is not None:
            logger.error("Error base station: Repeaters are not available for 5G computations")
            sys.exit(errno.EINVAL)

    return base_station


def create_mapdatas(mapdata_list: list, authentication_data: Optional[dict],
                    server: str, logger: logging.Logger) -> dict:
    """
    @summary: Create mapdatas from list
    @param mapdata_list: {list} list of mapdata
    @param authentication_data: {dict} authentication data
    @param server: {str} server url
    @param logger: {logging.Logger} used to trace output log
    @return mapdata_dict: {dict} dict of mapdata
    """
    logger.info("Creation mapdata")

    # Validate mapdatas
    validate_mapdatas(mapdata_list, logger)

    # Create mapdatas
    mapdata_dict = {}
    for mapdata in mapdata_list:
        mapdata["uuid"] = str(uuid.uuid4())
        mapdata["sridEpsg"] = mapdata["epsgSrid"]
        mapdata.pop("epsgSrid", None)
        # Check name mapData
        res = call_request("GET", f"{server}mapdata/{mapdata['uuid']}", authentication_data, logger)
        result_get = res.json()
        if res.status_code == 200:
            logger.warning("Mapdata uuid already exists")
        # POST mapdata to server
        result_post = call_request("POST", get_resource_uri(server, "mapdata", authentication_data),
                                   authentication_data, logger, json_content=mapdata).json()
        handle_create_mapdata_result(result_get, result_post, mapdata, logger)
        mapdata_dict[mapdata[NAME]] = result_post["uuid"]
    return mapdata_dict


def validate_mapdatas(mapdata_list: list, logger: logging.Logger) -> None:
    """
    @summary: Validate mapdatas from list
    @param mapdata_list: {list} list of mapdata
    @param logger: {logging.Logger} used to trace output log
    """
    mapdata_validated: Union[list, dict] = {}
    for mapdata in mapdata_list:
        if mapdata[NAME] in mapdata_validated \
                and mapdata_validated[mapdata[NAME]] != sorting_json(mapdata):
            logger.error("Error mapdata %s : %s", mapdata[NAME],
                         "two mapdatas have the same name but different contents")
            sys.exit(errno.EINVAL)
        else:
            mapdata_validated[mapdata[NAME]] = sorting_json(mapdata)


def handle_create_mapdata_result(result_get: dict, result_post: dict, mapdata: dict,
                                 logger: logging.Logger) -> None:
    """
    @summary: Handle the result returned by the mapdata creation api call
    @param result_get: {dict} result of get call api
    @param result_post: {dict} result of post call api
    @param mapdata: {dict} mapdata object
    @param logger: {logging.Logger} used to trace output log
    """
    if "status" in result_post.keys() and result_post["status"] != 201:
        if "layers" in result_get.keys() and mapdata["layers"] != result_get["layers"]:
            logger.error(
                "The process failed due to a difference between the path in the mapdata "
                "of the input.json file and the mapdata saved in the API")
            layer_index = 0
            for layer in result_get["layers"]:
                if len(mapdata["layers"]) > layer_index and layer != mapdata["layers"][layer_index]:
                    logger.error("Mapdata layer saved in the API: %s", str(layer))
                    logger.error("Mapdata layer of the input.json: %s",
                                 str(mapdata["layers"][layer_index]))
                layer_index += 1
            sys.exit(errno.EINVAL)
        elif result_post["status"] != 406:
            logger.error("Error mapdata %s : %s", mapdata[NAME], get_error_message(result_post))
            sys.exit(errno.EINVAL)


def create_model(model_list: list, mapdata_dict: dict, session_uuid: uuid.UUID,
                 authentication_data: Optional[dict], server: str, logger: logging.Logger) -> dict:
    """
    @summary: Create a model
    @param model_list: {list} list of model
    @param mapdata_dict: {dict} dict of mapdata
    @param session_uuid: {uuid.UUID} uuid of the current session
    @param authentication_data: {dict} authentication data
    @param server: {str} server url
    @param logger: {logging.Logger} used to trace output log
    @return model_dict: {dict} dict of propagation models
    """
    logger.info("Creation model")
    model_dict = {}
    for model in model_list:
        model["uuid"] = str(uuid.uuid4())
        if "mapdataName" in model:
            model["mapdataUuid"] = get_resource_uuid_from_cache("Mapdata", mapdata_dict,
                                                                model["mapdataName"], logger)
            del model["mapdataName"]
        model["sessionUuid"] = str(session_uuid)

        result = None
        if "vxfFilePath" in model:
            model_filename = os.path.basename(model["vxfFilePath"])
            with open(model["vxfFilePath"], "rb") as vxf_file:
                multipart_form_data = [
                    (JSON_PARAM, (None, json.dumps(model), APPLICATION_JSON)),
                    (DATA_PARAM, (model_filename, vxf_file))
                ]
                result = call_request(
                    "POST", get_resource_uri(server, "propagationmodels", authentication_data),
                    authentication_data, logger, files=multipart_form_data).json()
        if "type" in model:
            result = call_request("POST", get_resource_uri(server, "propagationmodels", authentication_data),
                                  authentication_data, logger, json_content=model).json()
        if result is None:
            logger.error("Error model %s : there is no 'vxfFilePath' or 'type' key in this model", model[NAME])
            sys.exit(errno.EINVAL)
        if "status" in result.keys() and result["status"] != 406:
            logger.error("Error model %s : %s", model[NAME], get_error_message(result))
            sys.exit(errno.EINVAL)
        model["uuid"] = result["uuid"]
        model_dict[model[NAME]] = model["uuid"]
    return model_dict


def get_model(model_name: str, session_uuid: uuid.UUID, models: dict,
              authentication_data: Optional[dict], server: str,
              logger: logging.Logger) -> dict:  # type: ignore[return]
    """
    @summary: Get model by session uuid and model name
    @param model_name: {str} name of the model to retrieve
    @param session_uuid: {uuid.UUID} uuid of the current session
    @param models: {dict} dictionary of models
    @param authentication_data: {dict} authentication data
    @param server: {str} server url
    @param logger: {logging.Logger} used to trace output log
    @return: {dict} the model corresponding to the model name
    """
    model = models.get(model_name)
    if model is not None:
        return model

    param = {
        "sessionid": str(session_uuid)
    }

    models_list = call_request("GET", f"{server}propagationmodels",
                               authentication_data, logger, params=param).json()
    for model in models_list:
        if model[NAME] == model_name:
            models[NAME] = model
            return model
    logger.error("Error model %s : does not exist in the session", model_name)
    sys.exit(errno.EINVAL)


def create_network_list(network_file_path: str, logger: logging.Logger) -> list:
    """
    @summary: Create and validate list of network data from csv network file
    @param network_file_path: {str} csv network file path to read
    @param logger: {logging.Logger} used to trace output log
    @return: {list} a list of network data
    """
    logger.debug("Import network file")
    network_list = []
    with open(network_file_path, encoding="utf-8") as csv_file:
        csv_reader = csv.DictReader(csv_file, delimiter=";")

        # Validate csv headers
        # 1. Check for unknown or misspelled headers
        header_regexes = [re.compile(csv_header) for csv_header in NetworkFields.list()]
        headers = csv_reader.fieldnames
        if headers is not None:
            valid_headers = set()
            unknown_headers = set()
            for header in headers:
                if header.strip() and not any(hr.fullmatch(header) for hr in header_regexes):
                    # csv header does not match any known header
                    unknown_headers.add(header)
                else:
                    valid_headers.add(header)
            if unknown_headers:
                logger.error("Unknown field(s) in network file: %s", ', '.join(unknown_headers))
                sys.exit(errno.EINVAL)

        # 2. Check for missing mandatory headers
        mandatory_headers = NetworkFields.list_mandatory()
        missing_headers = mandatory_headers - valid_headers
        if missing_headers:
            logger.error("Missing mandatory field(s) in network file: %s",
                         ', '.join(missing_headers))
            sys.exit(errno.EINVAL)
        # Check if tuple "transmitters easting"/"transmitter northing" or "longitude"/"latitude" is present in headers
        long_lat_coordinates = NetworkFields.TRANSMITTER_LONGITUDE in valid_headers \
                               and NetworkFields.TRANSMITTER_LATITUDE in valid_headers \
                               and NetworkFields.TRANSMITTER_EASTING not in valid_headers \
                               and NetworkFields.TRANSMITTER_NORTHING not in valid_headers
        easting_northing_coordinates = NetworkFields.TRANSMITTER_EASTING in valid_headers \
                                       and NetworkFields.TRANSMITTER_NORTHING in valid_headers \
                                       and NetworkFields.TRANSMITTER_LONGITUDE not in valid_headers \
                                       and NetworkFields.TRANSMITTER_LATITUDE not in valid_headers
        if not (long_lat_coordinates ^ easting_northing_coordinates):
            logger.error(
                "Tuple 'transmitters easting'/'transmitter northing' "
                "or 'longitude'/'latitude' must be present in headers"
            )
            sys.exit(errno.EINVAL)

        # Read csv and create network list
        nb_line = 1
        for rows in csv_reader:
            data = {}
            for key in rows.keys():
                if rows[key]:
                    # Add the value to data dict only if the value is not null or empty
                    data[key] = rows[key]
                elif key in mandatory_headers:
                    # Validate csv value: Check for mandatory field with empty value
                    logger.error("Mandatory field '%s' with empty value in line %s of network file",
                                 key, nb_line)
                    sys.exit(errno.EINVAL)

            network_list.append(data)
            nb_line = nb_line + 1

    return network_list


def create_post_processing_request(json_input_file: dict, logger: logging.Logger) -> dict | None:
    """
    @summary: Create post processing request
    @param json_input_file: {dict} post processing settings
    @param logger: {logging.Logger} used to trace output log
    @return: {dict} post processing request object
    """
    new_postprocessing_request = None

    if "network" in json_input_file.keys():
        if get_prediction_type(json_input_file["predictionSettings"]) == "POINT":
            logger.warning("Post processing calculation ignored: "
                           "All predictions must be of type AREA")
        else:
            postprocessing_settings = json_input_file["network"]
            new_postprocessing_request = {
                "resolution": postprocessing_settings["resolution"],
                "computationType": postprocessing_settings["computationType"],
                "resultTypes": postprocessing_settings["computationResultType"]
            }
            if "dynamicParameters" in postprocessing_settings.keys():
                new_postprocessing_request["dynamicParameters"] = postprocessing_settings["dynamicParameters"]

            if "repeaterSeparated" in postprocessing_settings.keys():
                new_postprocessing_request["repeaterSeparated"] = postprocessing_settings["repeaterSeparated"]

            if COMPUTATION_ZONE in postprocessing_settings.keys():
                new_postprocessing_request[COMPUTATION_ZONE] = postprocessing_settings[COMPUTATION_ZONE]

    return new_postprocessing_request


def create_shapefile(json_input_file: dict) -> tuple | None:
    """
    @summary: Create shapefile multipart section for post processing request
    @param json_input_file: {dict} dictionary of settings for post processing
    @return: {tuple | None} shapefile multipart section or None if no shapefile
    """
    new_shapefile = None
    if "network" in json_input_file.keys() \
            and COMPUTATION_ZONE in json_input_file["network"].keys() \
            and FILTER_SHAPE in json_input_file["network"][COMPUTATION_ZONE].keys():
        filter_shape_file = json_input_file["network"][COMPUTATION_ZONE].pop(FILTER_SHAPE)
        check_shapefile_archive(filter_shape_file, LOGGER)
        if filter_shape_file:
            new_shapefile = (SHAPEFILE_ARCHIVE_PARAM,
                             (os.path.basename(filter_shape_file), open(filter_shape_file, 'rb'), APPLICATION_ZIP))
    return new_shapefile


def check_shapefile_archive(zip_path: str, logger: logging.Logger) -> None:
    """
    @summary: check files composing the shapefile archive
    @param zip_path: {str} path to the shapefile archive
    @param logger: {logging.Logger} used to trace output log
    """
    # Check shapefile path exists
    if not os.path.exists(zip_path):
        logger.error("Error post processing shapefile: %s does not exist", zip_path)
        sys.exit(errno.EINVAL)

    # Check shapefile is a shp file
    if not zip_path.endswith(".zip"):
        logger.error("Error post processing shapefile: %s is not a '.zip' file", zip_path)
        sys.exit(errno.EINVAL)

    filter_shape_name = Path(zip_path).stem

    # Check content of shapefile archive
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_content = zip_ref.namelist()
        # Remove directories from list of content
        zip_files = [f for f in zip_content if not f.endswith('/')]
        # Get mandatory files composing the shapefile
        mandatory_ext = tuple(SHAPE_FILE_EXT_MANDATORY)
        mandatory_files = [f for f in zip_files
                           if f.endswith(mandatory_ext) and Path(f).stem == filter_shape_name]
        if len(mandatory_files) != len(SHAPE_FILE_EXT_MANDATORY):
            logger.error("Error post processing shapefile archive: %s must contain at least %s files",
                         zip_path, mandatory_ext)
            sys.exit(errno.EINVAL)

        # Get optional files composing the shapefile
        optional_ext = tuple(SHAPE_FILE_EXT_OPTIONAL)
        optional_files = [f for f in zip_files
                          if (f.endswith(optional_ext) and Path(f).stem == filter_shape_name)
                          or (f.endswith(SHAPE_FILE_EXT_OPTIONAL_XML)
                              and ''.join(f.rsplit(SHAPE_FILE_EXT_OPTIONAL_XML, 1)) == filter_shape_name)]

        # Check if archive contains other files than mandatory and optional files
        unknown_files = [f for f in zip_files if f not in mandatory_files and f not in optional_files]
        if unknown_files:
            logger.error("Error post processing shapefile archive: must not contain the following files %s",
                         unknown_files)
            sys.exit(errno.EINVAL)


def pull_simulation_status(simulation_uuid: uuid.UUID,
                           authentication_data: Optional[dict], server: str,
                           logger: logging.Logger) -> None:
    """
    @summary: Pull simulation status every 5 seconds
    @param simulation_uuid: {uuid.UUID} uuid of the simulation
    @param authentication_data: {dict} authentication data
    @param server: {str} server url
    @param logger: {logging.Logger} used to trace output log
    """
    while True:
        time.sleep(5)
        res = call_request("GET", f"{server}simulations/{str(simulation_uuid)}/status",
                           authentication_data, logger)
        response = res.json()
        if res.status_code != 404:
            result_code = handle_pull_simulation_status_response(
                simulation_uuid, response, logger)
            if result_code == 0:
                # Status is done, break the loop
                break
        else:
            logger.error("Server unreachable : %s", str(res.status_code))
            break


def handle_pull_simulation_status_response(simulation_uuid: uuid.UUID,
                                           response: dict,
                                           logger: logging.Logger) -> int:
    """
    @summary: Handle the response returned by simulation status api call
    @param simulation_uuid: {uuid.UUID} uuid of the simulation
    @param response: {dict} response of api call
    @param logger: {logging.Logger} used to trace output log
    @return: {int} 0 if success, 1 if waiting and 2 if retry
    """
    progress = int(response["progress"])
    update_progress(progress)
    if response["state"] == "WAITING":
        return 1
    if response["state"] == "ERROR":
        logger.error("%s %s : %s", ERROR_SIMULATION, str(simulation_uuid), str(response['error']))

        for i, item in enumerate(response['errorMessages']):
            logger.error("%d : %s", i, item)

        sys.exit(errno.EINVAL)
    if response["state"] == "DONE":
        logger.info("Success simulation %s", str(simulation_uuid))
        return 0
    if response["state"] == "DONE_WITH_ERROR":
        logger.warning("Simulation finished : some steps failed %s",
                       str(simulation_uuid))
        for i, item in enumerate(response['errorMessages']):
            logger.error("%d : %s", i, item)
        logger.warning("Simulation may have partial results")
        return 0
    if response["state"] == "CANCELED":
        logger.warning("Simulation %s has been cancelled. The calculation was stopped.",
                       str(simulation_uuid))
        sys.exit(errno.EINVAL)
    return 1


def pull_post_processing_status(post_processing_uuid: uuid.UUID,
                                authentication_data: Optional[dict], server: str,
                                logger: logging.Logger) -> None:
    """
    @summary: Pull post processing status every 5 seconds
    @param post_processing_uuid: {uuid.UUID} uuid of the post processing
    @param authentication_data: {dict} authentication data
    @param server: {str} server url
    @param logger: {logging.Logger} used to trace output log
    """
    retry = True
    while True:
        time.sleep(5)
        res = call_request("GET", f"{server}postprocessings/{str(post_processing_uuid)}/status",
                           authentication_data, logger)
        response = res.json()
        if res.status_code != 404:
            result_code = handle_pull_post_processing_status_response(
                post_processing_uuid, response, retry, logger)
            if result_code == 2:
                # One error occurred, retry once
                retry = False
            elif result_code == 0:
                # Status is done, break the loop
                break
        else:
            logger.error("Server unreachable : %s", str(res.status_code))
            break


def handle_pull_post_processing_status_response(post_processing_uuid: uuid.UUID, response: dict,
                                                retry: bool, logger: logging.Logger) -> int:
    """
    @summary: Handle the response returned by post processing status api call
    @param post_processing_uuid: {uuid.UUID} uuid of the post processing
    @param response: {dict} response of api call
    @param retry: {bool} True if you have to retry the call, False else
    @param logger: {logging.Logger} used to trace output log
    @return: {int} 0 if success, 1 if waiting and 2 if retry
    """
    progress = int(response["progress"])
    update_progress(progress)
    if response["state"] == "WAITING":
        return 1
    if response["state"] == "ERROR":
        logger.error("%s %s %s",
                     ERROR_POST_PROCESSING, str(post_processing_uuid), response["error"])
        if retry:
            logger.warning("Retry")
            return 2
        sys.exit(errno.EINVAL)
    if response["state"] == "DONE":
        logger.info("Success post processing %s", str(post_processing_uuid))
        return 0
    if response["state"] == "CANCELED":
        logger.warning("Post processing %s has been cancelled. The calculation was stopped.",
                       str(post_processing_uuid))
        sys.exit(errno.EINVAL)
    return 1


def download_simulation_results(output_path: str, file_name: str,
                                simulation_uuid: uuid.UUID,
                                authentication_data: Optional[dict], server: str,
                                logger: logging.Logger) -> None:
    """
    @summary: Download the simulation results files
    @param output_path: {str} the path where to save the results files
    @param file_name: {str} the file name
    @param simulation_uuid: {uuid.UUID} uuid of the simulation
    @param authentication_data: {dict} authentication data
    @param server: {str} server url
    @param logger: {logging.Logger} used to trace output log
    """
    logger.info("Download simulation results %s", simulation_uuid)
    # Patch to slow down the script during the writing on the database
    time.sleep(1)
    i = 3
    results = {}
    while i > 0:
        res = call_request("GET", f"{server}simulations/{str(simulation_uuid)}/results",
                           authentication_data, logger)
        results = res.json()
        if res.status_code in (404, 400):
            logger.error("%s %s", ERROR_SIMULATION, get_error_message(results))
            sys.exit(errno.EINVAL)
        if len(results) > 0:
            break
        i = i - 1

    path = f"{output_path}/{file_name}/simulationResult/"
    create_directory(path)

    for result in results:
        # Check from result fileName if it contains subfolder (e.g. cells/)
        split_name = result["fileName"].rsplit("/", 1)
        folder_path = ''
        if len(split_name) == 2:
            folder_path = split_name[0]
            name = split_name[1]
        else:
            name = split_name[0]
        final_folder_path = os.path.join(path, folder_path)

        current_tiff = call_request("GET", f"{server}results/{str(result['uuid'])}/download",
                                    authentication_data, logger)
        if current_tiff.status_code != 200:
            logger.error("Error downloading %s", result["fileName"])
            sys.exit(errno.EINVAL)
        if folder_path != '' and not os.path.exists(final_folder_path):
            os.makedirs(final_folder_path)
        with open(os.path.join(final_folder_path, name), "wb") as result_file:
            result_file.write(current_tiff.content)


def get_resource_uri(server: str, resource_type: str, authentication_data: Optional[dict]) -> str:
    """
    @summary: Get the post resource uri according to the authentication data
    @param server: {str} server url
    @param resource_type: {str} resource to build url (eg. predictions, sessions...)
    @param authentication_data: {dict} authentication data
    @return: {str} the post resource uri
    """

    if authentication_data is None or not authentication_data["required"]:
        return f"{server}{resource_type}"

    return f"{server}{resource_type}/public" if authentication_data["publicPrediction"] \
        else f"{server}{resource_type}"


def fill_prediction_area(user_equipment_list: list, network_list: list, base_station_list: list,
                         index_user_equipment: int, index_base_station: int,
                         session_uuid: uuid.UUID, prediction_group_uuid: uuid.UUID,
                         prediction_settings: dict, models: dict, authentication_data: Optional[dict],
                         server: str, logger: logging.Logger) -> dict:
    """
    @summary: Fill a prediction object for area type
    @param user_equipment_list: {list} list of user equipment
    @param network_list: {dict} list of network datas
    @param base_station_list: {list} list of base station
    @param index_user_equipment: {int} index for user equipment list
    @param index_base_station: {int} index for base station list
    @param session_uuid: {uuid.UUID} uuid of the current session
    @param prediction_group_uuid: {uuid.UUID} uuid of the prediction group
    @param prediction_settings: {dict} dictionary of settings for prediction
    @param models: {dict} dictionary of models
    @param authentication_data: {dict} authentication data
    @param server: {str} server url
    @param logger: {logging.Logger} used to trace output log
    @return: {dict} the prediction object
    """
    prediction = {
        "uuid": str(uuid.uuid4()),
        "calculationSessionUuid": str(session_uuid),
        "creationDate": "",
        "resultTypesList": prediction_settings["predictionResultType"],
        "userEquipmentUuids": [user_equipment_list[index_user_equipment]["uuid"]],
        "predictionGroupUuids": [str(prediction_group_uuid)]
    }


    prediction[NAME] = base_station_list[index_base_station][NAME] + "_PREDICTION"
    model = get_model(network_list[index_base_station][NetworkFields.PROPAGATION_MODEL],
                      session_uuid, models, authentication_data, server, logger)
    prediction["modelUuid"] = model["uuid"]

    prediction["baseStationUuid"] = base_station_list[index_base_station]["uuid"]

    if "isotropic" in prediction_settings.keys():
        prediction["isotropic"] = prediction_settings["isotropic"]
    if "force" in prediction_settings.keys():
        prediction["force"] = prediction_settings["force"]
    if "priority" in prediction_settings.keys():
        prediction["priority"] = prediction_settings["priority"]

    return prediction


def fill_prediction_point(transmitter_list: list, network_list: list, base_station_list: list,
                          index_transmitter: int, session_uuid: uuid.UUID,
                          prediction_group_uuid: uuid.UUID, prediction_settings: dict, models: dict,
                          authentication_data, server: str, logger: logging.Logger) -> dict:
    """
    @summary: Fill a prediction object for point type
    @param transmitter_list: {list} list of transmitters
    @param network_list: {dict} list of network datas
    @param base_station_list: {list} list of base station
    @param index_transmitter: {int} index for transmitter list
    @param session_uuid: {uuid.UUID} uuid of the current session
    @param prediction_group_uuid: {uuid.UUID} uuid of the prediction group
    @param prediction_settings: {dict} dictionary of settings for prediction
    @param models: {dict} dictionary of models
    @param authentication_data: {dict} authentication data
    @param server: {str} server url
    @param logger: {logging.Logger} used to trace output log
    @return: {dict} the prediction object
    """
    model = get_model(network_list[index_transmitter][NetworkFields.PROPAGATION_MODEL],
                      session_uuid, models, authentication_data, server, logger)

    prediction = {
        "uuid": str(uuid.uuid4()),
        "name": base_station_list[index_transmitter][NAME] + "_PREDICTION",
        "baseStationUuid": base_station_list[index_transmitter]["uuid"],
        "calculationSessionUuid": str(session_uuid),
        "predictionGroupUuids": [str(prediction_group_uuid)],
        "creationDate": "",
        "resultTypesList": prediction_settings["predictionResultType"],
        "userEquipmentUuids": list(
            map(lambda x: x["uuid"], transmitter_list[index_transmitter]["receivers"])),
        "modelUuid": model["uuid"]
    }

    if "isotropic" in prediction_settings.keys():
        prediction["isotropic"] = prediction_settings["isotropic"]
    if "force" in prediction_settings.keys():
        prediction["force"] = prediction_settings["force"]
    if "priority" in prediction_settings.keys():
        prediction["priority"] = prediction_settings["priority"]

    return prediction


def pull_prediction_group_status(prediction_group_uuid: uuid.UUID,
                                 authentication_data: Optional[dict], server: str,
                                 logger: logging.Logger) -> None:
    """
    @summary: Pull prediction group status every 5 seconds
    @param prediction_group_uuid: {uuid.UUID} uuid of the prediction group
    @param authentication_data: {dict} authentication data
    @param server: {str} server url
    @param logger: {logging.Logger} used to trace output log
    """
    retry = True
    while True:
        time.sleep(5)
        res = call_request("GET", f"{server}predictiongroups/{str(prediction_group_uuid)}/status",
                           authentication_data, logger)
        response = res.json()
        if res.status_code != 404:
            result_code = handle_pull_prediction_group_status_response(
                prediction_group_uuid, response, retry, authentication_data, server, logger)
            if result_code == 2:
                # One error occurred, retry once
                retry = False
            elif result_code == 0:
                # Status is done, break the loop
                break
        else:
            logger.error("Server unreachable : %s", str(res.status_code))
            break


def handle_pull_prediction_group_status_response(prediction_group_uuid: uuid.UUID,
                                                 response: dict, retry: bool,
                                                 authentication_data: Optional[dict], server: str,
                                                 logger: logging.Logger) -> int:
    """
    @summary: Handle the response returned by prediction group status api call
    @param prediction_group_uuid: {uuid.UUID} uuid of the prediction group
    @param response: {dict} response of api call
    @param retry: {bool} True if you have to retry the call, False else
    @param authentication_data: {dict} authentication data
    @param server: {str} server url
    @param logger: {logging.Logger} used to trace output log
    @return: {int} 0 if success, 1 if waiting and 2 if retry
    """
    progress = int(response["progress"])
    update_progress(progress)
    if response["state"] == "WAITING":
        return 1
    if response["state"] == "ERROR":
        logger.error("%s %s",
                     ERROR_PREDICTION_GROUP, str(prediction_group_uuid))
        if retry:
            logger.warning("Retry")
            return 2
        get_predictions_errors(prediction_group_uuid, authentication_data, server, logger)
        sys.exit(errno.EINVAL)
    if response["state"] == "DONE":
        logger.info("Success prediction group %s", str(prediction_group_uuid))
        return 0
    if response["state"] == "DONE_WITH_ERROR":
        logger.warning("Prediction group finished : some predictions failed %s",
                       str(prediction_group_uuid))
        logger.warning("Post processing will be launched with partial results")
        return 0
    if response["state"] == "CANCELED":
        logger.warning("Prediction group %s has been cancelled. The calculation was stopped.",
                       str(prediction_group_uuid))
        sys.exit(errno.EINVAL)
    return 1


def download_simulation_predictions_results(simulation_uuid: uuid.UUID,
                                            output_path: str, file_name: str,
                                            authentication_data: Optional[dict], server: str,
                                            logger: logging.Logger) -> None:
    """
    @summary: Download the predictions results files of the simulation
    @param simulation_uuid: {uuid.UUID} uuid of the simulation
    @param output_path: {str} the path where to save the results files
    @param file_name: {str} the file name
    @param authentication_data: {dict} authentication data
    @param server: {str} server url
    @param logger: {logging.Logger} used to trace output log
    """
    logger.info("Download predictions results of simulation %s", simulation_uuid)
    path = f"{output_path}/{file_name}/predictionsResults/"
    create_directory(path)

    # Get simulation's prediction group
    res = call_request("GET", f"{server}simulations/{simulation_uuid}",
                       authentication_data, logger)
    results = res.json()
    if res.status_code in (404, 400):
        logger.error(ERROR_SIMULATION_LOG, get_error_message(results))
        sys.exit(errno.EINVAL)
    prediction_group_uuid = None
    for step in results.get("steps", []):
        if "predictionGroupUuid" in step:
            prediction_group_uuid = step["predictionGroupUuid"]
            break
    if prediction_group_uuid is None:
        logger.error(f"Prediction group uuid cannot be extract from simulation {simulation_uuid}")

    # Get predictions of prediction group
    res = call_request("GET", f"{server}predictions",
                       authentication_data, logger, params={"groupid": prediction_group_uuid})
    prediction_list = res.json()
    if res.status_code in (404, 400):
        logger.error(ERROR_PREDICTION_LOG, get_error_message(results))
        sys.exit(errno.EINVAL)

    # Patch to slow down the script during the writing on the database
    time.sleep(1)
    for prediction in prediction_list:
        i = 3
        results = {}
        while i > 0:
            res = call_request("GET", f"{server}predictions/{str(prediction['uuid'])}/results",
                               authentication_data, logger)
            results = res.json()
            if len(results) > 0:
                break
            if res.status_code in (404, 400):
                logger.error(ERROR_PREDICTION_LOG, get_error_message(results))
                sys.exit(errno.EINVAL)
            i = i - 1
        pred_path = path + prediction[NAME] + "/"
        create_directory(pred_path)

        for result in results:
            name = result["fileName"]
            current_tiff = call_request("GET", f"{server}results/{str(result['uuid'])}/download",
                                        authentication_data, logger)
            if current_tiff.status_code != 200:
                logger.error("Error downloading %s", name)
                sys.exit(errno.EINVAL)
            with open(pred_path + name, "wb") as result_file:
                result_file.write(current_tiff.content)


def get_predictions_errors(prediction_group_uuid: uuid.UUID, authentication_data: Optional[dict],
                           server: str, logger: logging.Logger) -> None:
    """
    @summary: Get predictions errors
    @param prediction_group_uuid: {uuid.UUID} uuid of the prediction group
    @param authentication_data: {dict} authentication data
    @param server: {str} server url
    @param logger: {logging.Logger} used to trace output log
    """
    param = {
        "groupid": str(prediction_group_uuid)
    }
    res = call_request("GET", f"{server}predictions", authentication_data, logger, params=param)
    prediction_list = res.json()
    if res.status_code in (404, 400):
        logger.error("Error getting predictions : server unreachable ?")
        sys.exit(errno.EINVAL)
    for prediction in prediction_list:
        if prediction["status"]["state"] == "ERROR":
            logger.error("%s : %s", prediction[NAME], prediction["status"]["error"])
    sys.exit(errno.EINVAL)


def create_session(session: dict, session_uuid: uuid.UUID, authentication_data: Optional[dict],
                   server: str, logger: logging.Logger) -> None:
    """
    @summary: Create a session
    @param session: {dict} session object to create
    @param session_uuid: {uuid.UUID} uuid of the current session
    @param authentication_data: {dict} authentication data
    @param server: {str} server url
    @param logger: {logging.Logger} used to trace output log
    """
    logger.info("Creation session")
    session["uuid"] = str(session_uuid)
    result = call_request("POST", get_resource_uri(server, "sessions", authentication_data),
                          authentication_data, logger, json_content=session).json()
    if "status" in result.keys() and result["status"] != 406:
        logger.error("Error session %s : %s", session[NAME], get_error_message(result))
        sys.exit(errno.EINVAL)
    logger.info("Session : %s", session["uuid"])


def fill_user_equipment(network: dict, session_uuid: uuid.UUID, data_dict: dict, antenna_dict: dict,
                        logger: logging.Logger) -> dict:
    """
    @summary: Fill a user equipment object
    @param network: {dict} network datas
    @param session_uuid: {uuid.UUID} uuid of the current session
    @param data_dict: {dict} dictionary of parameters
    @param antenna_dict: {dict} dict of antenna for name to uuid mapping
    @param logger: {logging.Logger} used to trace output log
    @return: {dict} the user equipment object
    """
    user_equipment = {
        "sessionUuid": str(session_uuid),
        "description": get_from_dict(network, NetworkFields.COMMENTS, ""),
        "zmeaning": handle_zmeaning(data_dict["predictionSettings"], logger)
    }
    transmitter_long_lat_coordinate = (NetworkFields.TRANSMITTER_LONGITUDE in network
                                       and NetworkFields.TRANSMITTER_LATITUDE in network)

    if ("type" in data_dict["predictionSettings"] and
            data_dict["predictionSettings"]["type"] == "POINT"):
        receiver_long_lat_coordinate = (NetworkFields.RECEIVER_LONGITUDE in network
                                        and NetworkFields.RECEIVER_LATITUDE in network)
        user_equipment["type"] = "POINT"

        point_ue_fields = [NetworkFields.RECEIVER_NAME,
                           NetworkFields.RECEIVER_HEIGHT,
                           NetworkFields.RECEIVER_LONGITUDE if receiver_long_lat_coordinate
                           else NetworkFields.RECEIVER_EASTING,
                           NetworkFields.RECEIVER_LATITUDE if receiver_long_lat_coordinate
                           else NetworkFields.RECEIVER_NORTHING]
        found_point_ue_fields = \
            list(x in network.keys() and network.get(x) != '' for x in point_ue_fields)
        if not all(found_point_ue_fields):
            logger.error("Error user equipment: For POINT user equipment, "
                         "All values must be configured among %s",
                         point_ue_fields)
            sys.exit(errno.EINVAL)

        user_equipment[NAME] = get_from_dict(network, NetworkFields.RECEIVER_NAME)
        user_equipment["heights"] = [get_from_dict(network, NetworkFields.RECEIVER_HEIGHT)]
        user_equipment["coordinates"] = {
            "x": get_float_from_dict(network, NetworkFields.RECEIVER_LONGITUDE)
            if receiver_long_lat_coordinate else get_float_from_dict(network, NetworkFields.RECEIVER_EASTING),
            "y": get_float_from_dict(network, NetworkFields.RECEIVER_LATITUDE)
            if receiver_long_lat_coordinate else get_float_from_dict(network, NetworkFields.RECEIVER_NORTHING),
            "epsgCode": 4326 if transmitter_long_lat_coordinate else None
        }

        # check for receiver antenna
        if network.get(NetworkFields.RECEIVER_ANTENNA):
            user_equipment["antenna"] = get_from_dict(network, NetworkFields.RECEIVER_ANTENNA)
            user_equipment["antennaUuid"] = get_resource_uuid_from_cache("Antenna", antenna_dict,
                                                                         user_equipment["antenna"], logger)
            user_equipment["azimuth"] = get_from_dict(network, NetworkFields.RECEIVER_AZIMUTH, "0")
            user_equipment["downtilt"] = get_from_dict(network, NetworkFields.RECEIVER_DOWNTILT, "0")
    else:
        user_equipment["type"] = "AREA"

        area_ue_fields = [NetworkFields.CALCULATION_RESOLUTION, NetworkFields.CALCULATION_RADIUS]
        found_area_ue_fields = \
            list(x in network.keys() and network.get(x) != '' for x in area_ue_fields)
        if not all(found_area_ue_fields):
            logger.error("Error user equipment: For AREA user equipment, "
                         "All values must be configured among %s",
                         area_ue_fields)
            sys.exit(errno.EINVAL)

        user_equipment[NAME] = get_from_dict(network, NetworkFields.TRANSMITTER_NAME)
        user_equipment["heights"] = data_dict["predictionSettings"]["receptionHeights"]
        resolution = get_float_from_dict(network, NetworkFields.CALCULATION_RESOLUTION)
        if "shiftGridCenter" in data_dict["predictionSettings"].keys() \
                and data_dict["predictionSettings"]["shiftGridCenter"] is True:
            # Shift Grid Center of user equipement
            tx_x = get_float_from_dict(network, NetworkFields.TRANSMITTER_LONGITUDE) \
                if transmitter_long_lat_coordinate else get_float_from_dict(network, NetworkFields.TRANSMITTER_EASTING)
            tx_y = get_float_from_dict(network, NetworkFields.TRANSMITTER_LATITUDE) \
                if transmitter_long_lat_coordinate else get_float_from_dict(network, NetworkFields.TRANSMITTER_NORTHING)
            # Define the center of the grid according to the resolution
            tx_x_grid = resolution * math.floor((tx_x + resolution / 2) / resolution)
            tx_y_grid = resolution * math.floor((tx_y + resolution / 2) / resolution)

        else:
            # default use case
            tx_x_grid = get_float_from_dict(network, NetworkFields.TRANSMITTER_LONGITUDE) \
                if transmitter_long_lat_coordinate else get_float_from_dict(network, NetworkFields.TRANSMITTER_EASTING)
            tx_y_grid = get_float_from_dict(network, NetworkFields.TRANSMITTER_LATITUDE) \
                if transmitter_long_lat_coordinate else get_float_from_dict(network, NetworkFields.TRANSMITTER_NORTHING)

        calculation_radius = get_float_from_dict(network, NetworkFields.CALCULATION_RADIUS)
        if transmitter_long_lat_coordinate:
            r_earth = 6378.137  # radius of the earth in kilometer
            m = (1 / ((2 * math.pi / 360) * r_earth)) / 1000  # 1 meter in degree
            lat_min = tx_y_grid - (calculation_radius * m)
            lat_max = tx_y_grid + (calculation_radius * m)
            long_min = tx_x_grid - (calculation_radius * m) / math.cos(lat_min * (math.pi / 180))
            long_max = tx_x_grid + (calculation_radius * m) / math.cos(lat_max * (math.pi / 180))
            user_equipment["coordinates"] = {
                "xmin": long_min,
                "xmax": long_max,
                "ymin": lat_min,
                "ymax": lat_max,
                "resolution": resolution,
                "epsgCode": 4326
            }
        else:
            user_equipment["coordinates"] = {
                "xmin": tx_x_grid - calculation_radius,
                "xmax": tx_x_grid + calculation_radius,
                "ymin": tx_y_grid - calculation_radius,
                "ymax": tx_y_grid + calculation_radius,
                "resolution": resolution
            }

    return user_equipment


def handle_zmeaning(prediction_settings: dict, logger: logging.Logger) -> str:
    """
    @summary: Handle zmeaning value for user equipment
    @param prediction_settings: {dict} dictionary of settings for prediction
    @param logger: {logging.Logger} used to trace output log
    @return: {str} zmeaning value
    """
    zmeaning = "ZMEANING_GROUND"
    if "receptionHeightReference" in prediction_settings.keys():
        if "CLUTTER" == prediction_settings["receptionHeightReference"]:
            zmeaning = "ZMEANING_CLUTTER"
        elif "ALTITUDE" == prediction_settings["receptionHeightReference"]:
            zmeaning = "ZMEANING_ALTITUDE"
        else:
            if "GROUND" == prediction_settings["receptionHeightReference"]:
                zmeaning = "ZMEANING_GROUND"
            else:
                logger.error("unknown receptionHeightReference, must be GROUND or CLUTTER")
                sys.exit(errno.EINVAL)
    return zmeaning





def is_same_base_station(base_station_1: dict, base_station_2: dict) -> bool:
    """
    @summary: Check if the two base stations in parameter are the same
    @param base_station_1: {dict} first base station to compare
    @param base_station_2: {dict} second base station to compare
    @return: {bool} True if equals, False else
    """
    return (
            base_station_1["networkId"] == base_station_2["networkId"] and
            base_station_1["name"] == base_station_2["name"] and
            base_station_1["x"] == base_station_2["x"] and
            base_station_1["y"] == base_station_2["y"] and
            base_station_1["z"] == base_station_2["z"] and
            base_station_1["azimuth"] == base_station_2["azimuth"] and
            base_station_1["downtilt"] == base_station_2["downtilt"] and
            base_station_1["carrierFrequency"] == base_station_2["carrierFrequency"] and
            base_station_1["transmitPower"] == base_station_2["transmitPower"]
    )


def create_simulation_request(simulation_uuid: uuid.UUID, network_list: list, settings: dict,
                              session_uuid: uuid.UUID, antenna_dict: dict, models: dict,
                              authentication_data: Optional[dict], server: str, logger: logging.Logger) -> None:
    """
    @summary: Create simulation request
    @param simulation_uuid: {uuid.UUID} simulation uuid
    @param network_list: {dict} list of network datas
    @param settings: {dict} dictionary of settings
    @param session_uuid: {uuid.UUID} uuid of the current session
    @param antenna_dict: {dict} dict of antenna for name to uuid mapping
    @param models: {dict} dict of models for name to uuid mapping
    @param authentication_data: {dict} authentication data
    @param server: {str} server url
    @param logger: {logging.Logger} logger
    @return: {list} the list of user equipments created
    """
    logger.info("Creation simulation request")

    # Init simulation request object
    simulation_request: dict[Any, Any] = {
        "uuid": str(simulation_uuid),
        "name": f"{settings['session']['name']}_postprocessing",
        "calculationSessionUuid": str(session_uuid)
    }

    propagation_request = create_propagation_request(network_list, settings, session_uuid,
                                                     antenna_dict, models, logger)
    if propagation_request is not None:
        simulation_request["propagationRequest"] = propagation_request

    postprocessing_request = create_post_processing_request(settings, logger)
    if postprocessing_request is not None:
        simulation_request["postprocessingRequest"] = postprocessing_request

    multipart_form_data = [(JSON_PARAM, (None, json.dumps(simulation_request), APPLICATION_JSON))]
    shapefile = create_shapefile(settings)
    if shapefile:
        multipart_form_data.append(shapefile)

    res = call_request("POST", get_resource_uri(server, "simulations", authentication_data),
                       authentication_data, logger, files=multipart_form_data)
    result = res.json()
    if res.status_code not in (200, 201):
        logger.error("Error simulation %s", get_error_message(result))
        sys.exit(errno.EINVAL)

    logger.info("Simulation : %s", result["uuid"])


def create_propagation_request(network_list: list, settings: dict, session_uuid: uuid.UUID,
                               antenna_dict: dict, models: dict, logger: logging.Logger) -> dict:
    """
    @summary: Create propagation request
    @param network_list: {dict} list of network datas
    @param settings: {dict} dictionary of settings for prediction
    @param session_uuid: {uuid.UUID} uuid of the current session
    @param antenna_dict: {dict} dict of antenna for name to uuid mapping
    @param models: {dict} dict of models for name to uuid mapping
    @param logger: {logging.Logger} used to trace output log
    @return: {list} the list of user equipments created
    """
    if get_prediction_type(settings["predictionSettings"]) == "POINT":
        logger.error("Cannot create POINT simulations")
        sys.exit(errno.EINVAL)

    propagation_list: List[dict] = []
    for network in network_list:
        # fill base station
        new_base_station = fill_base_station(network, get_computation_type(settings),
                                             session_uuid, antenna_dict, logger)
        # fill user equipment
        new_user_equipment = fill_user_equipment(network, session_uuid, settings, antenna_dict, logger)
        # fill propagation model uuid
        model_name = get_from_dict(network, NetworkFields.PROPAGATION_MODEL)
        model_uuid = get_resource_uuid_from_cache("PropagationModel", models,
                                                  model_name, logger)

        already_exist = False
        for propagation in propagation_list:
            base_station = propagation["baseStation"]
            if is_same_base_station(base_station, new_base_station):
                if new_user_equipment["type"] == "POINT":
                    # Should not happen
                    propagation["userEquipments"].append(new_user_equipment)
                    already_exist = True
                    break
                else:
                    logger.error("Cannot create point to multi points simulations")
                    sys.exit(errno.EINVAL)

        if not already_exist:
            new_propagation = {
                "baseStation": new_base_station,
                "userEquipments": [new_user_equipment],
                "propagationModelUuid": model_uuid
            }
            propagation_list.append(new_propagation)


    new_propagation_request = {
        "propagationScenarios": propagation_list,
        "resultTypes": settings["predictionSettings"]["predictionResultType"],
        "heights": settings["predictionSettings"]["receptionHeights"],
        "zmeaning": handle_zmeaning(settings["predictionSettings"], logger)
    }
    if "isotropic" in settings["predictionSettings"].keys():
        new_propagation_request["isotropic"] = settings["predictionSettings"]["isotropic"]
    if "force" in settings["predictionSettings"].keys():
        new_propagation_request["force"] = settings["predictionSettings"]["force"]
    if "priority" in settings["predictionSettings"].keys():
        new_propagation_request["priority"] = settings["predictionSettings"]["priority"]

    return new_propagation_request


def call_request(method: str, url: str, authentication_data: Optional[dict], logger: logging.Logger,
                 files: list | None = None, json_content: Union[dict, list] | None = None,
                 params: dict | None = None, retry: int = 0, timeout=None) -> requests.Response:
    """
    @summary: call requests with args for use authenticate or not
    @param method: {str} method request
    @param url: {str} url request
    @param authentication_data: {dict} authentication data
    @param logger: {logging.Logger} logger
    @param files: {list} files request
    @param json_content: {dict} json request
    @param params: {dict} params request
    @param retry: {int} number of retry
    @param timeout: {Any} timeout request
    @return: {request.Response} response of request
    """

    headers = None

    if authentication_data is not None and "required" in authentication_data.keys() and authentication_data["required"]:
        token = get_access_token(authentication_data, logger)
        headers = {"Authorization": f"Bearer {token}"}

    res = None
    if method.upper() == "POST":
        res = requests.post(url=url, files=files, json=json_content, params=params,
                            timeout=timeout, headers=headers)
    elif method.upper() == "PUT":
        res = requests.put(url=url, files=files, json=json_content, params=params,
                           timeout=timeout, headers=headers)
    elif method.upper() == "GET":
        res = requests.get(url=url, files=files, json=json_content, params=params,
                           timeout=timeout, headers=headers)
    elif method.upper() == "DELETE":
        res = requests.delete(url=url, files=files, json=json_content, params=params,
                              timeout=timeout, headers=headers)
    else:
        logger.error("Method name %S not implemented", method.upper())
        sys.exit(errno.EINVAL)

    # If access_token expires, refresh the token one time and recall requests
    if res.status_code == 403 and retry == 0:
        refresh_token(authentication_data, logger)
        res = call_request(method, url, authentication_data, logger,
                           files, json_content, params, 1, timeout)

    return res


def get_access_token(authentication_data: Optional[dict], logger: logging.Logger) -> str:
    """
    @summary: Retrieve an access token
    @param authentication_data: {dict} authentication data
    @param logger: {logging.Logger} logger
    @return: {str} access token provided
    """

    global ACCESS_TOKEN, REFRESH_TOKEN
    if ACCESS_TOKEN is not None:
        return ACCESS_TOKEN
    authentication_data = cast(dict, authentication_data)
    payload = {
        "grant_type": "password",
        "client_id": authentication_data["clientId"],
        "client_secret": authentication_data["clientSecret"],
        "username": authentication_data["username"],
        "password": authentication_data["password"]
    }

    response = requests.post(
        authentication_data["url"],
        data=payload
    )

    json_response = response.json()

    if response.status_code == 200:
        ACCESS_TOKEN = json_response["access_token"]
        REFRESH_TOKEN = json_response["refresh_token"]
    else:
        logger.error("Error call get access token: %s", json_response["error_description"])
        sys.exit(errno.EINVAL)
    return ACCESS_TOKEN


def refresh_token(authentication_data: Optional[dict], logger: logging.Logger) -> None:
    """
    @summary: Refresh the access token
    @param authentication_data: {dict} authentication data
    @param logger: {logging.Logger} logger
    """

    global ACCESS_TOKEN, REFRESH_TOKEN
    if REFRESH_TOKEN is None:
        logger.error("Error call refresh token : refresh token is empty")
        sys.exit(errno.EINVAL)

    authentication_data = cast(dict, authentication_data)
    payload = {
        "grant_type": "refresh_token",
        "client_id": authentication_data["clientId"],
        "client_secret": authentication_data["clientSecret"],
        "refresh_token": REFRESH_TOKEN
    }

    response = requests.post(
        authentication_data["url"],
        data=payload
    )

    json_response = response.json()

    if response.status_code == 200:
        ACCESS_TOKEN = json_response["access_token"]
        REFRESH_TOKEN = json_response["refresh_token"]
    else:
        logger.error("Error call get refresh token: %s", json_response["error_description"])
        sys.exit(errno.EINVAL)


def get_error_message(response: dict) -> str:
    """
    @summary: Extract error message from json response
    @param response: {dict} json response
    @return: {str} the error message
    """
    message = ""
    if 'message' in response.keys():
        message = response["message"]
    elif 'params' in response.keys() and 'parameter' in response["params"]:
        message = response["params"]["parameter"]
    if not message:
        message = "Unknown error"
    if 'detail' in response.keys():
        message = f"{message}. ({response['detail']})"
    return message


# Main class that sequences api calls to launch prediction and post processing calculations
if __name__ == "__main__":
    arguments = parse_args()
    json_input_file = json.load(arguments.inputFile)

    get_script_information(LOGGER)

    start_execution_time = time.time()
    server_url = json_input_file["serverUrl"]

    new_file_name = json_input_file["predictionSettings"]["networkFile"].split("/")
    new_file_name = new_file_name[len(new_file_name) - 1]
    new_file_name = new_file_name.split(".")[0]

    if 'authentication' in json_input_file.keys():
        AUTHENTICATION = json_input_file["authentication"]

    new_network_list = create_network_list(json_input_file["predictionSettings"]["networkFile"], LOGGER)

    # Functions call
    MAPDATA_MAP = create_mapdatas(json_input_file["mapdata"], AUTHENTICATION, server_url, LOGGER)

    ANTENNA_MAP = create_antennas(json_input_file["antennas"], AUTHENTICATION, server_url, LOGGER)

    if get_computation_type(json_input_file) == SINR5G and "gob" in json_input_file.keys():
        gob_dict = create_gobs(json_input_file["gob"], ANTENNA_MAP, AUTHENTICATION, server_url, LOGGER)
        ANTENNA_MAP = {**ANTENNA_MAP, **gob_dict}

    create_session(json_input_file["session"], SESSION_UUID, AUTHENTICATION, server_url, LOGGER)

    MODEL_MAP = create_model(json_input_file["models"], MAPDATA_MAP, SESSION_UUID,
                             AUTHENTICATION, server_url, LOGGER)

    # output Path : sessionName/date/networkFileName
    output_directory_path = json_input_file["outputPath"] \
                            + json_input_file["session"][NAME] + "/" \
                            + time.strftime("%Y%m%d-%H%M%S", time.gmtime(time.time())) + "/"

    # Start simulation creation
    LOGGER.info("Simulation calculation ...")

    create_simulation_request(SIMULATION_UUID, new_network_list, json_input_file,
                              SESSION_UUID, ANTENNA_MAP, MODEL_MAP,
                              AUTHENTICATION, server_url, LOGGER)

    start_simulation_time = time.time()
    pull_simulation_status(SIMULATION_UUID, AUTHENTICATION,
                           server_url, LOGGER)
    end_simulation_computation_time = time.time()

    download_simulation_results(output_directory_path, new_file_name,
                                SIMULATION_UUID, AUTHENTICATION,
                                server_url, LOGGER)

    end_simulation_execution_time = time.time()

    # Download prediction results if -p argument is present
    if arguments.downloadPrediction:
        download_simulation_predictions_results(
            SIMULATION_UUID, output_directory_path, new_file_name, AUTHENTICATION, server_url, LOGGER)

    end_prediction_download_time = time.time()

    LOGGER.info("Simulation execution time: %.2f seconds",
                (end_simulation_execution_time - start_simulation_time))
    LOGGER.info("    - Simulation computation time: %.2f seconds",
                (end_simulation_computation_time - start_simulation_time))
    LOGGER.info("    - Simulation download time: %.2f seconds",
                (end_simulation_execution_time - end_simulation_computation_time))
    if arguments.downloadPrediction:
        LOGGER.info("    - Prediction download time: %.2f seconds",
                    (end_prediction_download_time - end_simulation_execution_time))

    LOGGER.info("Job done. All results are available in the following path : %s%s",
                output_directory_path, new_file_name)

    # Delete volcano scenarii folders
    if "deleteScenariiDir" in json_input_file["predictionSettings"].keys() \
            and json_input_file["predictionSettings"]["deleteScenariiDir"] is True:
        LOGGER.info("Deleting volcanoweb scenarii folders ...")
        delete_scenarii_dir(AUTHENTICATION, server_url, LOGGER)

    LOGGER.info("Total execution time: %.2f seconds", (time.time() - start_execution_time))
