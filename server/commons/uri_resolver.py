"""
This modules responsibility is following:
  - convert from one uri to another example share:// to ftp://
  - convert uri to absolute or relative path
"""

import os

import server.commons.constants as consts
from server.commons.logger import logger


def get_share_uri_relative_path(uri, share_id):
    return uri.split(consts.SHARE_URI_PREFIX+share_id+"/")[-1]


def get_abs_path_from_uri_for_share(uri, share):
    if not uri.startswith(consts.SHARE_URI_PREFIX):
        logger.error("[get_abs_path_from_uri_for_share]: Invalid uri. uri doesn't starts with share://")
        return None

    if consts.PROTOCOL_FILE not in share["protocols"]:
        logger.error("[get_abs_path_from_uri_for_share]: Only 'file' protocol is supported.")
        return None

    path_info = share["paths"][consts.PROTOCOL_FILE]
    # preparing absolute path
    return os.path.join(path_info["path"], get_share_uri_relative_path(uri, share["_id"]))