"""
 This module is responsible for configuring nrcs & publishing data to nrcs
"""

import asyncio
import json

from aiohttp import web as aioweb

# importing logger
from server.request import logger

import server.commons.constants as consts
import server.commons.utils as utils

from server.commons import session

from collections import defaultdict

# shares all rest api routes are added to this table
routes = aioweb.RouteTableDef()

# ################ Routes ################
@routes.get('/nrcs')
async def get_nrcs_list(request):
    """
    Fetches the NRCS list
    :param request:
    :return: list of configured nrcs clients
    """
    db = request.app["db"]
    # retrieving information from db
    nrcs_list = []
    async for nrcs in db.nrcs.find():
        nrcs_list.append(nrcs)
    return aioweb.json_response({"nrcs": nrcs_list})


@routes.get("/nrcs/{nrcs_id}")
async def get_nrcs_info(request):
    """
    Given a specific nrcss id fetchs it
    :param request:
    :return:
    """
    db = request.app["db"]
    nrcsinfo = None
    nrcs_id = request.match_info["nrcs_id"]
    if nrcs_id:
        nrcsinfo = await db.nrcs.find_one({"_id": nrcs_id})
    return aioweb.json_response(nrcsinfo if nrcsinfo else None)


@routes.post("/nrcs")
async def create_nrcs_config(request):
    """
    Create an nrcs config .
    :param request:
    :return:
    """
    db = request.app["db"]
    data = await request.json()

    # nrcs id
    nrcsinfo = {}
    if not data.get("id"):
        logger.error("[/nrcs] [POST]: NRCS 'id' not provided.")
        return utils.get_http_error("NRCS 'id' not provided")
    nrcs_id = data["id"]

    # checking if nrcs id already configured
    if await db.nrcs.find_one({"_id": nrcs_id}):
        logger.error("[/nrcs] [ POST]: NRCS id '{}' already in use. Please choose different id.".format(nrcs_id))
        return utils.get_http_error("NRCS '{}' already in use. Please choose different id.".format(nrcs_id))
    nrcsinfo["_id"] = nrcs_id

    # nrcs name
    if not data.get("name"):
        logger.error("[/nrcs] [POST] [{}]: NRCS 'name' not provided.".format(nrcs_id))
        return utils.get_http_error("NRCS 'name' not provided")

    # checking if nrcs name already is being used. This is being checked to avoid display name conflict in UI.
    if await db.nrcs.find_one({"name": data["name"]}):
        logger.error("[/nrcs] [POST]: NRCS name '{}' already in use. Please choose different name."
                     .format(data["name"]))
        return utils.get_http_error("NRCS name '{}' already in use. Please choose different name."
                                    .format(data["name"]))
    nrcsinfo["name"] = data["name"]

    # data format
    if not data.get("data_format"):
        logger.error("[/nrcs] [POST] [{}]: NRCS 'data_format' not provided.".format(nrcs_id))
        return utils.get_http_error("NRCS 'data_format' not provided")
    nrcsinfo["data_format"] = data["data_format"]

    # protocol
    if not data.get("protocol"):
        logger.error("[/nrcs] [POST] [{}]: NRCS 'protocol' not provided.".format(nrcs_id))
        return utils.get_http_error("NRCS 'protocol' not provided")
    nrcsinfo["protocol"] = data["protocol"]

    if nrcsinfo["protocol"] == "post":
        nrcsinfo["credentials"] = {}
        credentials = data.get("credentials", {})
        if not credentials.get("url"):
            logger.error("[/nrcs] [POST] [{}]: NRCS 'url' not provided.".format(nrcs_id))
            return utils.get_http_error("NRCS 'url' not provided")
        nrcsinfo["credentials"]["url"] = credentials["url"]
    elif nrcsinfo["protocol"] == "upload":
        nrcsinfo["credentials"] = {}
        credentials = data.get("credentials", {})
        if not credentials.get("ip"):
            logger.error("[/nrcs] [POST] [{}]: NRCS 'ip' not provided.".format(nrcs_id))
            return utils.get_http_error("NRCS 'ip' not provided")
        nrcsinfo["credentials"]["ip"] = credentials["ip"]
        if not credentials.get("port"):
            logger.error("[/nrcs] [POST] [{}]: NRCS 'port' not provided.".format(nrcs_id))
            return utils.get_http_error("NRCS 'port' not provided")
        nrcsinfo["credentials"]["port"] = credentials["port"]
        if not credentials.get("username"):
            logger.error("[/nrcs] [POST] [{}]: NRCS 'username' not provided.".format(nrcs_id))
            return utils.get_http_error("NRCS 'username' not provided")
        nrcsinfo["credentials"]["username"] = credentials["username"]
        if not credentials.get("password"):
            logger.error("[/nrcs] [POST] [{}]: NRCS 'password' not provided.".format(nrcs_id))
            return utils.get_http_error("NRCS 'password' not provided")
        nrcsinfo["credentials"]["password"] = credentials["password"]
        if not credentials.get("offset_path"):
            logger.error("[/nrcs] [POST] [{}]: NRCS 'offset_path' not provided.".format(nrcs_id))
            return utils.get_http_error("NRCS 'offset_path' not provided")
        nrcsinfo["credentials"]["offset_path"] = credentials["offset_path"]
    else:
        logger.error("[/nrcs] [POST] [{}]: Invalid 'protocol'.".format(nrcs_id))
        return utils.get_http_error("Invalid protocol")

    # saving to db
    res = await db.nrcs.update_one({"_id": nrcs_id}, {"$setOnInsert": nrcsinfo}, upsert=True)

    # parsing motor response

    if not res.upserted_id:
        if res.matched_count > 0 and res.modified_count == 0:
            logger.error("[/nrcs] [POST] [{}]: NRCS already exists.".format(nrcs_id))
            return utils.get_http_error("NRCS already exists")

        logger.error("[/nrcs] [POST] [{}]: Failed to save to db.".format(nrcs_id))
        return utils.get_http_error("Server ran into database error", aioweb.HTTPInternalServerError)

    logger.info("[/nrcs] [POST] [{}]: New nrcs '{}' saved successfully.".format(nrcs_id, nrcsinfo))
    nrcsinfo["_id"] = nrcs_id
    nrcsinfo["ok"] = True
    return aioweb.json_response(nrcsinfo)


