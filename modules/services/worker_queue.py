import queue
import threading
import sys
import traceback

# ABSOLUTE SINGLETON QUEUE
if not hasattr(sys.modules[__name__], 'TASK_QUEUE'):
    sys.modules[__name__].TASK_QUEUE = queue.Queue()

def task_worker(bot):
    print("/// TASK WORKER STARTED", flush=True)
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
                print(f"/// TASK EXECUTION ERROR: {e}", flush=True)
                traceback.print_exc()
            finally:
                q.task_done()
        except Exception as e:
            print(f"/// TASK WORKER CRITICAL ERROR: {e}", flush=True)
            traceback.print_exc()

def start_worker(bot):
    t = threading.Thread(target=task_worker, args=(bot,), daemon=True)
    t.start()
    return t

def enqueue_task(func, *args, **kwargs):
    q = sys.modules[__name__].TASK_QUEUE
    q.put((func, args, kwargs))
    print(f"/// QUEUE: Added {func.__name__}. Size: {q.qsize()}", flush=True)
