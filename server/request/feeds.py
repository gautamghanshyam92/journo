"""
 This module is responsble for registering of websockets
 and sending feeds to the registered clients
"""

import asyncio
import json

from aiohttp import web as aioweb

# importing logger
from server.request import logger
from collections import defaultdict

# shares all rest api routes are added to this table
routes = aioweb.RouteTableDef()


async def initial_setup(app):
    """
     Initial setup of the feed server
    """
    app['feed_server'] = FeedServer(app)
    logger.info("Feeds [Setup] Setup completed")
    return True


################ Process Feeds ####################

class FeedServer(object):
    """
     Feed Server Responsible for Publishing feeds
    """
    def __init__(self, app):
        """
         Setting up of the feed server
        """
        self.task = None
        self.lock = asyncio.Lock()
        self.feeds = asyncio.Queue()
        self.websockets = defaultdict(set)  # by default all keys will have a value of a set
        app.on_startup.append(self.start_feed_task)
        app.on_cleanup.append(self.stop_feed_task)
        pass


    async def start_feed_task(self, app):
        """
         Background feed management task.
         Started upon the start of the app
        """
        self.task = app.loop.create_task(self.process_feeds())


    async def stop_feed_task(self, app):
        """
         Stop the task.
        """
        logger.info("stop_feed_task: Stopping feed task server")
        if self.task:
            await self.feeds.put(None)
            self.task.cancel()
            await self.task


    async def push(self, feed):
        """
         Inserts the feed into the feed queue
        """
        await self.feeds.put(feed)


    def register(self, user_id, ws):
        """
         Register the user_id and the websocket.
        """
        self.websockets[user_id].add(ws)


    async def unregister(self, user_id, ws):
        """
         Unregister the user_id related websocket
        """
        async with self.lock:
            if user_id in self.websockets:
                if ws in self.websockets[user_id]:
                    self.websockets[user_id].remove(ws)
                if not self.websockets[user_id]:
                    del self.websockets[user_id]


    async def process_feeds(self):
        """
         Function to process the feeds
         Fetch them and send the feed to the clients
        """
        logger.info("[process_feeds] Processing Incoming feeds")
        while True:
            feed = await self.feeds.get()
            if feed is None:
                # To stop processing of the feeds.
                logger.info("[process_feeds] Recieved None, stopping feeds processing")
                break
            async with self.lock:
                for user in self.websockets.keys():
                    for ws in self.websockets.get(user, []):
                        try:
                            await ws.send_str(feed)
                        except Exception as ex:
                            logger.info("process feeds Exception client :{}".format(ex))
        return


################# Routes ################
@routes.get('/ws')
async def get_websocket(request):
    """
     Get the websocket connection
     Registeration
    """

    params = request.rel_url.query
    user_id = params['user_id']

    ws = aioweb.WebSocketResponse()
    await ws.prepare(request)
    request.app['feed_server'].register(user_id, ws)
    try:
        async for msg in ws:
            pass
    except Exception as ex:
        print(ex)
    finally:
        request.app['feed_server'].unregister(user_id, ws)
    return ws


@routes.post('/feeds')
async def add_feed(request):
    """
     Add the feed to the feed queue
    """
    feed = await request.json()
    if feed:
        await request.app['feed_server'].push(json.dumps(feed))
    return aioweb.Response(text="Feed Added!")

