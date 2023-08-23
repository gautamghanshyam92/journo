"""
This module is responsible for all task related operations
"""

import json
import datetime
from aiohttp import web as aioweb

# importing logger
from server.request import logger
from server.commons import session

import server.commons.constants as consts
import server.commons.utils as utils


async def get_story_info(story_id):
    url = utils.get_request_server_url("stories/{}".format(story_id))
    resp = await session.get(url)
    return await resp.json() if resp.status is 200 else None


async def send_command_to_taskserver(taskinfo):
    url = utils.get_task_server_url("tasks")
    resp = await session.post(url, data=json.dumps(taskinfo))
    return await resp.json() if resp.status is 200 else None


async def send_proxy_path_to_reqserver(asset_id, proxyinfo):
    url = utils.get_request_server_url("stories-assets/{}".format(asset_id))
    resp = await session.put(url, data=json.dumps(proxyinfo))
    return await resp.json() if resp.status is 200 else None

# ------------------ API's to manage tasks ------------------

routes = aioweb.RouteTableDef()


@routes.post("/tasks")
async def create_new_task(request):
    db = request.app["db"]
    data = await request.json()

    # validating user input and preparing data
    task_id = utils.generate_random_id()
    taskinfo = {}
    task_name = data.get("task_name")
    if task_name in [consts.TASK_UPLOAD, consts.TASK_DOWNLOAD]:
        # preparing task
        story_id = data.get("story_id", None)
        storyinfo = await get_story_info(story_id)
        if story_id is None or not storyinfo:
            logger.error("[/tasks] [POST] [story_id({})]: invalid story_id provided.".format(story_id))
            return utils.get_http_error("Requested story not found")

        # story_id
        taskinfo["story_id"] = story_id

        # file_name
        if not data.get("file_name"):
            logger.error("[/tasks] [POST] [story_id({})]: file_name not provided.".format(story_id))
            return utils.get_http_error("Filename not provided.")
        taskinfo["file_name"] = data["file_name"]

        # file_size
        if not data.get("file_size"):
            logger.error("[/tasks] [POST] [story_id({})]: file_size not provided.".format(story_id))
            return utils.get_http_error("Filesize not provided.")
        taskinfo["file_size"] = data["file_size"]

        # share_id
        if not data.get("share_id"):
            logger.error("[/tasks] [POST] [story_id({})]: share_id not provided.".format(story_id))
            return utils.get_http_error("share_id not provided")
        taskinfo["share_id"] = data["share_id"]

        # media_path
        if not data.get("media_path"):
            logger.error("[/tasks] [POST] [story_id({})]: media_path not provided.".format(story_id))
            return utils.get_http_error("Destination path not provided.")
        taskinfo["media_path"] = data["media_path"]

        # asset_id
        asset_id = data.get("asset_id")
        if not asset_id:
            asset_id = consts.ASSET_ID_FORMAT.format(story_id=story_id, filename=data["file_name"])
        taskinfo["asset_id"] = asset_id

        # task_id
        #task_id = utils.generate_hex_id(story_id, task_name, asset_id, data["media_path"])
        taskinfo["task_id"] = task_id

    elif task_name in [consts.TASK_GENERATE_LOWRES, consts.TASK_GENERATE_THUMBNAIL]:
        asset_id = data.get("asset_id")
        if not asset_id:
            logger.error("[/tasks] [POST]: asset_id not provided.")
            return utils.get_http_error("asset id not provided")
        taskinfo["asset_id"] = asset_id

        # share_id
        if not data.get("share_id"):
            logger.error("[/tasks] [POST] [asset_id({})]: share_id not provided.".format(asset_id))
            return utils.get_http_error("share_id not provided")
        taskinfo["share_id"] = data["share_id"]

        # proxy_share_id
        if not data.get("proxy_share_id"):
            logger.error("[/tasks] [POST] [asset_id({})]: proxy_share_id not provided.".format(asset_id))
            return utils.get_http_error("proxy_share_id not provided")
        taskinfo["proxy_share_id"] = data["proxy_share_id"]

        # media_path
        if not data.get("path"):
            logger.error("[/tasks] [POST] [asset_id({})]: media path not provided.".format(asset_id))
            return utils.get_http_error("media path not provided")
        taskinfo["media_path"] = data["path"]

        # task_id and proxy file path
        if task_name == consts.TASK_GENERATE_LOWRES:
            if not data.get("lowres_path"):
                logger.error("[/tasks] [POST] [asset_id({})]: lowres_path not provided.".format(asset_id))
                return utils.get_http_error("Lowres path not provided")
            taskinfo["lowres_path"] = data["lowres_path"]

            #task_id = utils.generate_hex_id(asset_id, task_name, data["lowres_path"])

        elif task_name == consts.TASK_GENERATE_THUMBNAIL:
            if not data.get("thumbnail_path"):
                logger.error("[/tasks] [POST] [asset_id({})]: thumbnail_path not provided.".format(asset_id))
                return utils.get_http_error("Thumbnail path not provided")
            taskinfo["thumbnail_path"] = data["thumbnail_path"]

            #task_id = utils.generate_hex_id(asset_id, task_name, data["thumbnail_path"])

        taskinfo["task_id"] = task_id
        taskinfo["task_name"] = task_name

        # sending proxy command to taskserver
        resp = await send_command_to_taskserver(taskinfo)
        if not resp or not resp.get("ok"):
            logger.error("[/tasks] [POST] [asset_id({})]: Failed to post proxy task '{}' to TaskServer.".format(asset_id, taskinfo))
            return utils.get_http_error("failed to submit proxy task to TaskServer")

    if taskinfo and task_id and task_name:

        dt_ = datetime.datetime.now()
        task = {
            "_id": task_id,
            "task_name": task_name,
            "status": consts.STATE_NEW,
            "progress": 0,
            "bandwidth": 0,
            "created_datetime": dt_.strftime(consts.DATETIME_FORMAT),
            "created_date": dt_.strftime(consts.DATE_FORMAT),
            "updated_datetime": dt_.strftime(consts.DATETIME_FORMAT),
            "data": taskinfo
        }

        # saving to db
        res = await db.tasks.update_one({"_id": task_id}, {"$setOnInsert": task}, upsert=True)

        # parsing motor response
        if not res.upserted_id:
            if res.matched_count > 0 and res.modified_count == 0:
                logger.error("[/tasks] [POST] [{}]: Task already exists.".format(task_id))
                return utils.get_http_error("Task already exists")

            logger.error("[/tasks] [POST] [{}]: Failed to save task to db.".format(task_id))
            return utils.get_http_error("Server ran into database error", httperror=aioweb.HTTPInternalServerError)

        logger.info("[/tasks] [POST] [story_id({})]: New task '{}' created successfully.".format(task_id, task))
        return aioweb.json_response({"task_id": task_id, "ok": True})
    
    logger.error("[/tasks] [POST]: Not enough command parameters provided to create a task.")
    return utils.get_http_error("Not enough parameters provided to create task")


