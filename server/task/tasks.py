import re
import asyncio
import functools
import json

from server.task import logger

import server.commons.constants as consts
import server.commons.uri_resolver as urv
import server.task.reqclient as rcl

FFMPEG_PATH = "/usr/bin/ffmpeg"
FFPROBE_PATH = "/usr/bin/ffprobe"
MEDIAINFO_PATH = "/usr/bin/mediainfo"


# ------------------- CHILD PROCESS MANAGEMENT ---------------------
class ProcessHandler(asyncio.SubprocessProtocol):
    """
        Handles spawned process pipes and communicates to process using pipes
    """

    def __init__(self, future, handler, task_id=None, stdin_data=None):
        self.task_id = task_id
        # validating future object
        if not asyncio.isfuture(future):
            raise TypeError("ProcessHandler(task_id={})< argument 'future' must be asyncio.Future object >"
                .format(self.task_id))
        self._future = future

        # validating handler
        if not handler:
            raise ValueError("ProcessHandler(task_id={})< argument 'handler' must be object type >"
                .format(self.task_id))
        self._handler = handler

        # data written to stdin
        self.stdin_data = stdin_data
        super().__init__()

        self.transport = None

    def connection_made(self, transport):
        self.transport = transport
        logger.info("[ProcessHandler.connection_made]: Process '{}' started for '{}' task.".format(
            self.transport.get_pid(), self.task_id))

        # writing to stdin
        if self.stdin_data:
            transport_stdin = self.transport.get_pipe_transport(0)
            transport_stdin.write(self.stdin_data)
            transport_stdin.close()

    def pipe_data_received(self, fd, data):
        if fd == 1 and hasattr(self._handler, "out_data"):
            self._handler.out_data(data)

        elif fd == 2 and hasattr(self._handler, "err_data"):
            self._handler.err_data(data)

    def process_exited(self):
        exit_code = self.transport.get_returncode()
        self._future.set_result(exit_code)
        logger.debug("[ProcessHandler.process_exited]: Process exited with exit code '{}' for task '{}'."
                     .format(exit_code, self.task_id))


# ------------------- MEDIA UTILS ---------------------
async def get_media_duration(media_path):
    cmd = [FFPROBE_PATH, "-show_format", "-hide_banner", "-print_format", "json", "-v", "quiet", media_path]

    # spawning new process and waiting for it to exit
    proc = await asyncio.create_subprocess_exec(*cmd, stdout=asyncio.subprocess.PIPE)
    stdout, _ = await proc.communicate()

    # checking command exit code
    if proc.returncode != 0:
        logger.error("[get_media_duration]: Failed to get duration. '{}' command exited with exit code '{}'."
            .format(FFPROBE_PATH, proc.returncode))
        return 0

    # parsing command output
    data = stdout.decode(consts.APP_ENCODING)
    data = json.loads(data)["format"] if data else {}

    return float(data.get("duration", 0))


# ------------------- LOWRES TASK ---------------------
async def prepare_lowres_task(data):
    task = {}
    for key in ["media_path", "lowres_path", "task_id", "share_id", "proxy_share_id"]:
        if not data.get(key):
            return None, "'{}' not provided".format(data[key])

    task["task_name"] = consts.TASK_GENERATE_LOWRES
    task["task_id"] = data["task_id"]
    task["share_id"] = data["share_id"]
    task["proxy_share_id"] = data["proxy_share_id"]

    # preparing share absolute path
    media_share = await rcl.get_share_details(task["share_id"])
    if media_share is None:
        return None, "failed to retrieve media storage '{}' details from request server.".format(data["share_id"])

    task["media_uri"] = data["media_path"]
    task["media_path"] = urv.get_abs_path_from_uri_for_share(data["media_path"], media_share)

    # preparing lowres absoulte path
    proxy_share = await rcl.get_share_details(task["proxy_share_id"])
    if proxy_share is None:
        return None, "failed to retrieve proxy storage '{}' details from request server.".format(data["proxy_share_id"])

    task["lowres_uri"] = data["lowres_path"]
    task["lowres_path"] = urv.get_abs_path_from_uri_for_share(data["lowres_path"], proxy_share)
    return task, ""


