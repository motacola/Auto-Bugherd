import requests
import os

class BugHerdClient:
    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv("BUGHERD_API_KEY")
        self.base_url = "https://www.bugherd.com/api/v2"

    def create_ticket(self, project_id, description, page_url=None):
        if not self.api_key:
            print("❌ BugHerd API Key missing. Skipping ticket creation.")
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
                print(f"✅ Ticket created successfully in project {project_id}")
                return response.json()
            else:
                print(f"❌ Failed to create ticket: {response.text}")
                return None
        except Exception as e:
            print(f"❌ Error connecting to BugHerd: {e}")
            return None

    def create_ticket_comment(self, project_id, task_id, text):
        if not self.api_key:
            return None

        url = f"{self.base_url}/projects/{project_id}/tasks/{task_id}/comments.json"
        payload = {"comment": {"text": text}}
        
        try:
            response = requests.post(url, auth=(self.api_key, 'x'), json=payload)
            if response.status_code == 201:
                print(f"✅ Comment added to task {task_id}")
                return response.json()
            return None
        except Exception as e:
            print(f"❌ Error adding comment: {e}")
            return None