@routes.put("/tasks-status/{task_id}")
async def update_task_status(request):
    db = request.app["db"]
    data = await request.json()

    # task_id
    task_id = request.match_info["task_id"]
    if not task_id:
        logger.error("[/tasks-status] [PUT]: task_id not provided.")
        return utils.get_http_error("task_id not provided.")

    if not data.get("task_name"):
        logger.error("[/tasks-status] [PUT] [{}]: task_name not provided.".format(task_id))
        return utils.get_http_error("task_name not provided")

    # db filter query and update info
    updateinfo = {}
    query = {"_id": task_id, "task_name": data["task_name"], "status": {"$nin": [consts.STATE_COMPLETED]}}

    # progress info
    if not data.get("status"):
        logger.error("[/tasks-status] [PUT] [{}]: task status not provided.".format(task_id))
        return utils.get_http_error("task status not provided.")

    updateinfo["status"] = data["status"]
    if data.get("progress"):
        updateinfo["progress"] = data["progress"]
    if data.get("bandwidth"):
        updateinfo["bandwidth"] = data["bandwidth"]

    # task specific info
    if data["task_name"] in [consts.TASK_UPLOAD, consts.TASK_DOWNLOAD]:
        pass

    elif data["task_name"] in [consts.TASK_GENERATE_LOWRES, consts.TASK_GENERATE_THUMBNAIL]:
        if data["status"] == consts.STATE_COMPLETED:
            taskinfo = await db.tasks.find_one({"_id": task_id})
            if not taskinfo:
                logger.error("[/tasks-status] [PUT] [{}]: '{}' task details not found in db hence failed to update asset with proxy path."
                    .format(task_id, data["task_name"]))
                return aioweb.json_response({"ok": False})

            # syncing generated lowres or thumbnail path to asset
            proxyinfo = {"asset_id": taskinfo["data"].get("asset_id")}
            if data["task_name"] == consts.TASK_GENERATE_LOWRES:
                proxyinfo["lowres_path"] = taskinfo["data"]["lowres_path"]

            elif data["task_name"] == consts.TASK_GENERATE_THUMBNAIL:
                proxyinfo["thumbnail_path"] = taskinfo["data"]["thumbnail_path"]

            resp = await send_proxy_path_to_reqserver(proxyinfo["asset_id"], proxyinfo)
            if not resp or not resp["ok"]:
                logger.error("[/tasks-status] [PUT] [{}]: Request Server failed to save asset '{}' proxy '{}' information."
                    .format(task_id, proxyinfo.get("asset_id"), proxyinfo))
            else:
                logger.info("[/tasks-status] [PUT] [{}]: Proxy info '{}' successfully saved for asset '{}'."
                    .format(task_id, proxyinfo, proxyinfo.get("asset_id")))

    # updating status to db
    if updateinfo:
        # updating status to db
        res = await db.tasks.update_one(query, {"$set": updateinfo})

        # parsing motor response
        if res.raw_result["updatedExisting"]:
            logger.debug("[/tasks-status] [PUT] [{}]: Task status '{}' updated to db successfully.".format(task_id, updateinfo))
            return aioweb.json_response({"ok": True})

    logger.error("[/tasks-status] [PUT] [{}]: Failed update task status '{}' to db.".format(task_id, updateinfo))
    return aioweb.json_response({"ok": False})


