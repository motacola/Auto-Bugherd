from flask import Flask, request, jsonify
import sys
import os
import threading
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Add src to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from engine import BugHerdEngine

app = Flask(__name__)

# Initialize engine lazily to avoid startup crashes
_engine = None

def get_engine():
    global _engine
    if _engine is None:
        _engine = BugHerdEngine()
    return _engine

@app.route('/webhook', methods=['POST'])
def handle_bugherd_webhook():
    data = request.json
    if not data:
        return jsonify({"error": "No payload"}), 400

    event = data.get('event')
    task = data.get('task', {})
    task_id = task.get('id')
    # Support both project_id and projectId common naming conventions
    project_id = data.get('project_id') or data.get('projectId')
    
    # BugHerd tasks often contain the URL in metadata
    target_url = task.get('metadata', {}).get('url')

    logging.info(f"Received BugHerd Webhook: {event} (Task #{task_id} in Project {project_id})")

    if event in ['task_create', 'task_update']:
        if target_url:
            threading.Thread(target=process_task_qa, args=(target_url, task_id, project_id)).start()
            return jsonify({"status": "processing", "task_id": task_id}), 202
        else:
            logging.info(f"Skipping task #{task_id}: No URL found in task metadata.")
            return jsonify({"status": "ignored", "reason": "No URL in task"}), 200

    return jsonify({"status": "ignored", "event": event}), 200

def process_task_qa(url, task_id, project_id):
    try:
        logging.info(f"Starting automated QA for {url}...")
        engine = get_engine()
        success = engine.run_qa_ad_hoc(url)
        
        status_msg = "✅ Automated QA check passed for this URL." if success else "⚠️ Automated QA check found discrepancies. Please review."
        engine.bh_client.create_ticket_comment(project_id, task_id, status_msg)
        logging.info(f"Finished QA for {url}. Result: {'Success' if success else 'Issues Found'}")
    except Exception as e:
        logging.error(f"Error processing QA for task #{task_id}: {e}")

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    logging.info(f"BugHerd Webhook Listener starting on port {port}...")
    app.run(host='0.0.0.0', port=port)