@routes.put("/nrcs/{nrcs_id}")
async def update_nrcs_config_info(request):
    db = request.app["db"]

    data = await request.json()
    # validating user input
    nrcsinfo = {}
    nrcs_id = request.match_info.get("nrcs_id")

    db_data = await db.nrcs.find_one({"_id": nrcs_id})
    if not db_data:
        logger.error("[/nrcs] [PUT]: Requested nrcs not found for the id '{}'."
                     .format(nrcs_id))
        return utils.get_http_error("Requested nrcs not found for the id '{}'."
                                    .format(nrcs_id))

    if data.get("name"):
        if await db.nrcs.find_one({"name": data["name"], "_id": {"$ne": nrcs_id}}):
            logger.error("[/nrcs] [PUT]: NRCS name '{}' already in use. Please choose different name."
                         .format(data["name"]))
            return utils.get_http_error("NRCS name '{}' already in use. Please choose different name"
                                        .format(data["name"]))
        nrcsinfo["name"] = data["name"]

    if data.get("data_format"):
        nrcsinfo["data_format"] = data["data_format"]

    nrcsinfo["protocol"] = db_data.get("protocol")
    if data.get("protocol"):
        nrcsinfo["protocol"] = data["protocol"]

    credentials = data.get("credentials", {})
    db_data_credentials = db_data.get("credentials", {})
    nrcsinfo["credentials"] = {}
    if nrcsinfo["protocol"] == "post":
        if credentials.get("url"):
            nrcsinfo["credentials"]["url"] = credentials["url"]
        elif db_data_credentials.get("url"):
            nrcsinfo["credentials"]["url"] = db_data_credentials["url"]
        else:
            logger.error("[/nrcs] [POST] [{}]: NRCS 'url' not provided.".format(nrcs_id))
            return utils.get_http_error("NRCS 'url' not provided")
    elif nrcsinfo["protocol"] == "upload":
        if credentials.get("ip"):
            nrcsinfo["credentials"]["ip"] = credentials["ip"]
        elif db_data_credentials.get("ip"):
            nrcsinfo["credentials"]["ip"] = db_data_credentials["ip"]
        else:
            logger.error("[/nrcs] [POST] [{}]: NRCS 'ip' not provided.".format(nrcs_id))
            return utils.get_http_error("NRCS 'ip' not provided")
        if credentials.get("port"):
            nrcsinfo["credentials"]["port"] = credentials["port"]
        elif db_data_credentials.get("port"):
            nrcsinfo["credentials"]["port"] = db_data_credentials["port"]
        else:
            logger.error("[/nrcs] [POST] [{}]: NRCS 'port' not provided.".format(nrcs_id))
            return utils.get_http_error("NRCS 'port' not provided")
        if credentials.get("username"):
            nrcsinfo["credentials"]["username"] = credentials["username"]
        elif db_data_credentials.get("username"):
            nrcsinfo["credentials"]["username"] = db_data_credentials["username"]
        else:
            logger.error("[/nrcs] [POST] [{}]: NRCS 'username' not provided.".format(nrcs_id))
            return utils.get_http_error("NRCS 'username' not provided")
        if credentials.get("password"):
            nrcsinfo["credentials"]["password"] = credentials["password"]
        elif db_data_credentials.get("password"):
            nrcsinfo["credentials"]["password"] = db_data_credentials["password"]
        else:
            logger.error("[/nrcs] [POST] [{}]: NRCS 'password' not provided.".format(nrcs_id))
            return utils.get_http_error("NRCS 'password' not provided")
        if credentials.get("offset_path"):
            nrcsinfo["credentials"]["offset_path"] = credentials["offset_path"]
        elif db_data_credentials.get("offset_path"):
            nrcsinfo["credentials"]["offset_path"] = db_data_credentials["offset_path"]
        else:
            logger.error("[/nrcs] [POST] [{}]: NRCS 'offset_path' not provided.".format(nrcs_id))
            return utils.get_http_error("NRCS 'offset_path' not provided")
    else:
        logger.error("[/nrcs] [PUT]: NRCS name '{}' already in use. Please choose different name."
                     .format(data["name"]))
        return utils.get_http_error("NRCS name '{}' already in use. Please choose different name."
                                    .format(data["name"]))

    # updating to db
    res = await db.nrcs.update_one({"_id": nrcs_id}, {"$set": nrcsinfo})

    # parsing motor response
    if not res.raw_result["updatedExisting"]:
        if res.matched_count == 0:
            logger.error("[/nrcs] [PUT] [{}]: Requested nrcs not found.".format(nrcs_id))
            return utils.get_http_error("Requested nrcs not found")

        logger.error("[/nrcs] [PUT] [{}]: Failed to save to db.".format(nrcs_id))
        return utils.get_http_error("Server ran into database error", aioweb.HTTPInternalServerError)

    logger.info("[/nrcs] [PUT] [{}]: NRCS info '{}' updated successfully.".format(nrcs_id, nrcsinfo))
    return aioweb.json_response({"ok": True})