class LowresTask:
    """
    TODO:
        * validating media file
        * error reporting
    """

    def __init__(self, task_id, media_path, lowres_path, params=None):
        # task info
        self.task_id = task_id
        self.name = consts.TASK_GENERATE_LOWRES

        # media and lowres path
        self.media_path = media_path
        self.lowres_path = lowres_path

        # command parameters to generate lowres
        self.params = {
            "scale": "320:240"
        }

        # callbacks to communicate command status
        self.status_callback = None

        # parsing and setting command params
        self.parse_params(params)

    def parse_params(self, params):
        if not params:
            return

        # validating and setting lowres video scale
        if not params.get("scale") or re.search(r"^[0-9]:[0-9]$", params["scale"]) is None:
            raise ValueError("LowresTask(task_id={})< invalid command parameter 'scale' value provided >"
                .format(self.task_id)) 
        self.params["scale"] = params["scale"]

    def generate_command(self):
        cmd = [ FFMPEG_PATH, "-y", "-hide_banner", "-i", self.media_path, "-vf" ]
        for key,_ in self.params.items():
            if key == "scale":
                cmd.append("scale={}".format(self.params["scale"]))
        cmd.append(self.lowres_path)
        return cmd

    async def run(self, loop, status_callback=None, exit_callback=None):
        # setting status callbacks 
        self.status_callback = status_callback if callable(status_callback) else lambda _id, d: logger.debug(d)

        # getting media duration
        self.duration = await get_media_duration(self.media_path)
        if not self.duration:
            logger.error("[LowresTask.run] [{}]: Failed to retrieve media '{}' duration."
                .format(self.task_id, self.media_path))
            return False

        # getting command
        command = self.generate_command()

        # configuring process with event loop
        future = asyncio.Future(loop=loop)
        factory = functools.partial(ProcessHandler, future, self, task_id=self.task_id)
        proc = loop.subprocess_exec(factory, *command, stdin=None)

        logger.info("[LowresTask.run] [{}]: Generating lowres with command '{}'.".format(self.task_id, command))
        transport = None
        try:
            transport,_ = await proc
            logger.debug("[LowresTask.run] [{}]: Waiting for process to complete.".format(self.task_id))
            await future
        finally:
            if transport: transport.close()

        # processing exit code
        status = False
        status_data = {"task_id": self.task_id, "task_name": consts.TASK_GENERATE_LOWRES}
        exit_code = future.result()
        if exit_code == 0:
            status = True
            status_data["status"] = consts.STATE_COMPLETED
            status_data["progress"] = 100.0
            logger.info("[LowresTask.run] [{}]: Lowres generated successfully.".format(self.task_id))
        else:
            status_data["status"] = consts.STATE_FAILED
            status_data["progress"] = 0.0
            logger.info("[LowresTask.run] [{}]: Failed to generate lowres.".format(self.task_id))

        # calling registered status callback
        if self.status_callback: self.status_callback(self.task_id, status_data)

        # calling registered exit callback
        if exit_callback: exit_callback(self.task_id, exit_code)
        return status

    def parse_output(self, line):
        try:
            line = bytes(line).decode(consts.APP_ENCODING).splitlines()[0].strip("\r")
            if not line.startswith("frame"):
                return {}

            tokens = list(filter(None, re.split(r" |=", line)))
            return dict((k, v) for k, v in zip(tokens[0::2], tokens[1::2]))
        except Exception as ex:
            logger.error("[LowresTask.parse_output] [{}]: Error '{}' while parsing output."
                .format(self.task_id, ex))
        return {}

    def out_data(self, data):
        logger.debug("[LowresTask.out_data]: {}".format(data))

    def err_data(self, data):
        # parsing output
        parsed_data = self.parse_output(data)

        if not parsed_data.get("time"):
            return

        # calculating progress and preparing status data
        timeframe = sum(m*float(t) for m, t in zip([3600, 60, 1], parsed_data["time"].split(":")))
        progress = ( timeframe / self.duration ) * 100
        status_data = {
            "task_id": self.task_id,
            "task_name": consts.TASK_GENERATE_LOWRES,
            "status": consts.STATE_IN_PROGRESS,
            "progress": round(progress, 2)
        }

        # calling registered status callback
        if self.status_callback: self.status_callback(self.task_id, status_data)


