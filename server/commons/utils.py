
import crossplane
import datetime
import hashlib
import json
import os
import re
import uuid

from aiohttp import web as aioweb

# importing logger
from server.commons.logger import logger
import server.commons.constants as consts
import server.config as conf
from server.commons import session

# ------------- Common Api's ---------------


def get_http_error(message="", httperror=aioweb.HTTPUnprocessableEntity, code=None):
    error = {
        "code": code,
        "message": message
    }
    return httperror(text=json.dumps(error))


def generate_md5_for_string(s):
    return hashlib.md5(s.encode(consts.APP_ENCODING)).hexdigest()


def generate_hex_id(*args):
    s = ""
    for e in args:
        s += "".join(re.findall("[a-zA-Z0-9]+", e))
    return generate_md5_for_string(s)


def generate_random_id():
    return "{}".format(uuid.uuid4()).replace("-", "")


def get_request_server_url(path):
    return "http://{}:{}/{}".format(conf.REQUEST_SERVER_IP, conf.REQUEST_SERVER_PORT, path)


def get_task_server_url(path):
    return "http://{}:{}/{}".format(conf.TASK_SERVER_IP, conf.TASK_SERVER_PORT, path)


def get_feed_server_url(path):
    # return "http://{}:{}/{}".format(conf.FEED_SERVER_IP, conf.FEED_SERVER_PORT, path)
    return "http://{}:{}/{}".format(conf.REQUEST_SERVER_IP, conf.REQUEST_SERVER_PORT, path)


def get_websocket_server_url(path, user_id):
    return "http://{}:{}/{}?user_id={}".format(conf.FEED_SERVER_IP, conf.FEED_SERVER_PORT, path, user_id)


def print_motor_response(res):
    for key in ['acknowledged', 'matched_count', 'modified_count', 'raw_result', 'upserted_id', 'deleted_count']:
        if not hasattr(res, key):
            continue
        logger.info("[MotorResponse]: {}: {}".format(key, getattr(res, key)))


def is_valid_email_format(email_id):
    return re.search(r"^.+@.+\..+$", email_id) is not None


async def push_feed(msg, data):
    """
     Post the feed to the feed server.
    """
    if not msg or not data:
        logger.info('[push_feed] Invalid message/data received : msg:{} , data:{}'.format(msg, data))
        return
    feed = {}
    feed['message'] = msg
    feed['data'] = data
    await session.post(url=get_feed_server_url('feeds'), data=json.dumps(feed))

def get_template_mapping():
    template_mapping = {}
    try:
        if os.path.isfile('./settings/template_mapping.json'):
            with open("./settings/template_mapping.json") as template:
                template_mapping = json.load(template)
    except Exception as ex:
        logger.exception("[commons.__init__]: template_mapping could not be fetched : {}".format(ex))
    return template_mapping


def generate_proxy_url(share_path):
    """
     Generate the proxy url for the share path
    """
    return "http://{}:{}/{}/".format(conf.NGINX_SERVER_IP, conf.NGINX_SERVER_PORT, consts.NGINX_PROXY_ROUTE)


def generate_media_url(share_path):
    """
     Generate the source media url for the share path
    """
    return "http://{}:{}/{}/".format(conf.NGINX_SERVER_IP, conf.NGINX_SERVER_PORT, consts.NGINX_SOURCE_ROUTE)


def get_nginx_data():
    """
     Fetches the nginx config by parsing it into a dictionary containing lists
     return payload : the data after parsing the nginx data
    """
    payload = crossplane.parse(consts.NGINX_CONF_PATH)
    return payload


