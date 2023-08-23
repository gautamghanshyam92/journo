"""
This is the main hosting service to receive and process all user requests
"""
import sys
import asyncio
from aiohttp import web as aioweb
import aiohttp_jinja2
import jinja2

import motor.motor_asyncio as amotor

# importing logger
from server.request import logger
from server.commons import session

# app imports
import server.commons.constants as consts
import server.config as conf

# importing plugins
import server.request.metadata as mdatasrv
import server.request.shares as sharesrv
import server.request.tasks as tasksrv
import server.request.stories as storysrv
import server.request.agencies as agencysrv
import server.request.users as usersrv
import server.request.journoweb as websrv
import server.request.nrcs as nrcssrv
import server.request.streams as streamsrv
# NEWS FEEDS TODO
import server.request.feeds as feedsrv

# ------------ Service setup --------------

# adding routes from all plugins to app
PLUGINS_TO_INSTALL = [mdatasrv, sharesrv, tasksrv, storysrv, agencysrv, usersrv, feedsrv, nrcssrv, websrv, streamsrv]


async def setup_plugins(webapp):
    for plugin in PLUGINS_TO_INSTALL:
        # setting up plugins if requested
        if hasattr(plugin, "initial_setup") and callable(plugin.initial_setup):
            if not await plugin.initial_setup(webapp):
                logger.error("[Main] [setup_plugins]: Failed to setup '{}' plugin.".format(plugin.__name__))
                return False
    return True


def add_plugin_routes(webapp):
    for plugin in PLUGINS_TO_INSTALL:
        # validating plugin
        if not hasattr(plugin, "routes"):
            continue

        if not isinstance(plugin.routes, aioweb.RouteTableDef):
            raise TypeError("plugin '{}' routes must be of type 'aiohttp.web.RouteTableDef'".format(plugin.__name__))

        # adding plugin routes to application
        webapp.add_routes(plugin.routes)

    logger.info("[Main] [LoadPlugins]: Total '{}' routes are added form '{}' plugins."
                .format(len(webapp.router._resources), len(PLUGINS_TO_INSTALL)))


# setting up application
async def setup_app(webapp):
    # initializing db
    client = amotor.AsyncIOMotorClient()
    webapp["client"] = client
    db = client[consts.DB_NAME]
    webapp["db"] = db
    logger.info("[Main] [Setup]: Database setup is done.")

    logger.info("[Main] [Setup]: Application setup done.")
    return True


# shutting down server
async def shutdown_app(webapp, event_loop=None):
    # closing database connection
    client = webapp.get("client", None)
    if client:
        client.close()
    logger.info("[Main] [Shutdown]: Database connection closed.")

    # closing aiohttp client session
    if session and not session.closed:
        await session.close()

    # fetching all pending tasks
    tasks = [task for task in asyncio.Task.all_tasks() if task is not
             asyncio.Task.current_task()]

    # waiting for tasks to complete
    if len(tasks):
        logger.info("[Main] [Shutdown]: Waiting 5 seconds for pending tasks to complete. Then cancelling them.")
        await asyncio.wait(asyncio.Task.all_tasks(), timeout=5)

        # cancelling all pending tasks
        logger.info("[Main] [Shutdown]: Cancelling '{}' tasks.".format(len(tasks)))
        for task in tasks:
            logger.info("Cancelling task '{}'".format(task))
            task.cancel()

        await asyncio.gather(*tasks)

    if event_loop:
        event_loop.stop()
    logger.info("[Main] [Shutdown]: Request Server Terminated.")


def add_web_static_routes(webapp):
    static_routes = websrv.get_static_routes()
    if not static_routes:
        return False
    webapp.add_routes(static_routes)
    return True


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

    # setting up plugins
    if not loop.run_until_complete(setup_plugins(app)):
        logger.error("[Main]: Failed to setup plugins. Hence terminating")
        loop.run_until_complete(shutdown_app(app, loop))
        sys.exit(1)

    # adding routes
    add_plugin_routes(app)

    # adding static routes to host Journo Web
    if not add_web_static_routes(app):
        logger.error("[Main]: Failed to add Journo Web static paths.")
        loop.run_until_complete(shutdown_app(app, loop))
        sys.exit(1)

    aiohttp_jinja2.setup(app,
                         loader=jinja2.FileSystemLoader(consts.TEMPLATE_BASE_FOLDER))
    # starting app
    aioweb.run_app(app, host=conf.REQUEST_SERVER_IP, port=conf.REQUEST_SERVER_PORT)
