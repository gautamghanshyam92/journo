"""
This module is responsible for handling all story related tasks
"""

import os
import math
import json
import datetime
import pymongo
from aiohttp import web as aioweb

# importing logger
from server.request import logger
from server.commons import session
import server.commons.constants as consts
import server.commons.utils as utils

# set this to true to automatically create tags
AUTOMATICALLY_CREATE_TAGS = False
TEXT_INDEX_ENABLED = False

# default directory in which all story files should be uploaded. NOTE: It should be created before upload starts.
DEFAULT_UPLOAD_DIRECTORY = "storyclips"

# Maximum number of stories to send on each get request
STORIES_PAGE_SIZE = 10


def generate_story_id(title, user_id, date_str):
    return utils.generate_hex_id(title, user_id, date_str)


# retrieving information using rest api
async def create_tag_with_name(tagname):
    url = utils.get_request_server_url("tags")
    resp = await session.post(url, data=json.dumps({"name": tagname}))
    return await resp.json() if resp.status is 200 else None


async def get_category_info(category_id):
    url = utils.get_request_server_url("categories/{}".format(category_id))
    resp = await session.get(url)
    return await resp.json() if resp.status is 200 else None


async def get_tag_info(tag_id):
    url = utils.get_request_server_url("tags/{}".format(tag_id))
    resp = await session.get(url)
    return await resp.json() if resp.status is 200 else None


async def get_user_info(user_id):
    url = utils.get_request_server_url("users/{}".format(user_id))
    resp = await session.get(url)
    return await resp.json() if resp.status is 200 else None


async def get_share_info(share_id):
    url = utils.get_request_server_url("shares/{}".format(share_id))
    resp = await session.get(url)
    return await resp.json() if resp.status is 200 else None


async def get_story_proxy_shares(share_filter):
    share_filter["type"] = consts.SHARE_TYPE_PROXY
    url = utils.get_request_server_url("shares?search={}".format(json.dumps(share_filter)))
    resp = await session.get(url)
    return await resp.json() if resp.status is 200 else None


async def get_story_shares(share_filter):
    share_filter["type"] = consts.SHARE_TYPE_FILE
    url = utils.get_request_server_url("shares?search={}".format(json.dumps(share_filter)))
    resp = await session.get(url)
    return await resp.json() if resp.status is 200 else None


async def get_recent_version(story_id):
    """
    Get the recent version for a story id
    :param story_id: Story id
    :return: Recent version of the story or None
    """
    url = utils.get_request_server_url('version/recent/{}'.format(story_id))
    resp = await session.get(url)
    if resp.status == 200:
        resp_data = await resp.json()
        return resp_data.get('recent_version', {})
    return None


async def get_version_history(story_id, skip=0):
    """
    Get the version history of a  story id
    :param story_id: Story Id being requested for
    :param skip: No of versions to skip, if pagination is applied
    :return: the next list of version histimport server.commons.utils as utilsory to be served
    """
    url = utils.get_request_server_url('version/history/{}/{}'.format(story_id, skip))
    resp = await session.get(url)
    return await resp.json() if resp.status == 200 else None


async def create_version(story_id, version_data):
    """
    Create  a version using the version_data and the story id
    :param story_id: Story id for the version
    :param version_info: Version Data, Data to be versioned (story_title, userid, description)
    :return: True if successful version creation else False
    """
    status = False
    url = utils.get_request_server_url('version')
    version_info = {}
    version_info['story_id'] = story_id
    version_info['version_data'] = version_data
    version_resp = await session.post(url, data=json.dumps(version_info))
    if version_resp.status == 200:
        status = True
    return status


async def get_specific_story(story_id):
    """
    Gets the story given a story id
    :param story_id: Story_id
    :return: Story data containing the versioned details.
    """
    url = utils.get_request_server_url('stories/{}'.format(story_id))
    story_resp = await session.get(url)
    return await story_resp.json() if story_resp.status == 200 else None


async def get_story_thumbnail_path(media_path, proxy_share_id=None):
    if proxy_share_id is None:
        # finding proxy base directory
        proxyshares = await get_story_proxy_shares({"protocol": consts.PROTOCOL_FILE})
        if not proxyshares or not proxyshares.get("shares"):
            logger.error("[get_story_thumbnail_path]: No proxy share found to store story thumbnail.")
            return utils.get_http_error("No proxy share configured.")

        proxyshares = proxyshares["shares"]
        # TODO: Update proxy share selection logic. Currently it saves to first proxy share in retrieved list
        proxy_share_id = proxyshares[0]["_id"]

    proxy_dir_uri = consts.SHARE_URI_PREFIX + proxy_share_id

    # thumbnail filename
    thumbnail_file = "{}.thumbnail.{}".format(os.path.basename(media_path), consts.STORY_THUMBNAIL_EXTENSION)

    # thumbnail path
    return os.path.join(proxy_dir_uri, thumbnail_file), proxy_share_id