@routes.delete("/nrcs/{nrcs_id}")
async def delete_nrcs_config(request):
    db = request.app["db"]

    nrcs_id = request.match_info.get("nrcs_id")
    if nrcs_id:
        # deleting from db
        res = await db.nrcs.delete_one({"_id": nrcs_id})

        # parsing motor response
        if res.deleted_count > 0:
            logger.info("[/nrcs] [DELETE]: NRCS '{}' deleted.".format(nrcs_id))
            return aioweb.json_response({"ok": True})

    logger.error("[/nrcs] [DELETE]: Failed to delete nrcs '{}'.".format(nrcs_id))
    return aioweb.json_response({"ok": False})


############################# publish to NRCS ##################################

@routes.post("/story/publish")
async def publish_story(request):
    db = request.app["db"]
    data = await request.json()

    nrcs_id = data.get("nrcs_id")
    if not nrcs_id:
        logger.error("[/story/publish] [POST] : nrcs_id not provided.")
        return utils.get_http_error("nrcs_id not provided.")

    if not await db.nrcs.find_one({"_id": nrcs_id}):
        logger.error("[/story/publish] [POST] {}: nrcs_info not found in db.".format(nrcs_id))
        return utils.get_http_error("nrcs_info not found in db.")

    story_id = data.get("story_id")
    if not story_id:
        logger.error("[/story/publish] [POST] : story_id not provided.")
        return utils.get_http_error("story_id not provided.")

    story_info = await db.stories.find_one({"_id": story_id})
    if not story_info:
        logger.error("[/story/publish] [POST] {}: story_info not found in db.".format(story_id))
        return utils.get_http_error("story_info not found in db.")

    if "_id" in story_info:
        del story_info["_id"]
    story_info["nrcs_id"] = nrcs_id
    story_info["story_id"] = story_id

    url = "http://localhost:7800/story/publish/editorapp"

    resp = await session.post(url, data=json.dumps(story_info))

    if resp.status is 200 and (await resp.json()).get("ok"):
        res = await db.stories.update_one({"_id": story_id}, {"$set": {"sent_to_editors":True}})
        if not res.raw_result["updatedExisting"]:
            if res.matched_count == 0:
                logger.error("[/story/publish] [POST] [{}]: Requested story not found, hence cannot update sent_to_editors status.".format(story_id))
                return utils.get_http_error("Requested story not found, hence cannot update sent_to_editors status.")

            logger.error("[/story/publish] [POST] [{}]: Failed to update sent_to_editors status.".format(story_id))
            return utils.get_http_error("Failed to update sent_to_editors status", aioweb.HTTPInternalServerError)

        logger.info("[/story/publish] [POST] [{}]: story status updated successfully.".format(nrcs_id))
        return aioweb.json_response({"ok": True})
    else:
        logger.error("[/story/publish] [POST] [{}]: Failed to publish to editorapp.".format(nrcs_id))
        return utils.get_http_error("Failed to publish to editorapp.")


#############################################################################

