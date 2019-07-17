import json
import os
from pprint import pprint
import csv
import requests
from utils import *
from osm import OSM_DATA_MODEL
from mapbox import MapMatcher, Static
import geopy

CONFIG = "config.json"
GPS_FILE = "./data/gps.txt"
OUTPUT = "./outputs/"
# GRAPHHOPPER_MAP_MATCHING_URL = https://graphhopper.com/api/1/match?vehicle


def set_access_token() -> str:
    """Return access token from file
    """
    with open(CONFIG) as config_file:
        data = json.load(config_file)
        os.environ["MAPBOX_ACCESS_TOKEN"] = data["mapbox_token"]


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


def map_match_mapbox(gps_data):
    """
    """
    MAPBOX_API = "https://api.mapbox.com/matching/v5/mapbox/driving"
    params = {"access_token": os.environ["MAPBOX_ACCESS_TOKEN"]}
    batch_size = len(gps_data) // 100
    map_matched = []
    for i in range(batch_size + 1):
        st = i * 100
        payload = {
            "coordinates": ";".join(
                [str(row["lon"] + "," + row["lat"]) for row in gps_data[st : st + 100]]
            )
        }
        resp = requests.request("POST", MAPBOX_API, data=payload, params=params)
        resp = resp.json()
        corr = []
        map_matched.extend([tp["location"] for tp in resp["tracepoints"]])
    save_data(OUTPUT, map_matched, "corrected.json")


def map_match_mapbox_v4(gps_data):
    """Checks gps correctness using Mapbox MapMatching API
    https://docs.mapbox.com/api/legacy/map-matching-v4/
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
        # pprint(corr)
        corrected.extend(corr["geometry"]["coordinates"])

        # Plot points on Static Map
        # generate_mapbox_static_maps(corr, i)

    save_data(OUTPUT, corrected, "corrected_v4.json")
    return corrected


def _format_map_matched_data():
    """
    """
    pass


if __name__ == "__main__":

    set_access_token()
    osm_data = OSM_DATA_MODEL()

    gps_data = preprocess_gps_data()
    # matched_gp_data = map_match_mapbox_v4(gps_data)
    matched_gps_data = map_match_mapbox(gps_data)

    # gps_set(corrected)