async def get_story_lowres_path(media_path, proxy_share_id=None):
    if proxy_share_id is None:
        # finding proxy base directory
        proxyshares = await get_story_proxy_shares({"protocol": consts.PROTOCOL_FILE})
        if not proxyshares or not proxyshares.get("shares"):
            logger.error("[get_story_lowres_path]: No proxy share found to store story lowres.")
            return utils.get_http_error("No proxy share configured.")

        proxyshares = proxyshares["shares"]
        # TODO: Update proxy share selection logic. Currently it saves to first proxy share in retrieved list
        proxy_share_id = proxyshares[0]["_id"]

    proxy_dir_uri = consts.SHARE_URI_PREFIX + proxy_share_id

    # lowres filename
    lowres_file = "{}.lowres.{}".format(os.path.basename(media_path), consts.STORY_LOWRES_EXTENSION)

    # lowres path
    return os.path.join(proxy_dir_uri, lowres_file), proxy_share_id


async def submit_story_thumbnail_task(assetinfo, story_id):
    try:
        task = dict(asset_id=assetinfo["asset_id"], share_id=assetinfo["share_id"], path=assetinfo["path"])

        # preparing thumbnail task
        task["task_name"] = consts.TASK_GENERATE_THUMBNAIL
        task["thumbnail_path"], task["proxy_share_id"] = await get_story_thumbnail_path(task["path"])

        # posting thumbnail task
        url = utils.get_request_server_url("tasks")
        resp = await session.post(url, data=json.dumps(task))
        if resp.status is not 200:
            logger.error("[submit_story_thumbnail_task]: Failed to post Generate Thumbnail Task for story '{}'."
                         .format(story_id))
            return False

        resp = await resp.json()
        if not resp["ok"]:
            logger.error("[submit_story_thumbnail_task]: Request Server failed to create thumbnail task for story '{}'."
                         .format(story_id))
            return False
        return True
    except Exception as ex:
        logger.error("[submit_story_thumbnail_task]: Failed to send GenerateThumbnail Task to TaskServer. Error: '{}'"
                     .format(ex))
    return False


async def submit_story_proxy_tasks(assetinfo, story_id):
    task = dict(asset_id=assetinfo["asset_id"], share_id=assetinfo["share_id"], path=assetinfo["path"])

    # preparing thumbnail task
    task["task_name"] = consts.TASK_GENERATE_THUMBNAIL
    task["thumbnail_path"], task["proxy_share_id"] = await get_story_thumbnail_path(task["path"])

    # posting thumbnail task
    url = utils.get_request_server_url("tasks")
    resp = await session.post(url, data=json.dumps(task))
    if resp.status is not 200:
        logger.error("[submit_story_proxy_tasks]: Failed to post Generate Thumbnail Task for story '{}'."
                     .format(story_id))
        return False

    resp = await resp.json()
    if not resp["ok"]:
        logger.error("[submit_story_proxy_tasks]: Request Server failed to create thumbnail task for story '{}'."
                     .format(story_id))
        return False

    # removing thumbnail_path
    del task["thumbnail_path"]

    # preparing lowres task
    task["task_name"] = consts.TASK_GENERATE_LOWRES
    task["lowres_path"], _ = await get_story_lowres_path(task["path"], task["proxy_share_id"])

    # posting task
    url = utils.get_request_server_url("tasks")
    resp = await session.post(url, data=json.dumps(task))
    if resp.status is not 200:
        logger.error("[submit_story_proxy_tasks]: Failed to post Generate Lowres Task for story '{}'.".format(story_id))
        return False

    resp = await resp.json()
    if not resp["ok"]:
        logger.error("[submit_story_proxy_tasks]: Request Server failed to create lowres task for story '{}'."
                     .format(story_id))
        return False

    logger.info("[submit_story_proxy_tasks]: Generate Thumbnail and Lowres tasks posted successfully for story '{}'."
                .format(story_id))
    return True


def prepare_proxy_url(lowres_path=None, thumbnail_path=None):
    """
     Prepare the lowres and thumbnail urls considering nginx
    """
    proxy_url = {}
    if lowres_path:
        proxy_url['lowres_url'] = utils.generate_proxy_url(lowres_path)
    if thumbnail_path:
        proxy_url['thumbnail_url'] = utils.generate_proxy_url(thumbnail_path)
    return proxy_url
# ------------------ Web Routes ------------------

routes = aioweb.RouteTableDef()

