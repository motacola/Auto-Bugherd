from flask import Flask, request, jsonify, abort
import sys
import os
import threading
import logging
from functools import wraps

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add src to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from engine import BugHerdEngine

app = Flask(__name__)

# Security: Load secret from environment
WEBHOOK_SECRET = os.getenv("BUGHERD_WEBHOOK_SECRET")

def require_secret(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if WEBHOOK_SECRET:
            # Check for a custom header like 'X-BugHerd-Secret'
            # Note: User must configure BugHerd to send this header if possible, 
            # or we can use another method if BugHerd supports it.
            # Assuming custom header or query param for simplicity.
            secret = request.headers.get('X-BugHerd-Secret') or request.args.get('secret')
            if secret != WEBHOOK_SECRET:
                logger.warning("Unauthorized webhook attempt rejected.")
                abort(401)
        return f(*args, **kwargs)
    return decorated_function

# Initialize engine lazily
_engine = None
def get_engine():
    global _engine
    if _engine is None:
        _engine = BugHerdEngine()
    return _engine

@app.route('/webhook', methods=['POST'])
@require_secret
def handle_bugherd_webhook():
    data = request.json
    if not data:
        return jsonify({"error": "No payload"}), 400

    event = data.get('event')
    task = data.get('task', {})
    task_id = task.get('id')
    project_id = data.get('project_id') or data.get('projectId')
    target_url = task.get('metadata', {}).get('url')

    logger.info(f"Received Webhook: {event} for Task #{task_id}")

    if event in ['task_create', 'task_update']:
        if target_url:
            threading.Thread(target=process_task_qa, args=(target_url, task_id, project_id)).start()
            return jsonify({"status": "processing", "task_id": task_id}), 202
        else:
            return jsonify({"status": "ignored", "reason": "No URL in task"}), 200

    return jsonify({"status": "ignored"}), 200

def process_task_qa(url, task_id, project_id):
    try:
        engine = get_engine()
        success = engine.run_qa_ad_hoc(url)
        
        status_msg = f"QA Results for {url}:\n"
        status_msg += "✅ Passed" if success else "⚠️ Issues found. See report."
        
        engine.bh_client.create_ticket_comment(project_id, task_id, status_msg)
    except Exception as e:
        logger.error(f"Webhook QA processing failed for task {task_id}: {e}")

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    # Warn if secret is not set
    if not WEBHOOK_SECRET:
        logger.warning("No BUGHERD_WEBHOOK_SECRET set. Webhook listener is UNSECURE.")
    
    app.run(host='0.0.0.0', port=port)
