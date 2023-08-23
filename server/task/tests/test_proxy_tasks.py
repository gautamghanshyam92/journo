import sys
if "../../.." not in sys.path:
    sys.path.append("..")

import asyncio
from server.task import tasks

media_path = "/home/ghanshyam/Videos/sample_videos/coca_cola_1080p.mp4"
lowres_path = "/home/ghanshyam/Videos/sample_videos/coca_cola_1080p.lowres.mp4"
thumbnail_path = "/home/ghanshyam/Videos/sample_videos/coca_cola_1080p.thumbnail.png"


async def test_duration():
    # media duration
    duration = await tasks.get_media_duration(media_path)
    print("DURATION: {}".format(duration))
    status = True if duration else False
    if not status:
        print("test_duration() FAILED.")
    else:
        print("test_duration() PASSED.")
    return status


async def test_lowres_task(loop):
    # testing lowres generation
    lowres_task = tasks.LowresTask("123", media_path, lowres_path)
    status = await lowres_task.run(loop)
    print("LOWRES TASK STATUS: ", status)
    if not status:
        print("test_lowres_task() FAILED.")
    else:
        print("test_lowres_task() PASSED.")
    return status


async def test_thumbnail_task(loop):
    # testing thumbnail generation
    thumbnail_task = tasks.ThumbnailTask("456", media_path, thumbnail_path)
    status = await thumbnail_task.run(loop)
    print("THUMBNAIL TASK STATUS: ", status)
    if not status:
        print("test_thumbnail_task() FAILED.")
    else:
        print("test_thumbnail_task() PASSED.")
    return status


async def main(loop):
    tasks = [
        test_duration(),
        test_lowres_task(loop),
        test_thumbnail_task(loop)
    ]

    await asyncio.wait(tasks)

loop = asyncio.get_event_loop()
try:
    loop.run_until_complete(main(loop))
finally:
    loop.close()