# ----------------- story resource ----------------------
@routes.post("/stories")
async def create_new_story(request):
    # db instance
    db = request.app["db"]
    data = await request.json()

    # new story data
    story = {}
    # Version Data
    # Version contains story_title, user_id, description
    version_data = {}
    # validating story

    # story_title - must
    story_title = data.get("story_title")
    if not story_title:
        logger.error("[/stories] [POST]: invalid story title '{}' provided.".format(story_title))
        return utils.get_http_error("Story title must be provided")

    version_data["story_title"] = story_title

    # user_id - must
    user_id = data.get("user_id")
    if not user_id or not await get_user_info(user_id):
        logger.error("[/stories] [POST]: invalid user; given user_id '{}' not found in db for story '{}'."
                     .format(user_id, story_title))
        return utils.get_http_error("User not found. Please re-login and retry.")

    version_data["user_id"] = user_id

    #
    # NOTE: Story id is used to identify a story uniquely. According to current logic story id is generated using
    #   alphanumeric characters from story_title, user_id, today's date. This means for one day two stories with same
    #   story_title cannot be added to db
    #
    today_date_time = datetime.datetime.now()
    story_id = generate_story_id(story_title, user_id, today_date_time.strftime(consts.DATE_FORMAT))
    if await db.stories.find_one({"_id": story_id}):
        logger.error("[/stories] [POST]: Story with same title '{}' already created for the today.".format(story_title))
        return utils.get_http_error("Story with same title already created. Please choose different story title.")

    # category_id
    category_id = data.get("category_id")
    if category_id:
        if not await get_category_info(category_id):
            logger.error("[/stories] [POST] [{}]: category_id '{}' not found in db.".format(story_id, category_id))
            return utils.get_http_error("Selected category not found. Please re-login and retry.")
        story["category_id"] = category_id

    # agency_id
    story["agency_id"] = data.get("agency_id", consts.JOURNO_AGENCY_ID)

    # story timestamp
    story["created_datetime"] = data.get("created_datetime", today_date_time.strftime(consts.DATETIME_FORMAT))
    created_datetime_obj = datetime.datetime.strptime(story["created_datetime"], consts.DATETIME_FORMAT)
    story["created_date"] = created_datetime_obj.strftime(consts.DATE_FORMAT)
    story["updated_datetime"] = today_date_time.strftime(consts.DATETIME_FORMAT)

    if data.get("incident_date", None):
        try:
            datetime.datetime.strptime(data["incident_date"], consts.DATE_FORMAT)
            story["incident_date"] = data["incident_date"]
        except ValueError:
            logger.error("[/stories] [POST] [{}]: invalid incident date format provided.".format(story_id))
            return utils.get_http_error("Invalid incident date format found")

    if data.get("incident_time", None):
        try:
            datetime.datetime.strptime(data["incident_time"], consts.TIME_FORMAT)
            story["incident_time"] = data["incident_time"]
        except ValueError:
            logger.error("[/stories] [POST] [{}]: invalid incident time format provided.".format(story_id))
            return utils.get_http_error("Invalid incident time format found")

    # description 
    version_data["description"] = data.get("description", "")

    # tags
    story["tags"] = data.get("tags", [])

    # link
    story["link"] = data.get("link", None)

    # new tags
    if AUTOMATICALLY_CREATE_TAGS:
        for tagname in data.get("new_tags", []):
            resp = await create_tag_with_name(tagname)
            if not resp or not resp["ok"]:
                logger.error("[/stories] [POST] [{}]: Failed to create tag '{}'. Creating story without this tag."
                             .format(story_id, tagname))
                continue
            story["tags"].append(resp["_id"])
    else:
        story["new_tags"] = data.get("new_tags")

    # attached assets
    attachments = []
    story["attachments"] = []
    for file_name in data.get("attachments", []):
        asset_id = consts.ASSET_ID_FORMAT.format(story_id=story_id, filename=file_name)
        story["attachments"].append(asset_id)
        # preparing asset details for response
        attachments.append({
            "asset_id": asset_id,
            "file_name": file_name,
            "state": consts.FILE_STATE_PENDING
        })

    # story status
    story["review_status"] = dict(reviewed=False, reviewed_by=None)
    story["sent_to_editors"] = False
    story["archived"] = False

    # creating an version entry before the actual story entry is created
    version_resp = await create_version(story_id, version_data)
    if not version_resp:
        logger.error("[/stories] [POST] [{}]: Could not create version.".format(story_id))
        return utils.get_http_error("Version Could not be created")

    # saving to db
    res = await db.stories.update_one({"_id": story_id}, {"$setOnInsert": story}, upsert=True)
    # parsing motor response
    if not res.upserted_id:
        if res.matched_count > 0 and res.modified_count == 0:
            logger.error("[/stories] [POST] [{}]: Story already exists.".format(story_id))
            return utils.get_http_error("Story already exists")

        logger.error("[/stories] [POST] [{}]: Failed to save to db.".format(story_id))
        return utils.get_http_error("Server ran into database error", httperror=aioweb.HTTPInternalServerError)

    await utils.push_feed(msg='story-created', data=await get_specific_story(story_id))
    logger.info("[/stories] [POST] [{}]: Story '{}' saved successfully.".format(story_id, story))
    return aioweb.json_response({"story_id": story_id, "attachments": attachments, "ok": True})


