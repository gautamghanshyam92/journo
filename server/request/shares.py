"""
This module is responsible for handling all storage related operations.
"""

import json
from aiohttp import web as aioweb
import datetime

# importing logger
from server.request import logger

import server.commons.constants as consts
import server.commons.utils as utils

# shares all rest api routes are added to this table
routes = aioweb.RouteTableDef()

@routes.post("/shares")
async def create_share_entry(request):
    db = request.app["db"]
    shareinfo = {}

    data = await request.json()

    # validating user input
    share_id = data.get("share_id")
    if not share_id:
        logger.error("[/shares] [POST]: Share id not provided.")
        return utils.get_http_error("Share id not provided")

    # checking if share already exists
    if await db.shares.find_one({"_id": share_id}):
        logger.error("[/shares] [POST] [{}]: Share id already in use.".format(share_id))
        return utils.get_http_error("Share id already in use")

    # validating data
    for key in ["name", "protocols"]:
        if not data.get(key):
            logger.error("[/shares] [POST] [{}]: {} not provided.".format(share_id, key))
            return utils.get_http_error("{} not provided".format(key))
        shareinfo[key] = data[key]

    if not data.get("type") or (data["type"] not in [consts.SHARE_TYPE_FILE, consts.SHARE_TYPE_PROXY]):
        logger.error("[/shares] POST [{}]: invalid share type '{}' provided.".format(share_id, data["type"]))
        return utils.get_http_error("Unknown share type provided")
    shareinfo["type"] = data["type"]

    if set(shareinfo["protocols"]) != set(data.get("paths", {}).keys()):
        logger.error("[/shares] POST [{}]: Inconsistency between protocols & paths : {} --> {}.".format(
                                                            share_id,
                                                            shareinfo['protocols'],
                                                            data.get('paths')))
        return utils.get_http_error("Inconsistent share protocols and paths provided")

    creds_validated = False
    shareinfo['paths'] = {}
    for proto, share in data["paths"].items():
        if not isinstance(share, dict) or not share.get('protocol'):
            logger.error("[/shares] [POST [{}] Invalid share provided. {}".format(share_id, share))
            return utils.get_http_error("Invalid share provided data.")

        if share["protocol"] == consts.PROTOCOL_FTP:
            for key in ["ip", "port", "username", "password", "path"]:
                if not share.get(key):
                    logger.error("[/shares] [POST] [{}]: share '{}' not provided.".format(share_id, key))
                    return utils.get_http_error("Share '{}' not provided".format(key))
            creds_validated = True

        elif share["protocol"] == consts.PROTOCOL_SMB:
            for key in ["ip", "username", "password", "path"]:
                if not share.get(key):
                    logger.error("[/shares] [POST] [{}]: share '{}' not provided.".format(share_id, key))
                    return utils.get_http_error("Share '{}' not provided".format(key))
            creds_validated = True

        elif share["protocol"] == consts.PROTOCOL_FILE:
            if not share.get("path"):
                logger.error("[/shares] [POST [{}]: share 'path' not provided.")
                return utils.get_http_error("Share 'path' not provided")
            creds_validated = True

        elif share["protocol"] == consts.PROTOCOL_TUS:
            for key in ["ip", "port", "path"]:
                if not share.get(key):
                    logger.error("[/shares] [POST] [{}]: share '{}' not provided.".format(share_id, key))
                    return utils.get_http_error("Share '{}' not provided".format(key))
            creds_validated = True

        else:
            logger.error("[/shares] [POST : [{}] : share invalid protocol '{}' provided."
                         .format(share_id, share["protocol"]))
            return utils.get_http_error("Invalid share protocol provided : {}".format(share["protocol"]))

        shareinfo["paths"][proto] = share

    if not creds_validated:
        logger.error("[/shares] [POST [{}]: insufficient credentials to access share provided.".format(share_id))
        return utils.get_http_error("Insufficient credentials to access share provided")

    shareinfo["state"] = data.get('state', consts.STATE_ACTIVE)
    shareinfo["created_time"] = datetime.datetime.now().strftime(consts.DATETIME_FORMAT)

    # saving to db
    res = await db.shares.update_one({"_id": share_id}, {"$setOnInsert": shareinfo}, upsert=True)

    # parsing motor response
    if not res.upserted_id:
        if res.matched_count > 0 and res.modified_count == 0:
            logger.error("[/shares] [POST] [{}]: Share already exists.".format(share_id))
            return utils.get_http_error("Share already exists")

        logger.error("[/shares] [POST [{}]: Failed to save to db.".format(share_id))
        return utils.get_http_error("Server ran into database error", httperror=aioweb.HTTPInternalServerError)

    logger.info("[/shares] [POST] [{}]: New share '{}' added to database.".format(share_id, shareinfo))
    shareinfo["_id"] = share_id
    shareinfo["ok"] = True
    return aioweb.json_response(shareinfo)


@routes.get("/shares/{share_id}")
async def get_share_details(request):
    db = request.app["db"]

    share_id = request.match_info["share_id"]
    if not share_id:
        return aioweb.json_response(None)

    query = {"_id": share_id}
    shareinfo = await db.shares.find_one(query)
    return aioweb.json_response(shareinfo if shareinfo else None)


