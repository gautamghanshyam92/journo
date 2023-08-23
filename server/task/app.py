#
#    * communicate back to caller
#

import sys
import asyncio
from aiohttp import web as aioweb

from server.task import logger
import server.commons.constants as consts
import server.config as conf
import server.commons.utils as utils
from server.commons import session

import server.task.tasks as tasks
from server.task.engine import TaskEngine

# all path exposed by service
routes = aioweb.RouteTableDef()

# api's to interact with server
@routes.post("/tasks")
async def create_new_task(request):
    engine = request.app["engine"]
    task = {}
    priority = TaskEngine.PRIORITY_DEFAULT

    data = await request.json()

    if not data or not all([bool(data.get(key)) for key in ["task_name", "task_id"]]):
        logger.error("[/tasks] [POST]: invalid task information provided.")
        return utils.get_http_error("invalid task information provided")

    if data["task_name"] == consts.TASK_GENERATE_THUMBNAIL:
        # preparing thumbnail task
        task, err_msg = await tasks.prepare_thumbnail_task(data)
        if not task:
            logger.error("[/tasks] [POST]: {}".format(err_msg))
            return utils.get_http_error(err_msg)
        priority -= 1

    elif data["task_name"] == consts.TASK_GENERATE_LOWRES:
        # preparing lowres task
        task, err_msg = await tasks.prepare_lowres_task(data)
        if not task:
            logger.error("[/tasks] [POST: {}".format(err_msg))
            return utils.get_http_error(err_msg)

    if task:
        logger.info("[/tasks] [POST]: Submitting task '{}' to TaskEngine.".format(task))
        await engine.submit(task, priority)
        return aioweb.json_response({"ok": True})

    return aioweb.json_response({"ok": False})


async def setup_app(app):
    logger.info("Setting up application")
    return True


async def shutdown_app(app, loop=None):
    logger.info("[Main] [Shutdown]: Shutting down application.")
    # stopping task engine
    engine = app.get("engine", None)
    if engine is not None:
        await engine.stop()

    # closing request server client session
    if session and not session.closed:
        await session.close()

    logger.info("[Main] [Shutdown]: Waiting 10 seconds for pending tasks to complete. Then cancelling them.")
    # waiting for tasks to complete
    await asyncio.wait(asyncio.Task.all_tasks(), timeout=10)

    # cancelling all tasks
    pending_tasks = [task for task in asyncio.Task.all_tasks() if task is not
                     asyncio.Task.current_task()]

    logger.info("[Main] [Shutdown]: Cancelling '{}' tasks.".format(len(pending_tasks)))
    for task in pending_tasks:
        logger.info("Cancelling task '{}'".format(task))
        task.cancel()

    await asyncio.gather(*pending_tasks)
    logger.info("[Main] [Shutdown]: All tasks are cancelled.")

    if loop:
        loop.stop()


if __name__ == "__main__":

    # main event loop
    loop = asyncio.get_event_loop()

    # web app
    app = aioweb.Application()

    # adding shutdown handler
    app.on_shutdown.append(shutdown_app)

    # setting up db and adding to app
    status = loop.run_until_complete(setup_app(app))
    if not status:
        logger.error("[Main]: Failed to setup application. Hence terminating.")
        loop.run_until_complete(shutdown_app(app, loop))
        sys.exit(1)

    # adding routes
    app.add_routes(routes)

    # registering TaskEngine with event loop
    engine = TaskEngine(loop)
    app["engine"] = engine

    # starting task engine
    loop.create_task(engine.run())

    # starting app
    aioweb.run_app(app, host=conf.TASK_SERVER_IP, port=conf.TASK_SERVER_PORT)