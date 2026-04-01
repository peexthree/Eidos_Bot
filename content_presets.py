import json
import os

# =============================================================================
# STANDARD: CONTENT STRUCTURE
# =============================================================================
# TABLE: content
# FIELDS:
#   - type: 'protocol' (Sync), 'signal' (Sync), 'event' (Raid), 'advice' (Raid)
#   - path: 'money', 'mind', 'tech', 'general' (for Sync), 'raid_general' (for Raid)
#   - level: 1-4 (Sync), 1-3 (Raid Depth Tiers)
#   - text: Content string
#
# RULES:
#   - Raid texts (events/advice) MUST have path='raid_general'.
#   - Protocol texts should generally follow the path theme.
# =============================================================================

# Define path to Data Directory
DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')

# =============================================================================
# CONTENT DATA
# =============================================================================
CONTENT_JSON_PATH = os.path.join(DATA_DIR, 'content.json')
CONTENT_DATA = {}

if os.path.exists(CONTENT_JSON_PATH):
    try:
        with open(CONTENT_JSON_PATH, 'r', encoding='utf-8') as f:
            _c_data = json.load(f)
            # JSON keys are always strings, convert back to int for logic compatibility
            for k, v in _c_data.items():
                if k.isdigit():
                    CONTENT_DATA[int(k)] = v
                else:
                    CONTENT_DATA[k] = v
    except Exception as e:
        print(f"Error loading content.json: {e}")
else:
    print(f"Warning: {CONTENT_JSON_PATH} not found.")

# =============================================================================
# VILLAINS DATA
# =============================================================================
VILLAINS_JSON_PATH = os.path.join(DATA_DIR, 'villains.json')

VILLAINS_DATA = []
OLD_VILLAINS_NAMES = ()

if os.path.exists(VILLAINS_JSON_PATH):
    try:
        with open(VILLAINS_JSON_PATH, 'r', encoding='utf-8') as f:
            _v_data = json.load(f)
        VILLAINS_DATA = _v_data.get('villains', [])
        OLD_VILLAINS_NAMES = tuple(_v_data.get('old_names', []))
    except Exception as e:
        print(f"Error loading villains.json: {e}")
else:
    print(f"Warning: {VILLAINS_JSON_PATH} not found.")