@routes.get("/stories/{story_id}")
async def get_story_details(request):
    db = request.app["db"]

    story_id = request.match_info["story_id"]
    if not story_id:
        logger.error("[/stories] [GET]: story_id not provided.")
        return utils.get_http_error("Story id not provided")

    storyinfo = await db.stories.find_one({"_id": story_id})
    if storyinfo:
        # updating category info
        storyinfo["category_info"] = await get_category_info(storyinfo["category_id"])
        del storyinfo["category_id"]

        version_info = await get_recent_version(story_id)
        if version_info and version_info.get("version_data"):
            storyinfo["version_time"] = version_info["version_time"]
            for vkey in consts.VERSIONING_KEYS:
                storyinfo[vkey] = version_info['version_data'].get(vkey)

        # Adding the previous versions to the story info
        storyinfo['versions'] = []
        version_history = await get_version_history(story_id)
        if version_history and version_history.get("version_history", []):
            if len(version_history['version_history']) > 1:
                storyinfo["versions"] = version_history['version_history'][1:]

        # updating tags info
        tags_info_list = []
        for tag_id in storyinfo.get("tags", []):
            tags_info_list.append(await get_tag_info(tag_id))

        storyinfo["tags_info_list"] = tags_info_list
        if "tags" in storyinfo:
            del storyinfo["tags"]
        logger.info("Storyinfo is : {}".format(storyinfo))
        # updating user info
        _user_info = await get_user_info(storyinfo["user_id"])
        storyinfo["user_info"] = {"_id": _user_info["_id"], "display_name": _user_info["display_name"]}
        del storyinfo["user_id"]

        # updating reviewer info
        if storyinfo["review_status"]["reviewed_by"] is not None:
            _reviewer_info = await get_user_info(storyinfo["review_status"]["reviewed_by"])
            storyinfo["review_status"]["reviewer_info"] = {"_id": _reviewer_info["_id"],
                                                           "display_name": _reviewer_info["display_name"]}

        attachments = []
        for asset_id in storyinfo["attachments"]:
            assetinfo = await db.assets.find_one(
                {"_id": asset_id},
                {"file_name": 1,
                 "file_size": 1,
                "type": 1,
                "path": 1,
                "created_date": 1,
                "thumbnail_path": 1, "lowres_path": 1}
            )

            if not assetinfo:
                assetinfo = dict(state=consts.FILE_STATE_PENDING)
                assetinfo["file_name"] = asset_id.split(storyinfo["_id"]+"__", 1)[-1]
            else:
                assetinfo["state"] = consts.FILE_STATE_READY
                proxy_url = prepare_proxy_url(assetinfo.get("lowres_path"), assetinfo.get("thumbnail_path"))
                assetinfo.update(proxy_url)
            assetinfo["asset_id"] = asset_id
            attachments.append(assetinfo)
        storyinfo["attachments"] = attachments
    return aioweb.json_response(storyinfo if storyinfo else None)



