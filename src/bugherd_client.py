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

    def create_ticket_with_element(self, project_id, issue_type, element_info, expected, found, page_url):
        """
        Create a BugHerd ticket with element location information.
        
        Args:
            project_id: BugHerd project ID
            issue_type: Type of issue (e.g., "SEO Title Mismatch")
            element_info: Dict with css_selector, xpath, context from ElementLocator
            expected: Expected value
            found: Actual value found
            page_url: URL of the page
        """
        if not self.api_key:
            logger.error("BugHerd API Key missing. Skipping ticket creation.")
            return None
        
        # Build structured description
        description = f"**{issue_type}**\n\n"
        
        if element_info and element_info.get('tag'):
            description += f"**Element:** `<{element_info['tag']}>`\n"
        
        description += f"**Expected:** {expected}\n"
        description += f"**Found:** {found}\n\n"
        
        # Add location information
        if element_info:
            description += "📍 **Element Location:**\n"
            if element_info.get('css_selector'):
                description += f"- **CSS Selector:** `{element_info['css_selector']}`\n"
            if element_info.get('xpath'):
                description += f"- **XPath:** `{element_info['xpath']}`\n"
            if element_info.get('context'):
                description += f"- **Context:** \"{element_info['context']}\"\n"
        
        description += f"\n🔗 **Page URL:** {page_url}"
        
        return self.create_ticket(project_id, description, page_url=page_url)
