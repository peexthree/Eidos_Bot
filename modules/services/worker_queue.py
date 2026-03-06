import queue
import threading
import logging

TASK_QUEUE = queue.Queue()

def task_worker(bot):
    logging.info("/// TASK WORKER STARTED")
    while True:
        try:
            task = TASK_QUEUE.get()
            if task is None: break

            func, args, kwargs = task
            try:
                func(bot, *args, **kwargs)
            except Exception as e:
                logging.error(f"/// TASK EXECUTION ERROR: {e}", exc_info=True)
            finally:
                TASK_QUEUE.task_done()
        except Exception as e:
            logging.error(f"/// TASK WORKER CRITICAL ERROR: {e}", exc_info=True)

def start_worker(bot):
    t = threading.Thread(target=task_worker, args=(bot,), daemon=True)
    t.start()
    return t

def enqueue_task(func, *args, **kwargs):
    TASK_QUEUE.put((func, args, kwargs))
