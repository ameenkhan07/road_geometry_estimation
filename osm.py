import xmltodict
from collections import *
from pprint import pprint
from utils import *

OSM_FILE = "./data/map.osm"


class OSM_DATA_MODEL:
    """The data model for the downloaded osm file.
    Data manually downloaded from OSM site:
            https://wiki.openstreetmap.org/wiki/Downloading_data
    """

    def __init__(self):
        self.node_data = []
        self.way_data = []
        self.node_fields = ["@id", "@timestamp", "@lat", "@lon", "tag"]
        self.way_fields = ["@id", "@timestamp", "nd", "tag"]
        self.fields = ["@lat", "@lon", "@id", "nd"]
        self.node_tags = set()
        self.way_tags = set()
        self.node_way_mapping = defaultdict(list)
        self._process_osm_data()

    def _process_osm_data(self) -> dict:
        """Process the OSM file data to the model
        """

        headers = []

        with open(OSM_FILE) as fd:
            doc = xmltodict.parse(fd.read())
            self._format_node_data(doc["osm"]["node"])
            self._format_way_data(doc["osm"]["way"])

    def _format_node_data(self, node_data):
        """Formats the "NODE" element of OSM
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
        """Formats the "WAY" element of OSM
        """
        for row in way_data:
            temp = {k.lstrip("@a"): v for k, v in row.items() if k in self.way_fields}
            temp["timestamp"] = utc_to_epoch(row["@timestamp"])
            if "nd" in temp.keys():
                temp["node_id"] = [n["@ref"] for n in temp["nd"]]
                del temp["nd"]
            if "tag" in temp.keys():
                if isinstance(temp["tag"], list):
                    temp["tag"] = {t["@k"]: t["@v"] for t in temp["tag"]}
                if isinstance(temp["tag"], OrderedDict):
                    temp["tag"] = {temp["tag"]["@k"]: temp["tag"]["@v"]}
                self.way_tags.update(temp["tag"].keys())
            self.way_data.append(temp)

    def set_node_way_mapping(self):
        """Generates a node_id->way_id mapping
        Return: None, stores the mapping to the data model
        """
        for way in self.way_data:
            for n_id in way["node_id"]:
                self.node_way_mapping[n_id].append(way["id"])



if __name__ == "__main__":

    osm = OSM_DATA_MODEL()
    # pprint(osm.node_data[:10])
    # pprint(sm.way_data[:10])
    osm.set_node_way_mapping()
