import os
import re

# 1. Patch ai_worker.py
filepath = 'modules/services/ai_worker.py'
with open(filepath, 'r') as f:
    content = f.read()

# Force Free Model
content = re.sub(
    r'OPENROUTER_MODEL = os\.environ\.get\("OPENROUTER_MODEL", ".*"\)',
    'OPENROUTER_MODEL = "google/gemma-3-27b-it:free"',
    content
)

# Add sentry_sdk import if missing
if 'import sentry_sdk' not in content:
    content = content.replace('import traceback', 'import traceback\nimport sentry_sdk\nimport logging')

# Replace tracebacks/prints with logging+sentry
content = content.replace(
    'print(f"/// AI WORKER CRITICAL ERROR: {e}", flush=True)',
    'logging.error(f"/// AI WORKER CRITICAL ERROR: {e}", exc_info=True)\n            sentry_sdk.capture_exception(e)'
)

content = content.replace(
    'print(f"/// AI WORKER VOICE ERROR: {e}", flush=True)',
    'logging.error(f"/// AI WORKER VOICE ERROR: {e}", exc_info=True)\n            sentry_sdk.capture_exception(e)'
)

content = content.replace(
    'print(f"/// AI WORKER DB ERROR: {e}", flush=True)',
    'logging.error(f"/// AI WORKER DB ERROR: {e}", exc_info=True)\n            sentry_sdk.capture_exception(e)'
)

content = content.replace(
    'print(f"/// AI WORKER DOSSIER ERROR: {e}", flush=True)',
    'logging.error(f"/// AI WORKER DOSSIER ERROR: {e}", exc_info=True)\n            sentry_sdk.capture_exception(e)'
)

with open(filepath, 'w') as f:
    f.write(content)

# 2. Patch worker_queue.py
filepath = 'modules/services/worker_queue.py'
with open(filepath, 'r') as f:
    content = f.read()

if 'import sentry_sdk' not in content:
    content = content.replace('import traceback', 'import traceback\nimport sentry_sdk\nimport logging')

content = content.replace(
    'print(f"/// TASK EXECUTION ERROR: {e}", flush=True)\n                traceback.print_exc()',
    'logging.error(f"/// TASK EXECUTION ERROR: {e}", exc_info=True)\n                sentry_sdk.capture_exception(e)'
)

content = content.replace(
    'print(f"/// TASK WORKER CRITICAL ERROR: {e}", flush=True)\n            traceback.print_exc()',
    'logging.error(f"/// TASK WORKER CRITICAL ERROR: {e}", exc_info=True)\n            sentry_sdk.capture_exception(e)'
)

with open(filepath, 'w') as f:
    f.write(content)

print("Patch complete.")
