import os
import sys
import uuid
import json
import requests

# ----------------------------------------------------------------------------
SERVER_URL = "http://localhost:7798/tasks"

MEDIA_PATH = "/home/ghanshyam/Videos/sample_videos/coca_cola_1080p.mp4"
PROXY_PATH = "/home/ghanshyam/Videos/sample_videos/proxy"
NUM_OF_THUMBNAILS = 0
NUM_OF_LOWRES = 1
# ----------------------------------------------------------------------------

LOWRES_NAME = "{name}.lowres.mp4"
THUMBNAIL_NAME = "{name}.thumbnail.png"

# posting lowres tasks
for i in range(NUM_OF_LOWRES):
    task_id = uuid.uuid4()
    lowres_path = os.path.join(PROXY_PATH, LOWRES_NAME.format(name=task_id))
    
    data = {
        "task_id": "{}".format(task_id),
        "media_path": MEDIA_PATH,
        "lowres_path": lowres_path,
        "task_name": "generate_lowres"
    }

    res = requests.post(SERVER_URL, data=json.dumps(data))
    if not res.ok:
        print("[LowresTask]: Failed to post task '{}'.".format(task_id))
        sys.exit(1)

    res = res.json()
    if res["ok"]:
        print("[LowresTask]: Task '{}' posted successfully.".format(task_id))
    else:
        print("[LowresTask]: Server ran into error hence task post failed.")
        sys.exit(1)

# posting thumbnail tasks
for i in range(NUM_OF_THUMBNAILS):
    task_id = uuid.uuid4()
    thumbnail_path = os.path.join(PROXY_PATH, THUMBNAIL_NAME.format(name=task_id))
    
    data = {
        "task_id": "{}".format(task_id),
        "media_path": MEDIA_PATH,
        "thumbnail_path": thumbnail_path,
        "task_name": "generate_thumbnail"
    }

    res = requests.post(SERVER_URL, data=json.dumps(data))
    if not res.ok:
        print("[ThumbnailTask]: Failed to post task '{}'.".format(task_id))
        sys.exit(1)

    res = res.json()
    if res["ok"]:
        print("[ThumbnailTask]: Task '{}' posted successfully.".format(task_id))
    else:
        print("[ThumbnailTask]: Server ran into error hence task post failed.")
        sys.exit(1)

print("Done posting all tasks.")
