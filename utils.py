import time
import json
import pickle
import os


def epoch_to_utc(timestamp: str) -> str:
    """Converts epoch to the defined pattern timestamp
    """
    pattern = "%Y-%m-%dT%H:%M:%SZ"
    return str(time.strftime(pattern, time.gmtime(int(timestamp))))


def utc_to_epoch(timestamp: str) -> int:
    """Converts timestamp of a pattern defined to epoch
    """
    pattern = "%Y-%m-%dT%H:%M:%SZ"
    return int(time.mktime(time.strptime(timestamp, pattern)))


def save_map_imgs(output_dir, suffix, data):
    filename = output_dir + "map_" + str(suffix) + "_.png"
    with open(filename, "wb") as output:
        _ = output.write(data)


def save_data(data, filename, obj=False):
    output_dir = os.environ["OUTPUT_DIR"]
    filename = output_dir + filename
    if obj:
        with open(filename, "wb") as outfile:
            pickle.dump(data, outfile)
    else:
        with open(filename, "w") as outfile:
            json.dump(data, outfile, indent=4)