@routes.get("/tasks/{task_id}")
async def get_task_info(request):
    db = request.app["db"]

    task_id = request.match_info["task_id"]
    if not task_id:
        return aioweb.json_response(None)

    query = {"_id": task_id}
    taskinfo = await db.tasks.find_one(query)
    return aioweb.json_response(taskinfo if taskinfo else None)


@routes.get("/tasks")
async def get_all_tasks(request):
    db = request.app["db"]

    # search keys to filter result
    if request.rel_url.query.get("search"):
        search_filter = json.loads(request.rel_url.query["search"])
    else:
        search_filter = request.rel_url.query

    # db query
    query = {}

    # Getting search parameters
    # story_id
    if search_filter.get("task_id"):
        query["_id"] = search_filter["task_id"]

    # created_date
    date_str = search_filter.get("created_date")
    if date_str:
        # validating date format
        try:
            datetime.datetime.strptime(date_str, consts.DATE_FORMAT)
        except ValueError:
            logger.error("[/tasks] [GET]: invalid date '{}' format found.".format(date_str))
            return utils.get_http_error("Please provide valid date format.")
        query["created_date"] = date_str

    # task name
    if search_filter.get("task_name"):
        query["task_name"] = search_filter["task_name"]

    # status
    if search_filter.get("status"):
        query["status"] = search_filter["status"]

    # story_id
    if search_filter.get("story_id"):
        query["data.story_id"] = search_filter["story_id"]

    # filename
    if search_filter.get("file_name"):
        query["data.file_name"] = {"$regex": ".*{}.*".format(search_filter["file_name"]), "$options": "i"}

    # retrieving tasks
    tasks = []
    async for task in db.tasks.find(query):
        tasks.append(task)
    return aioweb.json_response({"tasks": tasks})


@routes.delete("/tasks/{task_id}")
async def delete_task(request):
    db = request.app["db"]

    task_id = request.match_info["task_id"]
    if not task_id:
        logger.error("[/tasks] [DELETE]: task_id not provided.")
        return utils.get_http_error("task_id not provided")

    res = await db.tasks.delete_one({"_id": task_id})
    if res.deleted_count > 0:
        logger.info("[/tasks] [DELETE]: Task '{}' deleted.".format(task_id))
        return aioweb.json_response({"ok": True})

    logger.error("[/tasks] [DELETE]: Failed to delete task '{}'.".format(task_id))
    return aioweb.json_response({"ok": False})