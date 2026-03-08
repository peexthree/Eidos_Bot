import queue
import threading
import sys
import traceback
import sentry_sdk
import logging
import os

# ABSOLUTE SINGLETON STATE
if not hasattr(sys.modules[__name__], 'TASK_QUEUE'):
    sys.modules[__name__].TASK_QUEUE = queue.Queue()
if not hasattr(sys.modules[__name__], 'WORKER_THREAD'):
    sys.modules[__name__].WORKER_THREAD = None

def task_worker(bot):
    print(f"/// TASK WORKER STARTED IN PID {os.getpid()}", flush=True)
    q = sys.modules[__name__].TASK_QUEUE
    while True:
        try:
            task = q.get()
            if task is None: break

            func, args, kwargs = task
            try:
                print(f"/// WORKER: Executing {func.__name__} with args: {args}", flush=True)
                func(bot, *args, **kwargs)
            except Exception as e:
                logging.error(f"/// TASK EXECUTION ERROR: {e}", exc_info=True)
                sentry_sdk.capture_exception(e)
            finally:
                q.task_done()
        except Exception as e:
            logging.error(f"/// TASK WORKER CRITICAL ERROR: {e}", exc_info=True)
            sentry_sdk.capture_exception(e)

def start_worker(bot):
    t = threading.Thread(target=task_worker, args=(bot,), daemon=True)
    t.start()
    sys.modules[__name__].WORKER_THREAD = t
    return t

def enqueue_task(func, *args, **kwargs):
    q = sys.modules[__name__].TASK_QUEUE
    q.put((func, args, kwargs))
    print(f"/// QUEUE: Added {func.__name__}. Size: {q.qsize()}", flush=True)

    # SELF-HEALING MECHANISM (Resurrect thread if killed by Gunicorn fork)
    current_thread = sys.modules[__name__].WORKER_THREAD
    if current_thread is None or not current_thread.is_alive():
        print(f"/// WARNING: Worker thread is dead in PID {os.getpid()}. Resurrecting...", flush=True)
        from modules.bot_instance import bot
        sys.modules[__name__].WORKER_THREAD = start_worker(bot)
