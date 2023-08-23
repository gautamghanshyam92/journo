import json

from server.task import logger
from server.commons import session
import server.commons.utils as utils


async def send_status_to_reqserver(task_id, status_data):
    url = utils.get_request_server_url("tasks-status/{}".format(task_id))
    resp = await session.put(url, data=json.dumps(status_data))
    if resp.status != 200:
        logger.error("[send_status_to_reqserver] [{}]: Failed to send task status to Request Server.".format(task_id))
        return False

    resp = await resp.json()
    return True if resp.get("ok") else False


async def get_share_details(share_id):
    url = utils.get_request_server_url("shares/{}".format(share_id))
    resp = await session.get(url)
    return await resp.json() if resp.status is 200 else None