import json
import asyncio

from server.task import logger

import server.commons.constants as consts

import server.task.tasks as tasks
import server.task.reqclient as rcl


# Engine to process all tasks
class TaskEngine:

    PRIORITY_HIGHEST = 1
    PRIORITY_DEFAULT = 5
    PRIORITY_LOWEST = 10

    class Task:

        def __init__(self, priority, task):
            self.priority = priority
            self.task = task

        def __lt__(self, other):
            return self.priority < other.priority

        def __gt__(self, other):
            return self.priority > other.priority

        def __eq__(self, other):
            return self.priority == other.priority

    def __init__(self, loop, max_concurrent_tasks=3):
        self.loop = loop

        # task queue to process incoming tasks
        self.__queue = asyncio.PriorityQueue(loop=self.loop)

        # semaphore to run limit max number of concurrent tasks
        self.max_concurrent_tasks = max_concurrent_tasks
        self.__concurrent_slots = asyncio.Semaphore(
            value=self.max_concurrent_tasks,
            loop=self.loop)

    def size(self):
        return self.__queue.qsize()

    async def stop(self):
        logger.info("[TaskEngine.stop]: Requesting TaskEngine to stop.")
        await self.__queue.put(TaskEngine.Task(TaskEngine.PRIORITY_LOWEST, None))
        await self.__queue.join()

    async def submit(self, task, priority=None):
        if priority is None:
            priority = TaskEngine.PRIORITY_DEFAULT

        if priority < TaskEngine.PRIORITY_HIGHEST or priority > TaskEngine.PRIORITY_LOWEST:
            logger.warning("[TaskEngine.submit] [{}]: Setting default priority. Task priority value should be between {} and {}"
                .format(getattr(task, "task_id"), TaskEngine.PRIORITY_LOWEST, TaskEngine.PRIORITY_HIGHEST))
            priority = TaskEngine.PRIORITY_DEFAULT

        await self.__queue.put(TaskEngine.Task(priority, task))
        logger.info("[TaskEngine.submit]: New task '{}' pushed to task queue.".format(task))

    def handle_task_status(self, task_id, status_data):
        self.loop.create_task(rcl.send_status_to_reqserver(task_id, status_data))

    async def _execute(self, task):
        try:
            if task["task_name"] == consts.TASK_GENERATE_THUMBNAIL:
                thumbnail_task = tasks.ThumbnailTask(
                    task["task_id"],
                    task["media_path"],
                    task["thumbnail_path"]
                )
                status = await thumbnail_task.run(self.loop, status_callback=self.handle_task_status)
                logger.info("[TaskEngine] [{}]: Thumbnail task exited with status '{}'"
                    .format(task["task_id"], status))

            elif task["task_name"] == consts.TASK_GENERATE_LOWRES:
                lowres_task = tasks.LowresTask(
                    task["task_id"],
                    task["media_path"],
                    task["lowres_path"]
                )
                status = await lowres_task.run(self.loop, status_callback=self.handle_task_status)
                logger.info("[TaskEngine] [{}]: Lowres task exited with status '{}'"
                    .format(task["task_id"], status))

            # setting task done for queue to avoid blocking queue.join()
            self.__queue.task_done()
        except Exception as ex:
            logger.error("[TaskEngine._execute]: Error '{}' while executing task '{}'."
                .format(ex, task.get("task_id")))

        # releasing slot for other tasks
        self.__concurrent_slots.release()
        return True

    async def run(self):
        while True:
            try:
                logger.info("[TaskEngine.run]: Waiting for new tasks...")
                task = await self.__queue.get()
                task = task.task
                if task is None:
                    logger.info("[TaskEngine.run]: Abort request received hence terminating TaskEngine.")
                    self.__queue.task_done()
                    break

                # acquiring slot to execute task and control max parallel concurrent tasks
                await self.__concurrent_slots.acquire()

                # executing task
                logger.info("[TaskEngine.run]: Executing Task '{}'.".format(task))
                self.loop.create_task(self._execute(task))

            except Exception as ex:
                logger.error("[TaskEngine.run]: Error '{}' while processing task.".format(ex))

        logger.info("[TaskEngine.run]: TaskEngine stopped.")
        return True