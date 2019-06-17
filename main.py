import requests
import json
import csv
import xmltodict
import time
import sys
from pprint import pprint
from mapbox import MapMatcher, Static
import osrm

CONFIG = "config.json"
GPS_FILE = "./data/gps.txt"
OSM_FILE = "./data/map.osm"
OUTPUT = "./outputs/"
# API_MATCHING_URLpip = ""
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
        # headers = list(doc["osm"]["node"][0].keys())
        for row in doc["osm"]["node"]:
            temp = {k.lstrip("@a"): v for k, v in row.items()}
            # temp["timestamp"] = int(
            #     time.mktime(time.strptime(row["@timestamp"], pattern))
            # )
            node_data.append(temp)
        for row in doc["osm"]["way"]:
            temp = {k.lstrip("@a"): v for k, v in row.items()}
            # temp["timestamp"] = int(
            #     time.mktime(time.strptime(row["@timestamp"], pattern))
            # )
            way_data.append(temp)

    # print(headers)
    # pprint(data)
    return (node_data, way_data)


def preprocess_gps_data() -> list:
    """Preprocess smartphone data for MapMatching
    """
    data = []
    # fields = ["timestamp", "lat", "lon"]
    fields = ["lat", "lon"]
    pattern = "%Y-%m-%dT%H:%M:%SZ"

    with open(GPS_FILE, mode="r") as csv_file:
        reader = csv.DictReader(csv_file, delimiter=",")
        for row in reader:
            temp = {k: v for k, v in row.items() if k in fields}
            # modify epoch to utc datetime
            # temp["timestamp"] = str(
            #     time.strftime(pattern, time.gmtime(int(row["timestamp"][:10])))
            # )
            # data.append({k: v for k, v in row.items() if k in fields})
            data.append(temp)

    # pprint(data)
    return data


def mapbox_display_route(gps_data):
    """Checks gps correctness using Mapboc MapMatching API
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
    for i in range(len(gps_data) // 100):
        st = i * 100
        line["geometry"]["coordinates"] = [
            [float(row["lon"]), float(row["lat"])] for row in gps_data[st : st + 100]
        ]
        resp = map_matcher.match(line, profile="mapbox.driving")
        corr = resp.geojson()["features"][0]
        print(
            i,
            len(corr["geometry"]["coordinates"]),
            len(corr["properties"]["matchedPoints"]),
        )
        corr["geometry"]["coordinates"] = corr["properties"]["matchedPoints"]
        del corr["properties"]["matchedPoints"]
        del corr["properties"]["indices"]
        corrected.append(corr)

        # Display original path on static map
        static_map = Static(access_token=mapbox_access_token)
        response = static_map.image("mapbox.streets", features=line)
        print(response.status_code, response.headers["Content-Type"])
        filename = OUTPUT + "map" + str(i) + ".png"
        with open(filename, "wb") as output:
            _ = output.write(response.content)


if __name__ == "__main__":

    # osm_data = preprocess_osm_data()
    # print(osm_data[0][0])
    # print(osm_data[1][0])

    gps_data = preprocess_gps_data()

    mapbox_display_route(gps_data)