@routes.get("/stories")
async def get_all_stories(request):
    # db instance
    db = request.app["db"]

    # search keys to filter result
    if request.rel_url.query.get("search"):
        search_filter = json.loads(request.rel_url.query["search"])
    else:
        search_filter = request.rel_url.query

    logger.info("[/stories] [GET]: search_filter '{}'".format(search_filter))
    # db query
    query = {}

    # page number
    page_number = 1
    if search_filter.get("page_number"):
        try:
            page_number = int(search_filter["page_number"])
        except ValueError:
            logger.error("[/stories] [GET]: invalid page_number type. page_number must be of int type hence "
                         "skipping pagination.")

    # Getting search parameters
    # story_id
    if search_filter.get("story_id", None):
        query["_id"] = search_filter["story_id"]

    # user_id
    user_id = search_filter.get("user_id", None)
    if user_id:
        if not await get_user_info(user_id):
            logger.error("[/stories] [GET]: user_id '{}' not found in db.".format(user_id))
            return utils.get_http_error("User not identified")
        query["user_id"] = user_id

    # agency id
    query["agency_id"] = {"$regex" : "^{}$".format(search_filter.get("agency_id", consts.JOURNO_AGENCY_ID )),
                          "$options": '-i' }

    # created_date
    date_str = search_filter.get("created_date", None)
    if date_str:
        # validating date format
        try:
            datetime.datetime.strptime(date_str, consts.DATE_FORMAT)
            query["created_date"] = date_str
        except ValueError:
            logger.error("[/stories] [GET]: invalid created date '{}' format found hence skipping filter."
                         .format(date_str))

    # incident date
    incident_date_str = search_filter.get("incident_date", None)
    if incident_date_str:
        # validating date format
        try:
            datetime.datetime.strptime(incident_date_str, consts.DATE_FORMAT)
            query["incident_date"] = incident_date_str
        except ValueError:
            logger.error("[/stories] [GET]: Invalid incident date '{}' format found.".format(date_str))

    # category_id
    if search_filter.get("category_id", None):
        query["category_id"] = search_filter["category_id"]

    # tag_ids
    tags = []
    if search_filter.get("tag_ids"):
        if isinstance(search_filter["tag_ids"], list):
            for tag in search_filter["tag_ids"]:
                if not isinstance(tag, str):
                    continue
                tags.append(tag)

        elif isinstance(search_filter["tag_ids"], str):
            tags.extend(search_filter["tag_ids"].split(","))

    if tags:
        query["tags"] = {"$in": tags}

    # search by story status
    # review status
    if "reviewed" in search_filter:
        value = None
        if isinstance(search_filter["reviewed"], bool):
            value = search_filter["reviewed"]
        elif isinstance(search_filter["reviewed"], str) and search_filter["reviewed"] in ['true', 'false']:
            value = True if search_filter["reviewed"] == 'true' else False
        if value is not None:
            query["review_status.reviewed"] = value
    # reviewed by
    if search_filter.get("reviewed_by") and await get_user_info(search_filter["reviewed_by"]):
        query["review_status.reviewed_by"] = search_filter["reviewed_by"]
    # archived
    if "archived" in search_filter:
        value = None
        if isinstance(search_filter["archived"], bool):
            value = search_filter["archived"]
        elif isinstance(search_filter["archived"], str) and search_filter["archived"] in ['true', 'false']:
            value = True if search_filter["archived"] == 'true' else False
        if value is not None:
            query["archived"] = value

    # text search -- only for title and description
    # For more details on $text search refer link: https://docs.mongodb.com/v3.6/text-search/
    # TODO: Stories 'title' and 'description' field should be programmatically added to 'stories' table text indexes.
    # if search_filter.get("text_search") and TEXT_INDEX_ENABLED:
    #    query["$text"] = {"$search": search_filter["text_search"]}

    # calculating pagination information
    total_stories_count = await db.stories.count_documents(query)
    total_pages = math.ceil(total_stories_count / STORIES_PAGE_SIZE)

    skip_first_n = STORIES_PAGE_SIZE * (page_number - 1)

    # retrieving stories
    stories = []
    if "$text" in query:
        stories_cursor = db.stories.find(query, {"score": {"$meta": "textScore"}})\
            .sort([("score", {"$meta": "textScore"})])
    else:
        stories_cursor = db.stories.find(query).sort([("created_datetime", pymongo.DESCENDING)])

    logger.info("[/stories] [GET]: search query: {}".format(query))

    async for story in stories_cursor.skip(skip_first_n).limit(STORIES_PAGE_SIZE):
        # updating category info
        story["category_info"] = await get_category_info(story["category_id"])
        del story["category_id"]

        version_info = await get_recent_version(story['_id'])
        if version_info and version_info.get('version_data'):
            story['version_time'] = version_info['version_time']
            for vkey in consts.VERSIONING_KEYS:
                story[vkey] = version_info['version_data'].get(vkey)

        # updating tags info
        tags_info_list = []
        for tag_id in story.get("tags", []):
            tags_info_list.append(await get_tag_info(tag_id))

        story["tags_info_list"] = tags_info_list
        if "tags" in story:
            del story["tags"]

        # updating user info
        _user_info = await get_user_info(story["user_id"])
        story["user_info"] = {"_id": _user_info["_id"], "display_name": _user_info["display_name"]}
        del story["user_id"]

        # updating reviewer info
        if story["review_status"]["reviewed_by"] is not None:
            _reviewer_info = await get_user_info(story["review_status"]["reviewed_by"])
            story["review_status"]["reviewer_info"] = {"_id": _reviewer_info["_id"],
                                                       "display_name": _reviewer_info["display_name"]}

        attachments = []
        for asset_id in story["attachments"]:
            assetinfo = await db.assets.find_one({"_id": asset_id})

            if not assetinfo:
                assetinfo = dict(state=consts.FILE_STATE_PENDING)
                assetinfo["file_name"] = asset_id.split(story["_id"]+"__", 1)[-1]
            else:
                assetinfo["state"] = consts.FILE_STATE_READY

            assetinfo["asset_id"] = asset_id
            attachments.append(assetinfo)
        story["attachments"] = attachments
        stories.append(story)

    return aioweb.json_response({"stories": stories, "page_number": page_number, "total_pages": total_pages})


