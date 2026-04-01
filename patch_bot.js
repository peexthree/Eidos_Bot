const fs = require('fs');
const file = 'bot.py';
let content = fs.readFileSync(file, 'utf8');

const twaSyncLogic = `
@app.route('/api/twa/sync', methods=['POST'])
@require_telegram_auth
def twa_sync():
    data = flask.request.json or {}
    uid = data.get('uid')
    if not uid:
        return flask.jsonify({"error": "Missing uid"}), 400

    try:
        # Clear redis cache for this specific user so next text interaction loads fresh data
        cache_db.clear_cache(uid)

        # Flush the background stats (which could be pending processing)
        flush_stats()

        return flask.jsonify({"success": True, "message": "Context synchronized"})
    except Exception as e:
        traceback.print_exc()
        return flask.jsonify({"error": "Sync Failed"}), 500
`;

// Insert the code before the @app.route('/api/leaderboard', methods=['GET'])
const parts = content.split("@app.route('/api/leaderboard', methods=['GET'])");
fs.writeFileSync(file, parts[0] + twaSyncLogic + "\n@app.route('/api/leaderboard', methods=['GET'])" + parts[1]);
console.log("Patched bot.py");
