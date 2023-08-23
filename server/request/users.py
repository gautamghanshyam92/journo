"""
    Manages all user related operations including:
    - rest api
    - user authentication system
    - user privilege systems.
"""

from aiohttp import web as aioweb

from server.request import logger

import server.commons.utils as utils

routes = aioweb.RouteTableDef()


@routes.post("/users")
async def save_user_info(request):
    db = request.app["db"]

    userinfo = {}
    data = await request.json()

    # validating and preparing user data
    for key in ["display_name", "username", "password", "email"]:
        if not data.get(key):
            logger.error("[/users] [POST]: '{}' not provided.".format(key))
            return utils.get_http_error("Required information -> '{}' not provided".format(key))

    if not utils.is_valid_email_format(data["email"]):
        logger.error("[/users] [POST]: invalid email format provided.")
        return utils.get_http_error("Invalid email format provided")

    userinfo["display_name"] = data["display_name"]
    userinfo["username"] = data["username"]
    userinfo["password"] = data["password"]
    userinfo["email"] = data["email"]

    # checking if username already exists
    if await db.users.find_one({"username": userinfo["username"]}):
        logger.error("[/users] [POST]: username '{}' already exists.".format(userinfo["username"]))
        return utils.get_http_error("Username already exists")

    # checking if user with same email id already exists
    if await db.users.find_one({"email": userinfo["email"]}):
        logger.error("[/users] [POST]: email '{}' already in use by other user.".format(userinfo["email"]))
        return utils.get_http_error("Email already in use by other user")

    # hexadecimal id to uniquely identify user
    userinfo["_id"] = utils.generate_random_id()

    # extra details about user
    userinfo["mobile"] = "{}".format(data["mobile"]) if data.get("mobile") else None

    # privileges provided to user in terms of roles
    userinfo["roles"] = data.get("roles", [])
    # TODO: Validate 'roles' using user authorization system

    # saving to db
    res = await db.users.update_one({"_id": userinfo["_id"]}, {"$setOnInsert": userinfo}, upsert=True)

    # parsing motor response
    if not res.upserted_id:
        if res.matched_count > 0 and res.modified_count == 0:
            logger.error("[/users] [POST] [{}]: User already exists.".format(userinfo["email"]))
            return utils.get_http_error("User already exists")

        logger.error("[/users] [POST] [{}]: Failed to save to db.".format(userinfo["_id"]))
        return utils.get_http_error("Server ran into database error", httperror=aioweb.HTTPInternalServerError)

    logger.info("[/users] [POST]: New user '{}' created successfully.".format(userinfo))
    return aioweb.json_response({"ok": True})


@routes.put("/users/{user_id}")
async def update_user_info(request):
    db = request.app["db"]
    user_id = request.match_info["user_id"]

    userinfo = {}
    data = await request.json()

    # validating user input
    if data.get("display_name"):
        userinfo["display_name"] = data["display_name"]

    if data.get("username"):
        userinfo["username"] = data["username"]

    if data.get("password"):
        userinfo["password"] = data["password"]

    if data.get("email"):
        if not utils.is_valid_email_format(data["email"]):
            logger.error("[/users] [PUT]: invalid email format provided.")
            return utils.get_http_error("Invalid email format provided")
        userinfo["email"] = data["email"]

    if data.get("mobile"):
        userinfo["mobile"] = "{}".format(data["mobile"])

    if data.get("roles"):
        # TODO: Validate 'roles' using user authorization system
        userinfo["roles"] = data["roles"]

    if userinfo.get("email"):
        # checking if email is already being used by some other user
        info = await db.users.find_one({"email": userinfo["email"]})
        if info and info["_id"] != user_id:
            logger.error("[/users] [PUT] [{}]: email id '{}' already used by some other user."
                         .format(user_id, userinfo["email"]))
            return utils.get_http_error("Email already in use by other user")

    # saving to db
    res = await db.users.update_one({"_id": user_id}, {"$set": userinfo})

    # parsing motor response
    if not res.raw_result["updatedExisting"]:
        if res.matched_count == 0:
            logger.error("[/users] [PUT] [{}]: Requested user not found.".format(user_id))
            return utils.get_http_error("Requested user not found")

        logger.error("[/users] [PUT] [{}]: Failed to save to db.".format(user_id))
        return utils.get_http_error("Server ran into database error", httperror=aioweb.HTTPInternalServerError)

    if userinfo.get("password"):
        del userinfo["password"]
    logger.info("[/users] [PUT] [{}]: User info '{}' updated successfully.".format(user_id, userinfo))
    return aioweb.json_response({"ok": True})


@routes.get("/users")
async def get_all_users(request):
    db = request.app["db"]

    users = []
    async for user in db.users.find():
        users.append(user)
    return aioweb.json_response({"users": users})


@routes.get("/users/{user_id}")
async def get_user_info(request):
    db = request.app["db"]

    userinfo = None
    user_id = request.match_info["user_id"]
    if user_id:
        userinfo = await db.users.find_one({"_id": user_id})
    return aioweb.json_response(userinfo if userinfo else None)


@routes.delete("/users/{user_id}")
async def delete_user_info(request):
    db = request.app["db"]

    user_id = request.match_info["user_id"]
    if user_id:
        # deleting user
        res = await db.users.delete_one({"_id": user_id})
        # parsing motor response
        if res.deleted_count > 0:
            logger.info("[/users] [DELETE]: User '{}' deleted.".format(user_id))
            return aioweb.json_response({"ok": True})

    logger.error("[/users] [DELETE]: Failed to delete user '{}'.".format(user_id))
    return aioweb.json_response({"ok": False})


@routes.post("/users-sessions")
async def create_user_session(request):
    db = request.app["db"]

    data = await request.json()

    if not data.get("username") and not data.get("email"):
        logger.error("[/users-sessions] [POST]: Neither username nor email provided to create session.")
        return utils.get_http_error("Neither username nor email provided")

    # validating username
    userinfo = None
    if data.get("username"):
        userinfo = await db.users.find_one({"username": data["username"]})
        if not userinfo:
            logger.error("[/users-sessions] [POST]: No user with given username '{}' found.".format(data["username"]))
            return utils.get_http_error("User with name '{}' not found".format(data["username"]),
                                        httperror=aioweb.HTTPUnauthorized)

    # validating email
    if data.get("email"):
        userinfo = await db.users.find_one({"email": data["email"]})
        if not userinfo:
            logger.error("[/users-sessions] [POST]: No user with given email '{}' found.".format(data["email"]))
            return utils.get_http_error("User with email '{}' not found".format(data["email"]),
                                        httperror=aioweb.HTTPUnauthorized)

    # validating password
    if userinfo["password"] != data.get("password", None):
        logger.error("[/users-sessions] [POST]: Wrong password provided for user '{}'.".format(userinfo["email"]))
        return utils.get_http_error("Wrong password provided", httperror=aioweb.HTTPUnauthorized)

    logger.info("[/users-sessions] [POST]: User '{}' successfully authenticated.".format(userinfo["email"]))

    # TODO: Create user session and return it. That session should be used for further communication
    # adding the websocket url
    user_id = userinfo['_id']
    userinfo['ws'] = utils.get_websocket_server_url('ws', user_id)

    # sending userinfo without password
    del userinfo["password"]
    return aioweb.json_response(userinfo)
