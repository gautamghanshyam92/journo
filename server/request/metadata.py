from aiohttp import web as aioweb
import datetime
# importing logger
from server.request import logger

import server.commons.utils as utils
import server.commons.constants as consts

def generate_category_uid(name):
    return name.replace(" ", "").lower()


def generate_tag_uid(name):
    return name.replace(" ", "").lower()

# ------------ Metadata Routes ------------


routes = aioweb.RouteTableDef()

# ------------ Categories --------------


@routes.post("/categories")
async def create_new_category(request):
    db = request.app["db"]

    data = await request.json()

    # validating user data
    category_name = data.get("name")
    if not category_name:
        logger.error("[/categories] [POST]: Category name not provided.")
        return utils.get_http_error("Category name not provided.")

    category_uid = generate_category_uid(category_name)
    category_id = utils.generate_random_id()
    created_time = datetime.datetime.now().strftime(consts.DATE_FORMAT)
    # checking if already exists
    if await db.categories.find_one({"uid": category_uid}):
        logger.error("[/categories] [POST] [{}]: category already exists.".format(category_uid))
        return utils.get_http_error("Category already exists.")

    # saving to db
    res = await db.categories.update_one({"uid": category_uid},
        {"$setOnInsert": {"name": category_name, "uid": category_uid,
         "created_time": created_time, "_id": category_id}}, upsert=True)

    # parsing motor response
    if not res.upserted_id:
        if res.matched_count > 0 and res.modified_count == 0:
            logger.error("[/categories] [POST] [{}]: Category already exists.".format(category_uid))
            return utils.get_http_error("Category already exists")

        logger.error("[/categories] [POST]: Failed to save to db.")
        return utils.get_http_error("Server ran into database error", httperror=aioweb.HTTPInternalServerError)

    logger.info("[/categories] [POST] [{}]: New category '{}' created."
        .format(category_uid, category_name))
    return aioweb.json_response({"ok": True, "_id": category_id, "uid": category_uid, "name": category_name})


@routes.get("/categories")
async def get_categories(request):
    db = request.app["db"]
    query = {}

    # preparing query with given prefix
    prefix_ = request.rel_url.query.get("prefix", None)
    if prefix_:
        query = {"name": {"$regex": "^{}".format(prefix_), "$options": "i"}}

    categories = []
    async for category in db.categories.find(query):
        categories.append({"uid": category["uid"], "name": category["name"], "_id": category["_id"]})
    return aioweb.json_response(categories)


@routes.get("/categories/{category_id}")
async def get_category_info(request):
    db = request.app["db"]

    category_id = request.match_info["category_id"]
    if category_id:
        categoryinfo = await db.categories.find_one({"_id": category_id})
        if categoryinfo:
            return aioweb.json_response(categoryinfo)
    return aioweb.json_response(None)
    

@routes.delete("/categories/{category_id}")
async def delete_category(request):
    db = request.app["db"]

    category_id = request.match_info["category_id"]
    if category_id:
        # deleting from db
        res = await db.categories.delete_one({"_id": category_id})
    
        # parsing motor response
        if res.deleted_count > 0:
            logger.info("[/categories] [DELETE]: Category '{}' deleted.".format(category_id))
            return aioweb.json_response({"ok": True})

    logger.error("[/categories] [DELETE]: Failed to delete category '{}'.".format(category_id))
    return aioweb.json_response({"ok": False})


@routes.put("/categories/{category_id}")
async def update_category(request):
    db = request.app["db"]

    category_id = request.match_info["category_id"]

    data = await request.json()

    # parsing user data
    category_name = data.get("name")
    if not category_name:
        logger.error("[/categories] [PUT] [{}]: Category name not provided. Only category name can be changed."
            .format(category_id))
        return utils.get_http_error("Only category name can be updated")

    category_uid = generate_category_uid(category_name)

    # checking if same category already exists
    info = await db.categories.find_one({"uid": category_uid})
    if info and info["_id"] != category_id:
        logger.error("[/categories] [PUT] [{}]: Category with same name '{}' already exists"
            .format(category_id, category_name))
        return utils.get_http_error("Category with same name already exists")

    # saving to db
    res = await db.categories.update_one({"_id": category_id},
        {"$set": {"name": category_name, "uid": category_uid}})

    # parsing motor response
    if not res.raw_result["updatedExisting"]:
        if res.matched_count == 0:
            logger.error("[/categories] [PUT] [{}]: Requested category not found.".format(category_uid))
            return utils.get_http_error("Requested category not found")

        logger.error("[/categories] [PUT] [{}]: Failed to save to db.".format(category_uid))
        return utils.get_http_error("Server ran into database error", httperror=aioweb.HTTPInternalServerError)

    logger.info("[/categories] [PUT]: Category '{}' updated.".format(category_id))
    return aioweb.json_response({"ok": True})