# ------------------- THUMBNAIL TASK ---------------------
async def prepare_thumbnail_task(data):
    task = {}
    for key in ["media_path", "thumbnail_path", "task_id", "share_id", "proxy_share_id"]:
        if not data.get(key):
            return None, "'{}' not provided".format(data[key])

    # adding basic parameters
    task["task_name"] = consts.TASK_GENERATE_THUMBNAIL
    task["task_id"] = data["task_id"]
    task["share_id"] = data["share_id"]
    task["proxy_share_id"] = data["proxy_share_id"]

    # preparing share absolute path
    media_share = await rcl.get_share_details(task["share_id"])
    if media_share is None:
        return None, "failed to retrieve media storage '{}' details from request server.".format(data["share_id"])

    task["media_uri"] = data["media_path"]
    task["media_path"] = urv.get_abs_path_from_uri_for_share(data["media_path"], media_share)

    # preparing thumbnail absoulte path
    proxy_share = await rcl.get_share_details(task["proxy_share_id"])
    if proxy_share is None:
        return None, "failed to retrieve proxy storage '{}' details from request server.".format(data["proxy_share_id"])

    task["thumbnail_uri"] = data["thumbnail_path"]
    task["thumbnail_path"] = urv.get_abs_path_from_uri_for_share(data["thumbnail_path"], proxy_share)

    return task, ""


class ThumbnailTask:
    """
    TODO:
        * validating media file
        * error reporting
    """

    def __init__(self, task_id, media_path, thumbnail_path, params=None):
        # task info
        self.task_id = task_id
        self.name = consts.TASK_GENERATE_THUMBNAIL

        # media and lowres path
        self.media_path = media_path
        self.thumbnail_path = thumbnail_path

        # command parameters to generate thumbnail
        self.params = {
            "scale": "320:240"
        }

        # callbacks to communicate command status
        self.status_callback = None

        # parsing and setting command params
        self.parse_params(params)

    def parse_params(self, params):
        if not params:
            return

        # validating and setting generated thumbnail scale
        if not params.get("scale") or re.search(r"^[0-9]:[0-9]$", params["scale"]) is None:
            raise ValueError("ThumbnailTask(task_id={})< invalid command parameter 'scale' value provided >"
                .format(self.task_id)) 
        self.params["scale"] = params["scale"]

    def generate_command(self):
        cmd = [ FFMPEG_PATH, "-y", "-hide_banner", "-i", self.media_path, "-vframes", "1"]
        for key, value in self.params.items():
            if key == "scale":
                cmd.extend(["-s", value])
        cmd.append(self.thumbnail_path)
        return cmd

    async def run(self, loop, status_callback=None, exit_callback=None):
        # setting status callbacks 
        self.status_callback = status_callback if callable(status_callback) else lambda _id, d: logger.debug(d)

        # getting command
        command = self.generate_command()

        # sending inprogress status
        status_data = {
            "task_id": self.task_id,
            "task_name": consts.TASK_GENERATE_THUMBNAIL,
            "status": consts.STATE_IN_PROGRESS,
            "progress": round(0.0, 2)
        }
        # calling registered status callback
        if self.status_callback: self.status_callback(self.task_id, status_data)

        # configuring process with event loop
        future = asyncio.Future(loop=loop)
        factory = functools.partial(ProcessHandler, future, self, task_id=self.task_id)
        proc = loop.subprocess_exec(factory, *command, stdin=None)

        logger.info("[ThumbnailTask.run] [{}]: Generating thumbnail with command '{}'.".format(self.task_id, command))
        transport = None
        try:
            transport,_ = await proc
            logger.debug("[ThumbnailTask.run] [{}]: Waiting for process to complete.".format(self.task_id))
            await future
        finally:
            if transport: transport.close()

        # processing exit code
        status = False
        status_data = {"task_id": self.task_id, "task_name": consts.TASK_GENERATE_THUMBNAIL}
        exit_code = future.result()
        if exit_code == 0:
            status = True
            status_data["status"] = consts.STATE_COMPLETED
            status_data["progress"] = 100.0
            logger.info("[ThumbnailTask.run] [{}]: Thumbnail generated successfully.".format(self.task_id))
        else:
            status_data["status"] = consts.STATE_FAILED
            status_data["progress"] = 0.0
            logger.info("[ThumbnailTask.run] [{}]: Failed to generate thumbnail.".format(self.task_id))

        # calling registered status callback
        if self.status_callback: self.status_callback(self.task_id, status_data)

        # calling registered exit callback
        if exit_callback: exit_callback(self.task_id, exit_code)
        return status

    def out_data(self, data):
        logger.debug("[ThumbnailTask.out_data]: {}".format(data))

    def err_data(self, data):
        logger.debug("[ThumbnailTask.err_data]: {}".format(data))
