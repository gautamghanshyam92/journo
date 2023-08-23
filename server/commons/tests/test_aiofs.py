#!/usr/bin/python3.6
import sys
import time
import asyncio
if "../../.." not in sys.path:
    sys.path.append("../../..")

from server.commons.aiofs import AioFsPath


def test_main(delay=None, after_count=2):
    count = 0
    loop = asyncio.get_event_loop()

    base_url = "ftp://ghanshyam:worklab@localhost/{}"
    for filename in ["file_1.mp4", "file_2.mp4", "file_3.mp4", "file_4.mp4"]:
        url = base_url.format(filename)
        path = AioFsPath(url)
        print("url: {}".format(url))
        for func_name in ["exists", "isfile", "isdir", "getsize", "getmtime", "stat"]:
            if not hasattr(path, func_name):
                print("Method '{}' not found for path")
                continue
            res = loop.run_until_complete(getattr(path, func_name)())
            print("[{}]: {}".format(func_name, res))
        print("--" * 30)

        # to test connection timeout behaviour
        count += 1
        if delay and (after_count % count == 0):
            time.sleep(delay)


if __name__ == "__main__":
    """
    if len(sys.argv) != 2:
        print("USAGE: ./test_aiofs.py <path url>")
        sys.exit(1)

    path = sys.argv[1]
    """
    test_main()