@routes.post("/tags")
async def create_tag(request):
    db = request.app["db"]

    data = await request.json()

    # validating user input
    tag_name = data.get("name")
    if not tag_name:
        logger.error("[/tags] [POST]: tag_name not provided.")
        return utils.get_http_error("Tag name not provided.")

    tag_uid = generate_tag_uid(tag_name)
    tag_id = utils.generate_random_id()

    # checking if already exists
    if await db.tags.find_one({"uid": tag_uid}):
        logger.error("[/tags] [POST] [{}]: tag already exists.".format(tag_uid))
        return utils.get_http_error("Tag already exists.")

    # saving to db
    res = await db.tags.update_one({"uid": tag_uid},
        {"$setOnInsert": {"name": tag_name, "uid": tag_uid, "_id": tag_id}},
        upsert=True)

    # parsing motor response
    if not res.upserted_id:
        if res.matched_count > 0 and res.modified_count == 0:
            logger.error("[/tags] [POST] [{}]: tag already exists.".format(tag_uid))
            return utils.get_http_error("tag already exists")

        logger.error("[/tags] [POST] [{}]: Failed to save to db.".format(tag_uid))
        return utils.get_http_error("Server ran into database error", httperror=aioweb.HTTPInternalServerError)

    logger.info("[/tags] [POST] [{}: New tag '{}' created.".format(tag_uid, tag_name))
    return aioweb.json_response({"ok": True, "_id": tag_id, "uid": tag_uid, "name": tag_name})


@routes.get("/tags")
async def get_all_tags(request):
    db = request.app["db"]
    query = {}

    # preparing query with given prefix
    prefix_ = request.rel_url.query.get("prefix", None)
    if prefix_:
        query = {"name": {"$regex": "^{}".format(prefix_), "$options": "i"}}

    tags = []
    async for tag in db.tags.find(query):
        tags.append({"_id": tag["_id"], "name": tag["name"], "uid": tag["uid"]})
    return aioweb.json_response(tags)


@routes.get("/tags/{tag_id}")
async def get_tag_info(request):
    db = request.app["db"]

    tag_id = request.match_info["tag_id"]
    if tag_id:
        taginfo = await db.tags.find_one({"_id": tag_id})
        if taginfo:
            return aioweb.json_response(taginfo)
    return aioweb.json_response(None)


@routes.delete("/tags/{tag_id}")
async def delete_tag(request):
    db = request.app["db"]

    tag_id = request.match_info["tag_id"]
    if tag_id:
        # deleting from db
        res = await db.tags.delete_one({"_id": tag_id})

        # parsing motor response
        if res.deleted_count > 0:
            logger.info("[/tags] [DELETE]: Tag '{}' deleted.".format(tag_id))
            return aioweb.json_response({"ok": True})

    logger.error("[/tags] [DELETE]: Failed to delete tag '{}'.".format(tag_id))
    return aioweb.json_response({"ok": False})


@routes.put("/tags/{tag_id}")
async def update_tag(request):
    db = request.app["db"]

    tag_id = request.match_info["tag_id"]

    data = await request.json()

    # validating user input
    tag_name = data.get("name")
    if not tag_name:
        logger.error("[/tags] [PUT]: tag_name not provided. Only tag name is allowed to be changed.")
        return utils.get_http_error("Only tag name is allowed to be changed")
    tag_uid = generate_tag_uid(tag_name)

    # checking if already exists
    info = await db.tags.find_one({"uid": tag_uid})
    if info and info["_id"] != tag_id:
        logger.error("[/tags] [POST] [{}]: tag already exists.".format(tag_uid))
        return utils.get_http_error("Tag already exists.")

    # saving to db
    res = await db.tags.update_one({"_id": tag_id},
        {"$set": {"name": tag_name, "uid": tag_uid}})

    # parsing motor response
    if not res.raw_result["updatedExisting"]:
        if res.matched_count == 0:
            logger.error("[/tags] [PUT] [{}]: Requested tag not found.".format(tag_uid))
            return utils.get_http_error("Requested tag not found")

        logger.error("[/tags] [PUT] [{}]: Failed to save to db.".format(tag_uid))
        return utils.get_http_error("Server ran into database error", httperror=aioweb.HTTPInternalServerError)

    logger.info("[/tags] [PUT]: Tag '{}' updated successfully.".format(tag_id))
    return aioweb.json_response({"ok": True})