@routes.put("/stories/{story_id}")
async def update_story_entry(request):
    # db instance
    db = request.app["db"]
    # request data
    data = await request.json()

    # changes to update to story
    story = {}

    # TODO: user_id check for authentication and authorization must be added using session details

    # validating story
    # story_id - must
    story_id = request.match_info["story_id"]
    if not story_id:
        logger.error("[/stories] [PUT]: story_id not provided.")
        return utils.get_http_error("Story id not provided")

    storyinfo = await db.stories.find_one({"_id": story_id})
    if not storyinfo:
        logger.error("[/stories] [PUT] [{}]: Story not found in db.".format(story_id))
        return utils.get_http_error("Requested story not found")

    recent_version = await get_recent_version(story_id)
    logger.info("[/stories] [PUT]:Recent version of data is : {}".format(recent_version))
    new_version_data = dict()

    # checking if story is already reviewed verified by input desk person
    if storyinfo["review_status"]["reviewed"]:
        logger.error("[/stories] [PUT] [{}]: Story is reviewed and verified. No more editing is allowed."
                     .format(story_id))
        return utils.get_http_error("Story is reviewed and verified. No more editing allowed")

    # category_id
    category_id = data.get("category_id")
    if category_id:
        if not await get_category_info(category_id):
            logger.error("[/stories] [PUT] [{}]: category_id '{}' not found in db.".format(story_id, category_id))
            return utils.get_http_error("Request category not found. Please re-login and retry")
        story["category_id"] = category_id

    user_id = data.get("user_id")
    if not user_id or not await get_user_info(user_id):
        logger.error("[/stories] [PUT]: invalid user; given user_id '{}' not found in db for story '{}'."
                     .format(user_id, story_id))
        return utils.get_http_error("User not found. Please re-login and retry.")

    # story_title
    if data.get("story_title"):
        new_version_data["story_title"] = data["story_title"]

    # description
    if data.get("description"):
        new_version_data["description"] = data["description"]

    # tags
    if "tags" in data and isinstance(data["tags"], list):
        data["tags"] = list()
        for tag in data["tags"]:
            if not await get_tag_info(tag):
                del data["tags"]
                break
            story["tags"].append(tag)

    # incident date
    if data.get("incident_date"):
        try:
            datetime.datetime.strptime(data["incident_date"], consts.DATE_FORMAT)
            story["incident_date"] = data["incident_date"]
        except ValueError:
            logger.error("[/stories] [PUT] [{}]: invalid incident date format provided.".format(story_id))
            return utils.get_http_error("Invalid incident date format found")

    # incident time
    if data.get("incident_time"):
        try:
            datetime.datetime.strptime(data["incident_time"], consts.TIME_FORMAT)
            story["incident_time"] = data["incident_time"]
        except ValueError:
            logger.error("[/stories] [PUT] [{}]: invalid incident time format provided.".format(story_id))
            return utils.get_http_error("Invalid incident time format found")

    # review status
    if data.get("reviewed"):
        if not data.get("reviewed_by") or not await get_user_info(data["reviewed_by"]):
            logger.error("[/stories] [PUT] [{}]: Invalid reviewer id provided".format(story_id))
            return utils.get_http_error("Invalid reviewer id provided")

        # TODO: mandatory story keys for valid values must be checked before updating review status
        story["review_status.reviewed"] = True
        story["review_status.reviewed_by"] = data["reviewed_by"]

    # attachments
    attachments = []
    if data.get("attachments"):
        story["attachments"] = []
        for file_name in data.get("attachments", []):
            asset_id = consts.ASSET_ID_FORMAT.format(story_id=story_id, filename=file_name)
            story["attachments"].append(asset_id)

            # checking file current state
            file_state = consts.FILE_STATE_PENDING
            if await db.assets.find_one({"_id": asset_id}):
                file_state = consts.FILE_STATE_READY

            # preparing asset details for response
            attachments.append({
                "asset_id": asset_id,
                "file_name": file_name,
                "state": file_state
            })

    if new_version_data.get("description") != recent_version["version_data"].get("description") or \
            new_version_data.get("story_title") != recent_version["version_data"].get("story_title"):
        new_version_data['user_id'] = user_id
        if not await create_version(story_id, new_version_data):
            logger.error("[/stories] [PUT] [{}]: Could not create version.".format(story_id))
            return utils.get_http_error("Version Could not be created")
        if not story:
            resp_data = dict(ok=True, story_id=story_id)
            if attachments:
                resp_data["attachments"] = attachments
            return aioweb.json_response(resp_data)

    if not story:
        logger.error("[/stories] [PUT] [{}]: Cannot update story no changes.".format(story_id))
        return utils.get_http_error("Cannot update story no changes")

    # saving to db
    res = await db.stories.update_one({"_id": story_id}, {"$set": story})

    # parsing motor response
    if not res.raw_result["updatedExisting"]:
        if res.matched_count == 0:
            logger.error("[/stories] [PUT] [{}]: Requested story not found.".format(story_id))
            return utils.get_http_error("Requested story not found")

        logger.error("[/stories] [PUT] [{}]: Failed to save to db.".format(story_id))
        return utils.get_http_error("Server ran into database error", httperror=aioweb.HTTPInternalServerError)
    await utils.push_feed(msg="story-updated", data=await get_specific_story(story_id))
    logger.info("[/stories] [PUT] [{}]: Story '{}' saved successfully.".format(story_id, story))
    resp_data = dict(ok=True, story_id=story_id)
    if attachments:
        resp_data["attachments"] = attachments
    return aioweb.json_response(resp_data)


@routes.get("/stories-shares")
async def get_stories_share_details(request):
    # TODO: Add strategy logic to decide which share should be used to upload story clip
    query = dict(protocols={"$in": [consts.PROTOCOL_FTP, consts.PROTOCOL_TUS]}, state=consts.STATE_ACTIVE)

    search_filter = request.rel_url.query
    if search_filter.get("protocol"):
        query["protocols"] = {"$in": [search_filter["protocol"]]}

    if search_filter.get("share_id"):
        query["_id"] = search_filter["share_id"]

    # fetching storage credentials
    share_credentials = None
    destination_folder = None

    shares = await get_story_shares(query)
    if shares and shares.get("shares"):
        # TODO: Add strategy to decide among storage with same protocol and constraints
        # giving more preference to TUS protocol for upload of bigger files.
        for share in shares["shares"]:
            if consts.PROTOCOL_TUS in share["protocols"]:
                share_credentials = share
                share_credentials.update(share_credentials["paths"][consts.PROTOCOL_TUS])
                share_credentials.pop("paths")

                # location on storage where clip should be uploaded
                # TODO: Add proper strategy to decide at location in storage the file should be uploaded
                destination_folder = os.path.join(share_credentials["path"])
                break

        if not share_credentials:
            share_credentials = shares["shares"][0]
            share_credentials.update(share_credentials["paths"][consts.PROTOCOL_FTP])
            share_credentials.pop("paths")

            # location on storage where clip should be uploaded
            # TODO: Add proper strategy to decide at location in storage the file should be uploaded
            destination_folder = os.path.join(share_credentials["path"], DEFAULT_UPLOAD_DIRECTORY)

    if not share_credentials:
        logger.error("[/stories-shares] [GET]: No share found to store stories assets.")
        return utils.get_http_error("No share configured.")

    share_credentials.pop("protocols")

    return aioweb.json_response({
        "share_credentials": share_credentials,
        "destination_folder": destination_folder
    })


