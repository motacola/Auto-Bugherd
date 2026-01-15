import requests
import os
import logging
from requests.exceptions import RequestException
from tenacity import retry, stop_after_attempt, wait_exponential

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BugHerdClient:
    def __init__(self, api_key=None, requester_email=None):
        self.api_key = api_key or os.getenv("BUGHERD_API_KEY")
        self.base_url = "https://www.bugherd.com/api/v2"
        self.requester_email = requester_email or os.getenv("BUGHERD_REQUESTER_EMAIL", "qa-auto@servicescalers.com")

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def create_ticket(self, project_id, description, page_url=None):
        if not self.api_key:
            logger.error("❌ BugHerd API Key missing. Skipping ticket creation.")
            return None

        url = f"{self.base_url}/projects/{project_id}/tasks.json"
        payload = {
            "task": {
                "description": description,
                "requester_email": self.requester_email,
                "priority": "normal",
                "metadata": {
                    "url": page_url
                }
            }
        }
        
        try:
            response = requests.post(url, auth=(self.api_key, 'x'), json=payload)
            if response.status_code == 201:
                logger.info(f"✅ Ticket created successfully in project {project_id}")
                return response.json()
            else:
                logger.error(f"❌ Failed to create ticket: {response.text}")
                return None
        except RequestException as e:
            logger.error(f"❌ Error connecting to BugHerd: {e}")
            raise

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def create_ticket_comment(self, project_id, task_id, text):
        if not self.api_key:
            logger.error("❌ BugHerd API Key missing. Skipping comment creation.")
            return None

        url = f"{self.base_url}/projects/{project_id}/tasks/{task_id}/comments.json"
        payload = {"comment": {"text": text}}
        
        try:
            response = requests.post(url, auth=(self.api_key, 'x'), json=payload)
            if response.status_code == 201:
                logger.info(f"✅ Comment added to task {task_id}")
                return response.json()
            else:
                logger.error(f"❌ Failed to add comment: {response.text}")
                return None
        except RequestException as e:
            logger.error(f"❌ Error adding comment: {e}")
            raise
