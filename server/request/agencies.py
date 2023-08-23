"""
This module is responsible for dealing with 3rd part news agencies.
"""
from aiohttp import web as aioweb

from server.request import logger
import server.commons.utils as utils
import server.commons.constants as consts

routes = aioweb.RouteTableDef()


async def initial_setup(app):
    db = app["db"]
    # initializing default agency
    default_agency = {
        "_id": consts.JOURNO_AGENCY_ID,
        "name": "Inbox",
        "description": "Journo News Feed",
        "config": {
            "type": consts.FEED_TYPE_REST_GET,
            "data_format": consts.FEED_DATA_FORMAT_JSON,
            "url": utils.get_request_server_url("stories")
        }
    }

    if not await db.agencies.find_one({"_id": default_agency["_id"]}):
        res = await db.agencies.update_one(
            {"_id": default_agency["_id"]},
            {"$setOnInsert": default_agency},
            upsert=True)
        if not res.upserted_id:
            logger.error("[agencies.initial_setup]: Failed to create default agency to db.")
            return False
    return True


@routes.post("/agencies")
async def create_agency_info(request):
    db = request.app["db"]
    data = await request.json()

    # agency id
    agencyinfo = {}
    if not data.get("id"):
        logger.error("[/agencies] [POST]: Agency 'id' not provided.")
        return utils.get_http_error("Agency 'id' not provided")
    agency_id = data["id"]

    if agency_id == consts.JOURNO_AGENCY_ID:
        logger.error("[/agencies] [POST]: Agency id '{}' is reserved for journo application. Please use different id."
                     .format(consts.JOURNO_AGENCY_ID))
        return utils.get_http_error("Agency id '{}' reserved for journo application. Please use different id."
                                    .format(agency_id))

    # checking if agency id already configured
    if await db.agencies.find_one({"_id": agency_id}):
        logger.error("[/agencies] [ POST]: Agency id '{}' already in use. Please choose different id.".format(agency_id))
        return utils.get_http_error("Agency '{}' already in use. Please choose different id.".format(agency_id))
    agencyinfo["_id"] = agency_id

    # agency name
    if not data.get("name"):
        logger.error("[/agencies] [POST] [{}]: Agency 'name' not provided.".format(agency_id))
        return utils.get_http_error("Agency 'name' not provided")

    # checking if agency name already is being used. This is being checked to avoid display name conflict in UI.
    if await db.agencies.find_one({"name": data["name"]}):
        logger.error("[/agencies] [POST]: Agency name '{}' already in use. Please choose different name."
                     .format(data["name"]))
        return utils.get_http_error("Agency name '{}' already in use. Please choose different name"
                                    .format(data["name"]))
    agencyinfo["name"] = data["name"]

    # validating if proper config is provided or not
    # TODO: Search how news feed works and hook the same configuration settings
    if not data.get("config") or not isinstance(data["config"], dict):
        logger.error("[/agencies] [POST] [{}]: Agency feed configuration not provided.".format(agency_id))
        return utils.get_http_error("Agency feed configuration not provided.")

    feed_config = {}
    # feed type
    if not data["config"].get("type") or \
            data["config"]["type"] not in [consts.FEED_TYPE_RSS, consts.FEED_TYPE_REST_GET]:
        logger.error("[/agencies] [POST] [{}]: Invalid agency feed type provided.".format(agency_id))
        return utils.get_http_error("Invalid agency feed type provided. Only 'rss' and 'rest-get' are supported.")
    feed_config["type"] = data["config"]["type"]

    # feed data format
    if not data["config"].get("data_format") or \
            data["config"]["data_format"] not in [consts.FEED_DATA_FORMAT_XML, consts.FEED_DATA_FORMAT_JSON]:
        logger.error("[/agencies] [POST] [{}]: Invalid agency feed data format type provided.".format(agency_id))
        return utils.get_http_error("Invalid agency feed data format provided. Only 'xml' and 'json' are allowed.")
    feed_config["data_format"] = data["config"]["data_format"]

    # feed url
    if not data["config"].get("url"):
        logger.error("[/agencies] [POST] [{}]: Agency feed url not provided.".format(agency_id))
        return utils.get_http_error("Agency feed url not provided.")
    feed_config["url"] = data["config"]["url"]
    agencyinfo["config"] = feed_config

    # agency status. It tells whether journo is a listening for feed to this news agency or not.
    agencyinfo["status"] = consts.STATE_ACTIVE

    # agency description
    agencyinfo["description"] = data.get("description", "")

    # saving to db
    res = await db.agencies.update_one({"_id": agency_id}, {"$setOnInsert": agencyinfo}, upsert=True)

    # parsing motor response
    if not res.upserted_id:
        if res.matched_count > 0 and res.modified_count == 0:
            logger.error("[/agencies] [POST] [{}]: Agency already exists.".format(agency_id))
            return utils.get_http_error("Agency already exists")

        logger.error("[/agencies] [POST] [{}]: Failed to save to db.".format(agency_id))
        return utils.get_http_error("Server ran into database error", aioweb.HTTPInternalServerError)

    logger.info("[/agencies] [POST] [{}]: New agency '{}' saved successfully.".format(agency_id, agencyinfo))
    return aioweb.json_response({"ok": True, "name": data["name"], "type": feed_config["type"], "url": feed_config["url"],
                                 "data_format": feed_config["url"]})


