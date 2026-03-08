filepath = 'modules/services/ai_worker.py'
with open(filepath, 'r') as f:
    content = f.read()

content = content.replace("import sentry_sdk\nimport logging; print(f\"[AI WORKER] FATAL ERROR for UID {uid}: {str(e)}\", flush=True); traceback.print_exc()", "        import sentry_sdk\n        import logging\n        logging.error(f\"[AI WORKER] FATAL ERROR for UID {uid}: {str(e)}\", exc_info=True)\n        sentry_sdk.capture_exception(e)")

with open(filepath, 'w') as f:
    f.write(content)
