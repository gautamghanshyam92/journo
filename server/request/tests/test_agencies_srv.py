import sys
import json
import requests
import logging

logging.basicConfig(level=logging.DEBUG, format="%(name)s %(message)s", stream=sys.stderr)

agency_url = "http://localhost:7799/agencies"

count = 0
agency_1 = {
    "_id": None,
    "name": None,
    "description": "Test News Feed",
    "config": {}
}


def create_new(data):
    global count
    logger = logging.getLogger("POST")
    logger.info("Testing post request.")

    # preparing data
    while True:
        agency_id = "test_agency{}".format(count)
        info = requests.get(agency_url+"/{}".format(agency_id))
        if info:
            count += 1
        break

    agency_id = "test_agency{}".format(count)
    agency_name = "Test Agency{}".format(count)

    data["_id"] = agency_id
    data["name"] = agency_name

    # sending post request
    resp = requests.post(agency_url, data=json.dumps(data))
    resp = resp.json()

    # validating response
    if resp.status_code == 200 and resp["ok"]:
        logger.info("New agency created successfully.")
        return True

    logger.error("Failed to create new agency.")