@routes.put("/agencies/{agency_id}")
async def update_agency_info(request):
    db = request.app["db"]

    data = await request.json()
    agency_id = request.match_info["agency_id"]

    # validating user input
    agencyinfo = {}

    # validating that journo agency id is not being updated
    if agency_id == consts.JOURNO_AGENCY_ID:
        logger.error("[/agencies] [PUT]: Agency '{}' is reserved for journo application. Updating it is not allowed"
                     .format(consts.JOURNO_AGENCY_ID))
        return utils.get_http_error("Agency '{}' reserved for journo application. Updating it is not allowed."
                                    .format(agency_id))
    # agency name
    # checking if agency name already is being used. This is being checked to avoid display name conflict in UI.
    if data.get("name"):
        if await db.agencies.find_one({"name": data["name"]}):
            logger.error("[/agencies] [PUT]: Agency name '{}' already in use. Please choose different name."
                         .format(data["name"]))
            return utils.get_http_error("Agency name '{}' already in use. Please choose different name"
                                        .format(data["name"]))
        agencyinfo["name"] = data["name"]

    # validating if proper config is provided or not
    # TODO: Proper checks and code to handle agency config must be added.
    if "config" in data and isinstance(data["config"], dict):
        feed_config = {}
        if data.get("config"):
            # feed type
            if not data["config"].get("type") or \
                    data["config"]["type"] not in [consts.FEED_TYPE_RSS, consts.FEED_TYPE_REST_GET]:
                logger.error("[/agencies] [PUT] [{}]: Invalid agency feed type provided.".format(agency_id))
                return utils.get_http_error("Invalid agency feed type provided. "
                                            "Only 'rss' and 'rest-get' are supported.")
            feed_config["type"] = data["config"]["type"]

            # feed data format
            if not data["config"].get("data_format") or \
                    data["config"]["data_format"] not in [consts.FEED_DATA_FORMAT_XML, consts.FEED_DATA_FORMAT_JSON]:
                logger.error("[/agencies] [PUT] [{}]: Invalid agency feed data format type provided.".format(agency_id))
                return utils.get_http_error("Invalid agency feed data format provided. "
                                            "Only 'xml' and 'json' are allowed.")
            feed_config["data_format"] = data["config"]["data_format"]

            # feed url
            if not data["config"].get("url"):
                logger.error("[/agencies] [PUT] [{}]: Agency feed url not provided.".format(agency_id))
                return utils.get_http_error("Agency feed url not provided.")
            feed_config["url"] = data["config"]["url"]
        agencyinfo["config"] = feed_config

    # agency status. Agency with id 'journofeed' status must not be set to 'disabled'.
    if data.get("status") and data["status"] in [consts.STATE_ACTIVE, consts.STATE_DISABLED]:
        agencyinfo["status"] = data["status"]

    # description
    agencyinfo["description"] = data.get("description", "")

    # updating to db
    res = await db.agencies.update_one({"_id": agency_id}, {"$set": agencyinfo})

    # parsing motor response
    if not res.raw_result["updatedExisting"]:
        if res.matched_count == 0:
            logger.error("[/agencies] [PUT] [{}]: Requested agency not found.".format(agency_id))
            return utils.get_http_error("Requested agency not found")

        logger.error("[/agencies] [PUT] [{}]: Failed to save to db.".format(agency_id))
        return utils.get_http_error("Server ran into database error", aioweb.HTTPInternalServerError)

    logger.info("[/agencies] [PUT] [{}]: Agency info '{}' updated successfully.".format(agency_id, agencyinfo))
    return aioweb.json_response({"ok": True})


@routes.get("/agencies")
async def get_all_agencies(request):
    db = request.app["db"]
    search_filter = request.rel_url.query

    query = {}
    # preparing search query
    # status
    if search_filter.get("status") and search_filter["status"] in [consts.STATE_ACTIVE, consts.STATE_DISABLED]:
        query["status"] = search_filter["status"]

    # agency id
    if search_filter.get("id"):
        query["_id"] = search_filter["id"]

    # retrieving information from db
    agencies = []
    async for agency in db.agencies.find(query):
        agencies.append(agency)
    return aioweb.json_response({"agencies": agencies})


@routes.get("/agencies/{agency_id}")
async def get_agency_info(request):
    db = request.app["db"]

    agencyinfo = None
    agency_id = request.match_info["agency_id"]
    if agency_id:
        agencyinfo = await db.agencies.find_one({"_id": agency_id})
    return aioweb.json_response(agencyinfo if agencyinfo else None)


@routes.delete("/agencies/{agency_id}")
async def delete_agency_info(request):
    db = request.app["db"]

    agency_id = request.match_info["agency_id"]
    if agency_id == consts.JOURNO_AGENCY_ID:
        logger.error("[/agencies] [DELETE]: Agency '{}' is reserved for journo application. Deleting it is not allowed"
                     .format(consts.JOURNO_AGENCY_ID))
        return utils.get_http_error("Agency '{}' reserved for journo application. Deleting it is not allowed."
                                    .format(agency_id))
    if agency_id:
        # deleting from db
        res = await db.agencies.delete_one({"_id": agency_id})

        # parsing motor response
        if res.deleted_count > 0:
            logger.info("[/agencies] [DELETE]: Agency '{}' deleted.".format(agency_id))
            return aioweb.json_response({"ok": True})

    logger.error("[/agencies] [DELETE]: Failed to delete agency '{}'.".format(agency_id))
    return aioweb.json_response({"ok": False})