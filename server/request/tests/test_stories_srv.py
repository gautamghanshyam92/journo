import sys
import asyncio

sys.path.append("../../..")
import server.commons.utils as utils
from server.commons import session


async def get_story_info(story_id):
    reqsrv_url = utils.get_request_server_url("stories/{}".format(story_id))
    storyinfo = await session.get(reqsrv_url)
    storyinfo = await storyinfo.json()
    print("get_story_info(): result: ", storyinfo)
    return storyinfo if storyinfo else None


async def get_all_stories():
    reqsrv_url = utils.get_request_server_url("stories")
    stories = await session.get(reqsrv_url)
    stories = await stories.json()
    print("get_all_stories(): result: ", stories)
    return stories if stories else None


async def main(loop):
    # retrieving all stories
    stories = await get_all_stories()
    if stories is None:
        print("/stories GET FAILED.")
        return False
    print("/stories GET PASSED")

    # retrieving single story info
    story_id = None
    if stories and stories.get("stories"):
        story_id = stories["stories"][0].get("_id")
        
    if story_id:
        storyinfo = await get_story_info(story_id)
        if storyinfo is None:
            print("/stories/{story_id} GET FAILED.")
            return False
        print("/stories/{story_id} GET PASSED.")

    return True


async def cleanup():
    await session.close()


loop = asyncio.get_event_loop()
try:
    # executing test cases
    loop.run_until_complete(main(loop))

    # cleaning up
    loop.run_until_complete(cleanup())
finally:
    loop.close()