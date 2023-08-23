import sys
import asyncio
from aiohttp import web as aioweb
import motor.motor_asyncio as amotor

# importing logger
from server.request import logger

import server.commons.utils as utils

routes = aioweb.RouteTableDef()


@routes.get("/published_stories/{nrcs_id}")
async def get_nrcs_story_details(request):
    db = request.app["db"]
    nrcs_id = request.match_info.get("nrcs_id")
    # retrieving information from db
    story_list = []
    if nrcs_id:
        async for story in db.stories.find({"nrcs_id":nrcs_id}):
            story_list.append(story)
    return aioweb.json_response({"story_list": story_list})


@routes.post("/story/publish/editorapp")
async def publish_story_to_editor_app(request):
    db = request.app["db"]
    data = await request.json()
    nrcs_id = data.get("nrcs_id")
    story_id = data.get("story_id", None)

    if not nrcs_id:
        logger.error("[/story/publish/editorapp] [POST] : nrcs_id not provided.")
        return utils.get_http_error("nrcs_id not provided.")

    if not story_id:
        logger.error("[/story/publish/editorapp] [POST] : story_id not provided.")
        return utils.get_http_error("story_id not provided.")

    data["nrcs_id"] = nrcs_id

    # saving to db
    res = await db.stories.update_one({"_id": nrcs_id, "story_id": story_id}, {"$setOnInsert": data}, upsert=True)

    # parsing motor response

    if not res.upserted_id:
        if res.matched_count > 0 and res.modified_count == 0:
            logger.error("[/story/publish/editorapp] [POST] : Story with nrcs_id '{}' and story_id '{}' already exists.".format(nrcs_id, story_id))
            return utils.get_http_error("Story already exists.")

        logger.error("[/story/publish/editorapp] [POST]: Failed to save to db (nrcs_id '{}' and story_id '{}')".format(nrcs_id, story_id))
        return utils.get_http_error("Failed to save to db")

    logger.info("[/story/publish/editorapp] [POST] [{}]: New story '{}' saved successfully.".format(nrcs_id, data))
    return aioweb.json_response({"ok": True})


async def setup_simulator_app(webapp):
    # initializing db
    client = amotor.AsyncIOMotorClient()
    db = client['simulator']
    webapp["db"] = db
    logger.info("[Main] [Setup]: News editor simulator database setup is done.")
    webapp.add_routes(routes)
    logger.info("[Main] [Setup]: News editor simulator application setup done.")
    return True

if __name__ == "__main__":
    # main event loop
    loop = asyncio.get_event_loop()

    # web app
    app = aioweb.Application()

    # setting up db and adding to app
    client = amotor.AsyncIOMotorClient()

    status = loop.run_until_complete(setup_simulator_app(app))
    if not status:
        logger.error("[Main]: Failed to setup news editor simulator application. Hence terminating.")
        sys.exit(1)

    # starting app
    aioweb.run_app(app, host="localhost", port=7800)
