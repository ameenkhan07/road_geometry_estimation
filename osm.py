import xmltodict
from utils import *
from collections import *

OSM_FILE = "./data/map.osm"


class OSM_DATA_MODEL:
    def __init__(self):
        self.node_data = []
        self.way_data = []
        self.node_fields = ["@id", "@timestamp", "@lat", "@lon", "tag"]
        self.way_fields = ["@id", "@timestamp", "nd", "tag"]
        self.fields = ["@lat", "@lon", "@id", "nd"]
        self.node_tags = set()
        self.way_tags = set()
        self._preprocess_osm_data()

    def _format_node_data(self, node_data):
        """
        """
        for row in node_data:
            temp = {k.lstrip("@a"): v for k, v in row.items() if k in self.node_fields}
            temp["timestamp"] = utc_to_epoch(row["@timestamp"])
            if "tag" in temp:
                if isinstance(temp["tag"], list):
                    temp["tag"] = {t["@k"]: t["@v"] for t in temp["tag"]}
                if isinstance(temp["tag"], OrderedDict):
                    temp["tag"] = {temp["tag"]["@k"]: temp["tag"]["@v"]}
            self.node_data.append(temp)

    def _format_way_data(self, way_data):
        """
        """
        for row in way_data:
            temp = {k.lstrip("@a"): v for k, v in row.items() if k in self.way_fields}
            temp["timestamp"] = utc_to_epoch(row["@timestamp"])
            if "nd" in temp.keys():
                if isinstance(temp["nd"], list):
                    temp["node_id"] = [n["@ref"] for n in temp["nd"]]
                    del temp["nd"]
            if "tag" in temp.keys():
                if isinstance(temp["tag"], list):
                    temp["tag"] = {t["@k"]: t["@v"] for t in temp["tag"]}
                    self.way_tags.update(temp["tag"].keys())
            self.way_data.append(temp)

    def _preprocess_osm_data(self) -> dict:
        """Preprocess OSM data for MapMatching
        Data manually downloaded from OSM site:
            https://wiki.openstreetmap.org/wiki/Downloading_data
        """

        headers = []

        with open(OSM_FILE) as fd:
            doc = xmltodict.parse(fd.read())
            node_headers = list(doc["osm"]["node"][0].keys())
            ways_headers = list(doc["osm"]["way"][0].keys())
            self._format_node_data(doc["osm"]["node"])
            self._format_way_data(doc["osm"]["way"])


if __name__ == "__main__":

    osm = OSM_DATA_MODEL()
    # pprint(osm.node_data[:100])
    pprint(osm.way_data[:10])
    # print(osm.way_tags)
