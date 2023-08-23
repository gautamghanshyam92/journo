"""
 This module is responsible for loading and making sure the streams are up and running.
      On startup if this module s loaded then it loads up the nginx config and keeps it in memory.
      it loads the json file containing the stream names.
      Supports a maximum of 20 streams loaded from a json file
 Conventions Used :
      stream name : alpha_12Sep19_175040
                   stream prefix : alpha
                   date of stream : 12Sep19
                   timestamp of stream start : 175040
"""
import os
import datetime
from aiohttp import web as aioweb
import server.commons.utils as utils
from server.request import logger
# shares all rest api routes are added to this table

routes = aioweb.RouteTableDef()


def move_stream_to_recordings(stream_name, recording_path):
    """
     Given a stream move it to the recording folder
    """
    # TODO Handle errors and use ASYNC FILE HANDLER
    if not os.path.exists(os.path.dirname(recording_path)):
        os.makedirs(os.path.dirname(recording_path))
    stream_path = "/mnt/hls/{}".format(stream_name)
    os.rename(stream_path, recording_path)


async def initial_setup(app):
    """
    Initial setup of the stream server
    :param app: store the nginx data in the app itself
    """
    app["stream_url_prefix"] = utils.get_stream_url_prefix()
    app["stream_names"] = utils.get_stream_names()
    # logger.info("Streams [initial_setup] stream_prefix_url : {} & {}".format(app["stream_url_prefix"], app["stream_names"]))
    logger.info("Stream [Setup] Setup of streams completed : ")
    return True


def prepare_stream(stream_prefix_url=None,
                   name=None,
                   url=None,
                   userid=None,
                   status=None):
    """
    Prepares the stream object any changes on the datastructur of the stream will occur here
    :param stream_prefix_url: the stream prefix url generated at runtime
    :param name: The stream name on which the stream will take place
    :param url: the complete url with the stream prefix and the stream name
    :param userid: userid of the user requesting access of the stream
    :param status: can be busy, completed or avaialbe by default available
    :return: dict containing the stream data
    """
    stream = {}
    stream["name"] = name
    if not url and stream_prefix_url:
        stream_name = name
        stream["url"] = stream_prefix_url+stream_name
    if url:
        stream["url"] = url
    if status:
        stream["status"] = status
    else:
        stream["status"] = "available"
    stream["userid"] = userid
    return stream


@routes.get("/streams")
async def get_streams(request):
    """
    Returns the details of the streams live and available
    :return: the list of streams avaliable & being used
    return data structure :
    {
    "streams":      [, {}, {}, {}, {}]}
    stream = {"stream_url" : "rtmp://server_ip:port/stream_app/stream_name",
              "status": "available", "stream_prefix": "alpha"}
    stream = {"stream_url" : "rtmp://server_ip:port/stream_app/stream_name",
              "status": "busy", "stream_prefix": "beta", "user_info": {"userid": "user1id"} }
    """
    # db instance
    db = request.app["db"]

    stream_query = {"status": "busy"}

    # logger.info("[/streams] [GET] : stream query is : {}".format(stream_query))
    busy_streams = []
    busy_stream_names = []
    available_streams = []

    async for busy_stream in db.streams.find(stream_query, {"_id": 0}):
        busy_streams.append(busy_stream)
        busy_stream_names.append(busy_stream['name'])

    for name in request.app["stream_names"]:
        if name in busy_stream_names:
            continue
        stream = prepare_stream(stream_prefix_url=request.app["stream_url_prefix"], name=name)
        available_streams.append(stream)
    
    total_streams = busy_streams+available_streams
    logger.info("[/streams] [GET] Total number of availablle streams are : {}/{}".format(len(available_streams), len(total_streams)))

    # TODO CLEANUP TIMEDOUT STREAMS
    
    return aioweb.json_response(total_streams)


@routes.post("/streams")
async def create_stream(request):
    """
    Given a stream name if the stream name is not already taken,
    then give access to the user else rasies 410 GONE to indicate that the resoucres is gone
    :param request: request
    :return: ok if the stream can be accuired by user else 410 error
    """
    db = request.app["db"]
    stream_data = await request.json()
    if not stream_data:
        logger.error("[/streams] [POST] Stream Data is invalid. {}".format(stream_data))
        return utils.get_http_error("Stream Data must be provided")

    stream_name = stream_data.get("stream_name")
    if not stream_name:
        logger.error("[/streams] [POST] Stream Name is invalid. {}".format(stream_name))
        return utils.get_http_error("Stream Name must be provided")

    if not stream_data.get("url"):
        logger.error("[/streams] [POST] Stream url is invalid. {}".format(stream_data))
        return utils.get_http_error("Stream Data must contain valid URL")

    if not stream_data.get("userid"):
        logger.error("[/streams] [POST] Valid userid must be provided {}".format(stream_data))
        return utils.get_http_error("Stream Data must contain valid userid.")

    stream = prepare_stream(url=stream_data["url"],
                            name=stream_name,
                            userid=stream_data["userid"], status="busy")

    insert_result = await db.streams.update_one({"name": stream_name, "status":"busy"},
                                                {"$setOnInsert": stream}, upsert=True)

    if not insert_result.upserted_id:
        if insert_result.matched_count > 0 and insert_result.modified_count == 0:
            logger.error("[/streams] [POST] [{}]: Stream already acquired.".format(stream_name))
            return utils.get_http_error(message="Stream name {} unavailable".format(stream_name), code=410)

        logger.error("[/streams] [POST] [{}]: Failed to save to db.".format(stream_name))
        return utils.get_http_error("Server ran into database error")

    await utils.push_feed(msg='stream-started', data=stream)
    logger.info("[/streams] POST : Stream entry created successfully. {}".format(stream_name))
    return aioweb.json_response({"stream_name": stream_name, "ok": True})


@routes.delete("/streams/{stream_name}/{user_id}")
async def delete_stream(request):
    """
     Delete the access of the stream 
     if the key force_close is recieved then the stream is closed.
     if the userid is recieved then the stream is checked if that user is 
    """
    db = request.app["db"]
    stream_name = request.match_info["stream_name"]
    user_id = request.match_info["user_id"]
    if not stream_name:
        logger.error('[/streams] [DELETE] Stream Name is invalid. {}'.format(stream_name))
        return utils.get_http_error("Stream Name must be provided")

    ''' 
    if "force_close" in stream_data:
        # This is for terminating the stream due to TimeOut
        raise NotImplementedError
    '''

    stream_details = await db.streams.find_one({"name": stream_name,
                                                 "status": "busy",
                                                 "userid": user_id
                                                })
    if not stream_details:
        logger.error("[/streams] [DELETE] Could not find Matching Stream for stream_name: {} and user: {}"
                     .format(stream_name, user_id))
        return utils.get_http_error("Could not find matching stream.")
    
    if utils.generate_playlist(stream_name):
        recording_path = utils.get_recording_path(stream_name)
        move_stream_to_recordings(stream_name, recording_path)
        logger.info("/streams] [DELETE] Successfully moved stream to : {}".format(recording_path))

    result = await db.streams.delete_one({"name": stream_name, "status": "busy"})
    logger.info("[/streams] [DELETE] Result of delete command is : {}: {}".format(stream_name, result))

    stream = prepare_stream(stream_prefix_url=request.app["stream_url_prefix"], 
                            name=stream_name)
    await utils.push_feed(msg='stream-ended', data=stream)
    return aioweb.json_response({"stream_name": stream_name, "ok": True})
