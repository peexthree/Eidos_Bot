import queue
import threading
import logging

TASK_QUEUE = queue.Queue()

def task_worker(bot):
    print("/// TASK WORKER STARTED", flush=True)
    while True:
        try:
            task = TASK_QUEUE.get()
            if task is None: break

            func, args, kwargs = task
            try:
                func(bot, *args, **kwargs)
            except Exception as e:
                import traceback; print(f"/// TASK EXECUTION ERROR: {e}", flush=True); traceback.print_exc()
            finally:
                TASK_QUEUE.task_done()
        except Exception as e:
            import traceback; print(f"/// TASK WORKER CRITICAL ERROR: {e}", flush=True); traceback.print_exc()

def start_worker(bot):
    t = threading.Thread(target=task_worker, args=(bot,), daemon=True)
    t.start()
    return t

def enqueue_task(func, *args, **kwargs):
    TASK_QUEUE.put((func, args, kwargs))