def get_stream_url_prefix():
    """
    Given the ngixn conf parsed data return the stream url prefix
    sample url prefix : "rtmp://serverIP:rtmpPort/[streamApplication]/"
    :return: OnSuccess streamPrefixUrl else None
    """
    payload = get_nginx_data()
    stream_prefix_url = "{proto}://{server_ip}:{port}/{stream_application_name}/"
    proto = port = stream_application_name = None
    server_ip = conf.NGINX_SERVER_IP
    for sections in payload.get("config"):
        if sections.get('file') == consts.NGINX_CONF_PATH and sections.get('status') == "ok":
            for block in sections.get("parsed"):
                if block.get("directive") == consts.NGINX_STREAM_PROTOCOL:
                    proto = consts.NGINX_STREAM_PROTOCOL
                    for proto_block in block.get("block"):
                        if proto_block.get("directive") == "server":
                            for server_block in proto_block.get("block"):
                                if server_block.get("directive") == "listen":
                                    port = server_block["args"][-1] if server_block.get("args", []) else None
                                if server_block.get("directive") == "application":
                                    stream_application_name = server_block["args"][-1] if server_block.get("args") else None
                            # Break if the server block is found
                            break
                    # Break if the protocol block is found
                    break
            # Break if nginx conf is read
            break

    if not proto or not port or not stream_application_name:
        stream_prefix_url = ""
    return stream_prefix_url.format(proto=proto, server_ip=server_ip, port=port,
                                    stream_application_name=stream_application_name)


def get_stream_names():
    """
    REad the json file with stream names and returns a list of stream names
    :return: [alpha, beta, gamma, delta ...]
    """
    streams = {}
    if os.path.isfile(consts.STREAM_NAMES_JSON):
        with open(consts.STREAM_NAMES_JSON) as stream_file:
            streams = json.load(stream_file)
    return streams.get("streams", [])


def generate_playlist(stream_name):
    """
     Given a stream name 
     generate the stream path and generate a playlist in that folder
    """
    stream_path = "/mnt/hls/{}".format(stream_name)
    if not os.path.exists(stream_path):
        return False
    ts_files = []
    for _file in os.listdir(stream_path):
        if not _file.endswith(".ts"):
            continue
        ts_files.append(_file)
    ts_files.sort(key=lambda _file: int(_file.split(".ts")[0]))
    playlist_file = os.path.join(stream_path, "playlist.txt")
    with open(playlist_file, "w") as wfile:
        for tsfile in ts_files[1:]:
            wfile.write("file {}\n".format(tsfile))
    # logger.info("[generate_playlist] Successfully created an playlist. \n {}".format(playlist_file))
    return True

def get_recording_path(stream_name):
    """
     Get the path for the recordings given a stream name.
     The path is prepared using the storage followed recordings
    """
    # for now gonna assume that the storage name for the streaming is hls
    # and the path for recordings is gonna be 
    #    hls/recordings/stream_name_timestamp
    timestamp = datetime.datetime.now().strftime(consts.VERSION_TIME_FORMAT)
    # TODO prepare path from storage details
    recording_path = '/mnt/hls/recordings/{}_{}'.format(stream_name, timestamp)
    return recording_path


def get_media_url(path=None, media_type=None):
    """
     get the file source url path.
    """
    if not type or not path:
        return ""
    
    nginx_ip = conf.NGINX_SERVER_IP
    nginx_port = 8384
    if media_type == "video":
        nginx_rendering_app = consts.NGINX_VIDEO_ROUTE
        source_url = "http://{nginx_ip}:{nginx_port}/{nginx_rendering_app}/{relative_path}/index.m3u8"
    else:
        nginx_rendering_app = consts.NGINX_IMAGE_ROUTE
        source_url = "http://{nginx_ip}:{nginx_port}/{nginx_rendering_app}/{relative_path}"
    relative_path = re.sub(r'''{}[\w]+/'''.format(consts.SHARE_URI_PREFIX), "", path)
    
    return source_url.format(nginx_ip=nginx_ip,
                             nginx_port=nginx_port,
                             nginx_rendering_app=nginx_rendering_app,
                             relative_path=relative_path)
    

def generate_stream_url(stream_name):
    stream_url = "http://{nginx_ip}/streams/{stream_name}/index.m3u8"
    nginx_ip = conf.NGINX_SERVER_IP
    return stream_url.format(nginx_ip=nginx_ip, stream_name=stream_name) 