@routes.post("/stories-assets")
async def save_story_file_details(request):
    # TODO: Add mime type for media
    db = request.app["db"]

    data = await request.json()

    # parsing user input and preparing data
    logger.info("[stories-assets] Post data recieved is : {}".format(data))
    assetinfo = {}
    story_id = data.get("story_id")
    if not story_id or not await db.stories.find_one({"_id": story_id}):
        logger.error("[/stories-assets] [POST]: story_id not provided.")
        return utils.get_http_error("Requested story not found")
    assetinfo["story_id"] = story_id

    if not data.get("asset_id"):
        logger.error("[/stories-assets] [POST] [{}]: asset_id not provided.".format(story_id))
        return utils.get_http_error("File information not provided.")
    assetinfo["asset_id"] = data["asset_id"]

    if not data.get("share_id"):
        logger.error("[/stories-assets] [POST] [{}]: share_id not provided.".format(story_id))
        return utils.get_http_error("Share information not provided.")
    assetinfo["share_id"] = data["share_id"]

    if not data.get("path"):
        logger.error("[/stories-assets] [POST] [{}]: path not provided.".format(story_id))
        return utils.get_http_error("Uploaded path information not provided.")
    assetinfo["path"] = data["path"]

    if not data.get("file_name"):
        logger.error("[/stories-assets] [POST] [{}]: file_name not provided.".format(story_id))
        return utils.get_http_error("File name not provided.")
    assetinfo["file_name"] = data["file_name"]

    if not data.get("file_size"):
        logger.error("[/stories-assets] [POST] [{}]: file_size not provided.".format(story_id))
        return utils.get_http_error("File size not provided.")
    # TODO: get file size from file system
    assetinfo["file_size"] = data["file_size"]

    # updating type
    assetinfo["type"] = data.get("type")
    today_date_timestamp = datetime.datetime.now()
    assetinfo["created_date"] = today_date_timestamp.strftime(consts.DATE_FORMAT)
    assetinfo["created_datetime"] = today_date_timestamp.strftime(consts.DATETIME_FORMAT)
    assetinfo["special_flags"] = {}

    # TODO: verify file is uploaded

    # saving to db
    res = await db.assets.update_one({"_id": assetinfo["asset_id"]}, {"$setOnInsert": assetinfo}, upsert=True)

    # parsing motor response
    if not res.upserted_id:
        if res.matched_count > 0 and res.modified_count == 0:
            logger.error("[/stories-assets] [POST] [{}]: Asset '{}' already exists."
                         .format(story_id, assetinfo["asset_id"]))
            return utils.get_http_error("Asset already exists")

        logger.error("[/stories-assets] [POST] [{}]: Failed to save to db.".format(story_id))
        return utils.get_http_error("Server ran into database error", httperror=aioweb.HTTPInternalServerError)

    logger.info("[/stories-assets] [POST] [{}]: New file information '{}' saved to database."
                .format(story_id, assetinfo))

    # posting proxy tasks
    await submit_story_thumbnail_task(assetinfo, story_id)
    return aioweb.json_response({"ok": True})


@routes.post("/stories-proxy")
async def request_story_proxy_creation(request):
    db = request.app["db"]

    data = await request.json()
    story_id = data.get("story_id")
    if not story_id or not await db.stories.find_one({"_id": story_id}):
        logger.error("[/stories-proxy] [POST]: story_id not provided.")
        return utils.get_http_error("Requested story not found")

    if not data.get("asset_id"):
        logger.error("[/stories-proxy] [POST] [{}]: asset_id not provided.".format(story_id))
        return utils.get_http_error("File information not provided.")

    assetinfo = await db.assets.find_one({"_id": data["asset_id"]})
    if not assetinfo:
        logger.error("[/stories-proxy] [POST] [{}]: asset '{}' not found in db.".format(story_id, data["asset_id"]))
        return utils.get_http_error("File information not found in database.")

    # posting proxy tasks
    if not await submit_story_thumbnail_task(assetinfo, story_id):
        logger.error("[/stories-proxy] [POST] [{}]: Failed to create proxy task.".format(story_id))
        return utils.get_http_error("Failed to create proxy task.")
    return aioweb.json_response({"ok": True})


