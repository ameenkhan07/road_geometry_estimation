import json
import os
from pprint import pprint
import csv
import xmltodict
import requests
from utils import *
from mapbox import MapMatcher, Static
import osrm
from osrm import Point, simple_route


CONFIG = "config.json"
GPS_FILE = "./data/gps.txt"
OSM_FILE = "./data/map.osm"
OUTPUT = "./outputs/"
# API_MATCHING_URL = ""
# GRAPHHOPPER_MAP_MATCHING_URL = https://graphhopper.com/api/1/match?vehicle


def set_access_token() -> str:
    """Return access token from file
    """
    with open(CONFIG) as config_file:
        data = json.load(config_file)
        os.environ["MAPBOX_ACCESS_TOKEN"] = data["mapbox_token"]


def preprocess_osm_data() -> dict:
    """Preprocess OSM data for MapMatching
    Data manually downloaded from OSM site:
        https://wiki.openstreetmap.org/wiki/Downloading_data
    """
    node_data = []
    way_data = []
    fields = ["@lat", "@lon", "@timestamp"]
    headers = []

    with open(OSM_FILE) as fd:
        doc = xmltodict.parse(fd.read())
        node_headers = list(doc["osm"]["node"][0].keys())
        ways_headers = list(doc["osm"]["way"][0].keys())
        for row in doc["osm"]["node"]:
            temp = {k.lstrip("@a"): v for k, v in row.items()}
            # temp["timestamp"] = utc_to_epoch(row["@timestamp"])
            node_data.append(temp)
        for row in doc["osm"]["way"]:
            temp = {k.lstrip("@a"): v for k, v in row.items()}
            # temp["timestamp"] = utc_to_epoch(row["@timestamp"])
            way_data.append(temp)

    # print(node_headers, "\n", ways_headers)
    return (node_data, way_data)


def preprocess_gps_data() -> list:
    """Preprocess smartphone data for MapMatching
    """
    data = []
    # fields = ["timestamp", "lat", "lon"]
    fields = ["lat", "lon"]

    with open(GPS_FILE, mode="r") as csv_file:
        reader = csv.DictReader(csv_file, delimiter=",")
        for row in reader:
            temp = {k: v for k, v in row.items() if k in fields}
            # temp["timestamp"] = epoch_to_utc(row["timestamp"][:10])
            data.append(temp)

    # pprint(data)
    return data


def generate_mapbox_static_maps(data, suffix):
    """Generates Mapbox static maps given the data
    The data should be in GeoJSON format
    """
    # Remove unrequired values, to keep the data light for map generation
    del data["properties"]["matchedPoints"]
    del data["properties"]["indices"]
    static_map = Static(access_token=os.environ["MAPBOX_ACCESS_TOKEN"])
    response = static_map.image("mapbox.streets", features=data)
    # print("StaticMap", response.status_code)
    save_map_imgs(OUTPUT, suffix, response.content)


def mapbox_mapmatching(gps_data):
    """Checks gps correctness using Mapbox MapMatching API
    https://docs.mapbox.com/api/navigation/#map-matching
    """

    # GeoJson for Mapbox API's
    line = dict()
    line["type"] = "Feature"
    line["properties"] = {"coordTimes": []}
    line["geometry"] = {"type": "LineString", "coordinates": []}

    # Create a verified path using matmatching api
    map_matcher = MapMatcher(access_token=os.environ["MAPBOX_ACCESS_TOKEN"])

    # Select Attributes for displaying the path on static map
    corrected = []
    batch_size = len(gps_data) // 100
    for i in range(batch_size + 1):
        st = i * 100
        line["geometry"]["coordinates"] = [
            [float(row["lon"]), float(row["lat"])] for row in gps_data[st : st + 100]
        ]
        response = map_matcher.match(line, profile="mapbox.driving")
        corr = response.geojson()["features"][0]
        # print("MapMatching", response.status_code)
        # print(i,len(corr["properties"]["matchedPoints"]))
        corr["geometry"]["coordinates"] = corr["properties"]["matchedPoints"]

        corrected.append(corr)

        # Plot points on Static Map
        generate_mapbox_static_maps(corr, i)

    save_data(OUTPUT, corrected, "corrected.json")
    return corrected


if __name__ == "__main__":

    set_access_token()

    osm_node_data, osm_way_data = preprocess_osm_data()

    gps_data = preprocess_gps_data()

    mapbox_mapmatching(gps_data)
