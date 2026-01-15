import requests
import os
import logging

logger = logging.getLogger(__name__)

class BugHerdClient:
    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv("BUGHERD_API_KEY")
        self.base_url = "https://www.bugherd.com/api/v2"

    def create_ticket(self, project_id, description, page_url=None):
        if not self.api_key:
            logger.error("BugHerd API Key missing. Skipping ticket creation.")
            return None

        url = f"{self.base_url}/projects/{project_id}/tasks.json"
        payload = {
            "task": {
                "description": description,
                "requester_email": "qa-auto@servicescalers.com",
                "priority": "normal",
                "metadata": {
                    "url": page_url
                }
            }
        }
        
        try:
            response = requests.post(url, auth=(self.api_key, 'x'), json=payload)
            if response.status_code == 201:
                logger.info(f"Ticket created successfully in project {project_id}")
                return response.json()
            else:
                logger.error(f"Failed to create ticket: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            logger.error(f"Error connecting to BugHerd: {e}")
            return None

    def create_ticket_comment(self, project_id, task_id, text):
        if not self.api_key:
            logger.error("BugHerd API Key missing. Skipping comment creation.")
            return None

        url = f"{self.base_url}/projects/{project_id}/tasks/{task_id}/comments.json"
        payload = {"comment": {"text": text}}
        
        try:
            response = requests.post(url, auth=(self.api_key, 'x'), json=payload)
            if response.status_code == 201:
                logger.info(f"Comment added to task {task_id}")
                return response.json()
            else:
                logger.error(f"Failed to add comment: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            logger.error(f"Error adding comment: {e}")
            return None
