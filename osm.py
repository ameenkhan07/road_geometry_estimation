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
        self.node_data = {}
        self.way_data = {}
        self.relation_data = []
        self.node_fields = ["@id", "@timestamp", "@lat", "@lon", "tag"]
        self.way_fields = ["@id", "@timestamp", "nd", "tag"]
        self.fields = ["@lat", "@lon", "@id", "nd"]
        self.node_tags = set()
        self.way_tags = set()
        self.highway_nodes = set()
        self.node_way_mapping = defaultdict(list)
        self._process_osm_data()

    def _process_osm_data(self) -> dict:
        """Process the OSM file data to the model
        """
        print("Creating OSM DATA MODEL ...")
        with open(OSM_FILE) as fd:
            doc = xmltodict.parse(fd.read())
            self._format_node_data(doc["osm"]["node"])
            self._format_way_data(doc["osm"]["way"])
            self._format_relation_data(doc["osm"]["relation"])
        self.set_node_way_mapping()
        self.set_highway_node_mapping()

        print("OSM DATA MODEL Created !!!")

    def _format_node_data(self, node_data):
        """Formats the "NODE" element of OSM
        """
        for row in node_data:
            temp = {k.lstrip("@a"): v for k, v in row.items() if k in self.node_fields}
            temp["timestamp"] = utc_to_epoch(row["@timestamp"])
            temp["lat"], temp["lon"] = float(temp["lat"]), float(temp["lon"])
            if "tag" in temp:
                if isinstance(temp["tag"], list):
                    temp["tag"] = {t["@k"]: t["@v"] for t in temp["tag"]}
                if isinstance(temp["tag"], OrderedDict):
                    temp["tag"] = {temp["tag"]["@k"]: temp["tag"]["@v"]}
            self.node_data[temp["id"]] = temp

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
            self.way_data[temp["id"]] = temp

    def _format_relation_data(self, relation_data):
        """Formats the "NODE" element of OSM
        """
        for row in relation_data:
            temp = {k.lstrip("@a"): v for k, v in row.items()}
            self.relation_data.append(temp)

    def set_node_way_mapping(self):
        """Generates a node_id->way_id mapping, where a node_id can
        belong to multiple way_id
        Return: None, stores the mapping to the data model
        """
        for way_id, way_value in self.way_data.items():
            for n_id in way_value["node_id"]:
                self.node_way_mapping[n_id].append(way_id)

    def set_highway_node_mapping(self):
        """Create a set of nodes belonging to drivable highways
            https://wiki.openstreetmap.org/wiki/Key:highway
        """
        exclude_highway_types = [
            "pedestrian",
            "track",
            "footway",
            "bridleway",
            "steps",
            "path",
            "elevator",
            "cycleway",
        ]
        for way_id, way_value in self.way_data.items():
            if (
                "tag" in way_value.keys()
                and "highway" in way_value["tag"].keys()
                and way_value["tag"]["highway"] not in exclude_highway_types
            ):
                self.highway_nodes.update(way_value["node_id"])


if __name__ == "__main__":

    osm = OSM_DATA_MODEL()

    pprint({k: osm.node_data[k] for k in list(osm.node_data.keys())[:10]})
    pprint({k: osm.way_data[k] for k in list(osm.way_data.keys())[:10]})
    pprint(len(list(osm.node_way_mapping.keys())))
    pprint(len(osm.highway_nodes))
    save_data(list(osm.highway_nodes), "highway_nodes.json")