@routes.get("/shares")
async def get_all_share_details(request):
    db = request.app["db"]

    query = {}
    # search keys to filter result
    if request.rel_url.query.get("search"):
        search_filter = json.loads(request.rel_url.query["search"])
    else:
        search_filter = request.rel_url.query

    if search_filter.get("share_id"):
        query["_id"] = search_filter["share_id"]

    if search_filter.get("protocols"):
        query["protocols"] = search_filter["protocols"]

    if search_filter.get("type"):
        query["type"] = search_filter["type"]

    if search_filter.get("state") and search_filter["state"] in [consts.STATE_ACTIVE, consts.STATE_DISABLED]:
        query["state"] = search_filter["state"]

    shares = []
    async for share in db.shares.find(query):
        shares.append(share)
    return aioweb.json_response({"shares": shares})


@routes.delete("/shares/{share_id}")
async def delete_share_entry(request):
    db = request.app["db"]
    share_id = request.match_info["share_id"]
    if not share_id:
        logger.error("[/shares] [DELETE]: share_id not provided.")
        return aioweb.json_response(None)

    res = await db.shares.delete_one({'_id': share_id})
    if res.deleted_count > 0:
        logger.info("[/shares] [DELETE]: share '{}' deleted.".format(share_id))
        return aioweb.json_response({"ok": True})

    logger.error("[/shares] [DELETE]: Failed to delete share '{}'.".format(share_id))
    return aioweb.json_response({"ok": False})


@routes.put("/shares/{share_id}")
async def update_share_details(request):
    db = request.app["db"]
    shareinfo = {}

    data = await request.json()

    # validating user input
    share_id = request.match_info["share_id"]
    if not share_id:
        logger.error("[/shares] [PUT]: Share id not provided.")
        return utils.get_http_error("Share id not provided.")

    # checking if share exists
    dbshare = await db.shares.find_one({"_id": share_id})
    if not dbshare:
        logger.error("[/shares] [PUT] [{}]: Share not found in db.".format(share_id))
        return utils.get_http_error("Share not found.")

    if data.get("name"):
        shareinfo["name"] = data["name"]

    if 'protocols' in data:
        if 'paths' not in data:
            logger.error("[/shares] PUT [{}]: Share paths not provided.".format(share_id))
            return utils.get_http_error("Share paths not provided")

        if set(data["protocols"]) != set(data["paths"].keys()):
            logger.error("[/shares] PUT [{}]: Inconsistency between protocols & paths : {} --> {}.".format(
                                                            share_id, data['protocols'], data['paths']))
            return utils.get_http_error("Inconsistent share protocols and paths provided")

        shareinfo['protocols'] = data['protocols']
        shareinfo['paths'] = {}
        for proto, share in data['paths'].items():
            if not isinstance(share, dict) or not share.get('protocol'):
                logger.error("[/shares] [PUT [{}] Invalid share provided. {}".format(share_id, share))
                return utils.get_http_error("Invalid share data provided.")

            if share["protocol"] == consts.PROTOCOL_FTP:
                for key in ["ip", "port", "username", "password", "path"]:
                    if not share.get(key):
                        logger.error("[/shares] [PUT] [{}]: share '{}' not provided.".format(share_id, key))
                        return utils.get_http_error("Share '{}' not provided".format(key))

            elif share["protocol"] == consts.PROTOCOL_SMB:
                for key in ["ip", "username", "password", "path"]:
                    if not share.get(key):
                        logger.error("[/shares] [PUT [{}]: share '{}' not provided.".format(share_id, key))
                        return utils.get_http_error("Share '{}' not provided".format(key))

            elif share["protocol"] == consts.PROTOCOL_FILE:
                if not share.get("path"):
                    logger.error("[/shares] [PUT] [{}]: share 'path' not provided.")
                    return utils.get_http_error("Share 'path' not provided")

            elif share["protocol"] == consts.PROTOCOL_TUS:
                for key in ["ip", "port", "path"]:
                    if not share.get(key):
                        logger.error("[/shares] [PUT [{}]: share '{}' not provided.".format(share_id, key))
                        return utils.get_http_error("Share '{}' not provided".format(key))

            else:
                logger.error("[/shares] [PUT : [{}] : share invalid protocol '{}' provided."
                             .format(share_id, share["protocol"]))
                return utils.get_http_error("Invalid share protocol provided : {}".format(share["protocol"]))

            shareinfo["paths"][proto] = share

    if data.get("state") in [consts.STATE_ACTIVE, consts.STATE_DISABLED]:
        shareinfo["state"] = data["state"]

    # saving to db
    res = await db.shares.update_one({"_id": share_id}, {"$set": shareinfo})

    # parsing motor response
    if not res.raw_result["updatedExisting"]:
        if res.matched_count == 0:
            logger.error("[/shares] [PUT] [{}]: Requested share not found.".format(share_id))
            return utils.get_http_error("Requested share not found")

        logger.error("[/shares] [PUT [{}]: Failed to save to db.".format(share_id))
        return utils.get_http_error("Server ran into database error", aioweb.HTTPInternalServerError)

    logger.info("[/shares] [PUT] [{}]: Share details '{}' updated to database.".format(share_id, shareinfo.keys()))
    return aioweb.json_response({"ok": True})

