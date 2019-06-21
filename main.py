import json
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


def get_access_token() -> str:
    """Return access token from file
    """
    with open(CONFIG) as config_file:
        data = json.load(config_file)
        mapbox_access_token = data["mapbox_token"]
    return mapbox_access_token


def preprocess_osm_data() -> dict:
    """Preprocess OSM data for MapMatching
    Data manually donwloaded from OSM site:
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
    # ppprint(node_data[0])
    # ppprint(way_data[0])
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


def mapbox_display_route(gps_data):
    """Checks gps correctness using Mapbox MapMatching API
    https://docs.mapbox.com/api/navigation/#map-matching
    """
    # print(len(gps_data))
    mapbox_access_token = get_access_token()

    # GeoJson for Mapbox API's
    line = dict()
    line["type"] = "Feature"
    line["properties"] = {"coordTimes": []}
    line["geometry"] = {"type": "LineString", "coordinates": []}

    # Create a clean path using matmatching api
    map_matcher = MapMatcher(access_token=mapbox_access_token)

    # Select Attributes for displaying the path on static map
    corrected = []
    batch_size = len(gps_data) // 100
    for i in range(batch_size):
        st = i * 100
        line["geometry"]["coordinates"] = [
            [float(row["lon"]), float(row["lat"])] for row in gps_data[st : st + 100]
        ]
        response = map_matcher.match(line, profile="mapbox.driving")
        corr = response.geojson()["features"][0]
        # print("MapMatching", response.status_code)
        print(
            i,
            len(corr["geometry"]["coordinates"]),
            len(corr["properties"]["matchedPoints"]),
        )
        corr["geometry"]["coordinates"] = corr["properties"]["matchedPoints"]
        del corr["properties"]["matchedPoints"]
        del corr["properties"]["indices"]
        corrected.append(corr)

        # Plot points on Static Map
        static_map = Static(access_token=mapbox_access_token)
        response = static_map.image("mapbox.streets", features=corr)
        # print('StaticMap', response.status_code)
        save_map_imgs(OUTPUT, i, response.content)


if __name__ == "__main__":

    osm_node_data, osm_way_data = preprocess_osm_data()

    gps_data = preprocess_gps_data()

    mapbox_display_route(gps_data)
