# creating aiohttp ClientSession
import aiohttp
session = None
if session is None or session.closed:
    print("[commons.__init__]: aiohttp.ClientSession object 'session' initialized.")
    session = aiohttp.ClientSession()