@routes.put("/stories-assets/{asset_id}")
async def update_story_file_details(request):
    db = request.app["db"]
    '''
    "path": "share://{storage_id}/folder1/folder2/filename.mov",
    '''
    asset_id = request.match_info["asset_id"]

    data = await request.json()

    query = {}
    assetinfo = {}

    # parsing user input and preparing data
    query["asset_id"] = asset_id

    if data.get("lowres_path"):
        assetinfo["lowres_path"] = data["lowres_path"]

    if data.get("thumbnail_path"):
        assetinfo["thumbnail_path"] = data["thumbnail_path"]

    # TODO: verify file is uploaded
    if not assetinfo:
        logger.error("[/stories-assets] [PUT] [{}]: No asset information provided to update.".format(asset_id))
        return aioweb.json_response({"ok": False})

    # saving to db
    res = await db.assets.update_one(query, {"$set": assetinfo})

    # parsing motor response
    if not res.raw_result["updatedExisting"]:
        if res.matched_count == 0:
            logger.error("[/stories] [PUT] [{}]: Requested asset not found.".format(asset_id))
            return utils.get_http_error("Requested asset not found")

        logger.error("[/stories] [PUT] [{}]: Failed to save to db.".format(asset_id))
        return utils.get_http_error("Server ran into database error", httperror=aioweb.HTTPInternalServerError)

    logger.info("[/stories-assets] [PUT] [{}]: Asset information '{}' updated to database."
                .format(asset_id, assetinfo))
    return aioweb.json_response({"ok": True})


@routes.get("/stories-assets")
async def get_story_all_assets(request):
    db = request.app["db"]

    story_id = request.rel_url.query.get("story_id")
    if not story_id:
        logger.error("[/stories-assets] [GET]: story_id not provided.")
        return utils.get_http_error("Story_id not provided")

    assets = []
    async for asset in db.assets.find({"story_id": story_id}):
        assets.append(asset)
    return aioweb.json_response({"assets": assets})


@routes.get("/version/recent/{story_id}")
async def get_recent_version_of_story(request):
    """
    Get the recent version of the story
    story_id: Checking with this story id
    :return: The latest story version
    """
    db = request.app['db']
    # Get the version data from db
    story_id = request.match_info["story_id"]
    version_info_cursor = db.story_versions.find({"story_id": story_id}, projection={"_id": False}).sort('version_time',-1)
    # Prepare the version data
    logger.info("Version requested for  : {}".format(story_id))
    version_data = dict()
    version_data['total_version_count'] = await db.story_versions.count_documents({"story_id": story_id})
    if version_data['total_version_count']:
        for v in await version_info_cursor.to_list(length=1):
            res = v
        version_data['recent_version'] = res
    else:
        version_data['recent_version'] = None
    # Return the version data prepared
    logger.info("Version info returning is : {}".format(version_data))
    return aioweb.json_response(version_data)


@routes.get("/version/history/{story_id}/{skip_interval}")
async def get_version_history_of_story(request):
    """
    Get the version history of the story,
    This is to basically serve you the versions of the story
    story_id: The story id being requested for
    :param skip_interval: The no of versions to skip over
    :return: the list of the versions
    """
    db = request.app["db"]
    # Get the version data from db
    story_id = request.match_info["story_id"]
    skip_interval = int(request.match_info['skip_interval'])

    # Prepare the query to fetch details from database
    if skip_interval:
        version_info = db.story_versions.find({"story_id": story_id},projection={"_id": False}).\
                                               sort("version_time", -1).\
                                               skip(skip_interval)
    else:
        version_info = db.story_versions.find({"story_id": story_id},{"_id": 0}). \
                                               sort("version_time", -1)

    # Prepare the version data to be sent
    version_data = {}
    if version_info:
        version_data['total_version_count'] = await db.story_versions.count_documents({"story_id": story_id})
        version_data['skip'] = skip_interval
        version_data['version_history'] = [ item for item in await version_info.limit(consts.VERSIONS_PER_PAGE).to_list(length=consts.VERSIONS_PER_PAGE)]
    else:
        version_data['total_version_count'] = 0
        version_data['skip'] = skip_interval
        version_data['version_history'] = []
    return aioweb.json_response(version_data)


@routes.post("/version")
async def create_new_version_of_story(request):
    """
    When the user updates the story, create an new version with that story_id
    :param story_id:
    """
    db = request.app["db"]

    # Check for necessary details, story_id and version_data
    data = await request.json()
    if "story_id" not in data:
        logger.error("[/version] [POST]: story_id not provided.")
        return utils.get_http_error("Version story_id not found")
    if "version_data" not in data:
        logger.error("[/version] [POST] version_data not provided")
        return utils.get_http_error("Version data not found")

    # Preparing the data to be inserted into story_versions
    version_info = {}
    version_info['story_id'] = data["story_id"]
    version_info["version_time"] = datetime.datetime.now().strftime(consts.VERSION_TIME_FORMAT)
    version_info['version_data'] = data["version_data"]
    resp = await db.story_versions.insert_one(version_info)
    logger.info("[/version] [POST] Version inserted is : {}".format(resp))
    return aioweb.json_response({"ok": True})
