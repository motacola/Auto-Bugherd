import requests
import json
import sys
import os
import argparse
import logging
from bs4 import BeautifulSoup
from requests.exceptions import RequestException
from .bugherd_client import BugHerdClient
from .doc_parser import GoogleDocParser
from .link_checker import LinkChecker
from .report_generator import ReportGenerator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BugHerdEngine:
    def __init__(self, config_path="config.json", bugherd_api_key=None):
        # Resolve config path relative to project root
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        config_full_path = os.path.join(base_path, config_path)
        
        self.config = {
            "projects": [],
            "settings": {
                "user_agent": os.getenv("USER_AGENT", "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"),
                "timeout": int(os.getenv("TIMEOUT", 10))
            }
        }

        if os.path.exists(config_full_path):
            try:
                with open(config_full_path, 'r') as f:
                    user_config = json.load(f)
                    # Merge settings safely
                    if "settings" in user_config:
                        self.config["settings"].update(user_config["settings"])
                    if "projects" in user_config:
                        self.config["projects"] = user_config["projects"]
            except Exception as e:
                print(f"⚠️ Warning: Failed to load config.json ({e}). Using defaults.")
            
        self.headers = {'User-Agent': self.config['settings']['user_agent']}
        self.timeout = self.config['settings']['timeout']
        self.bh_client = BugHerdClient(api_key=bugherd_api_key)
        self.doc_parser = GoogleDocParser(user_agent=self.config['settings']['user_agent'])
        self.link_checker = LinkChecker(user_agent=self.config['settings']['user_agent'], timeout=self.timeout)
        self.report_gen = ReportGenerator()

    def fetch_live_soup(self, url) -> BeautifulSoup | None:
        try:
            response = requests.get(url, headers=self.headers, timeout=self.timeout)
            if response.status_code == 200:
                return BeautifulSoup(response.text, 'html.parser')
            logger.error(f"Failed to fetch {url}: HTTP {response.status_code}")
            return None
        except RequestException as e:
            logger.error(f"Error fetching {url}: {e}")
            return None

    def check_seo_metadata(self, soup: BeautifulSoup, target_meta: dict, page_name: str) -> list[str]:
        issues = []
        if not soup or not target_meta:
            return issues

        # Check Title
        if target_meta.get('title'):
            live_title = soup.title.string.strip() if soup.title else "Missing Title Tag"
            if not self.doc_parser.fuzzy_match(target_meta['title'], live_title):
                logger.warning(f"SEO Title mismatch for {page_name}. Expected: '{target_meta['title']}', Found: '{live_title}'")
                issues.append(f"SEO Title mismatch. Expected: '{target_meta['title']}', Found: '{live_title}'")

        # Check Description
        if target_meta.get('description'):
            live_desc = soup.find('meta', attrs={'name': 'description'})
            live_desc_content = live_desc['content'].strip() if live_desc else "Missing Meta Description"
            if not self.doc_parser.fuzzy_match(target_meta['description'], live_desc_content, threshold=0.6):
                logger.warning(f"Meta Description mismatch for {page_name}. Expected snippet of: '{target_meta['description'][:50]}...'")
                issues.append(f"Meta Description mismatch. Expected snippet of: '{target_meta['description'][:50]}...'")

        # Check H1
        if target_meta.get('h1'):
            live_h1 = soup.find('h1')
            live_h1_text = live_h1.get_text().strip() if live_h1 else "Missing H1 Tag"
            if not self.doc_parser.fuzzy_match(target_meta['h1'], live_h1_text):
                logger.warning(f"H1 Header mismatch for {page_name}. Expected: '{target_meta['h1']}', Found: '{live_h1_text}'")
                issues.append(f"H1 Header mismatch. Expected: '{target_meta['h1']}', Found: '{live_h1_text}'")

        return issues

    def run_qa_ad_hoc(self, url, doc_url=None, auto_ticket=False, project_id=None, check_links=False):
        print(f"--- Running Ad-Hoc QA Check ---")
        results = []
        issues = []
        
        doc_text = None
        target_seo = None
        if doc_url:
            doc_text = self.doc_parser.fetch_text_public(doc_url)
            if doc_text:
                print("✅ Source of Truth fetched from Google Doc.")
                target_seo = self.doc_parser.extract_seo_metadata(doc_text)
            else:
                print("⚠️ Warning: Could not fetch Google Doc content.")

        soup = self.fetch_live_soup(url)
        if not soup:
            print(f"❌ Could not reach target URL: {url}")
            return False

        content = soup.get_text()

        # 1. SEO Metadata Check
        if target_seo:
            issues.extend(self.check_seo_metadata(soup, target_seo, "Ad-Hoc"))

        # 2. Metrics Check
        if doc_text:
            doc_metrics = self.doc_parser.find_metrics_block(doc_text)
            for metric in doc_metrics:
                if not self.doc_parser.fuzzy_match(metric, content):
                    issue_msg = f"Metric '{metric}' missing or mismatch from Google Doc."
                    issues.append(issue_msg)
                    if auto_ticket and project_id:
                        self.bh_client.create_ticket(project_id, issue_msg, page_url=url)

        # 3. Link Check
        if check_links:
            broken = self.link_checker.check_page_links(url)
            if broken:
                issues.append(f"Broken links found: {', '.join(broken)}")

        results.append({"page_name": "Ad-Hoc Check", "url": url, "issues": issues})
        self.report_gen.generate_html_report("Ad-Hoc Run", results)

        if issues:
            print(f"\n🚨 {len(issues)} ISSUES FOUND (See HTML report for details)")
            return False
        
        print("\n✅ QA Check Passed!")
        return True

    def run_qa_project(self, project_id, auto_ticket=False, check_links=False):
        project = next((p for p in self.config['projects'] if str(p['id']) == str(project_id)), None)
        if not project:
            print(f"Project {project_id} not found in config.")
            return False

        print(f"--- Running QA for {project['name']} ---")
        results = []
        
        google_doc_url = project.get('google_doc_url')
        doc_text = self.doc_parser.fetch_text_public(google_doc_url) if google_doc_url else None
        target_seo = self.doc_parser.extract_seo_metadata(doc_text) if doc_text else None
        
        for page_name, url in project.get('live_pages', {}).items():
            print(f"Checking {page_name}...")
            page_issues = []
            soup = self.fetch_live_soup(url)
            if not soup:
                page_issues.append(f"Could not reach page: {url}")
                results.append({"page_name": page_name, "url": url, "issues": page_issues})
                continue

            content = soup.get_text()

            # SEO METADATA
            if target_seo:
                page_issues.extend(self.check_seo_metadata(soup, target_seo, page_name))

            # BAD PHRASES
            rules = project.get('rules', {})
            for phrase in rules.get('bad_phrases', []):
                if phrase in content:
                    issue_msg = f"Found copy error: '{phrase}'"
                    page_issues.append(issue_msg)
                    if auto_ticket:
                        self.bh_client.create_ticket(project.get('bugherd_project_id'), issue_msg, page_url=url)

            # METRICS
            if doc_text:
                doc_metrics = self.doc_parser.find_metrics_block(doc_text)
                for metric in doc_metrics:
                    if not self.doc_parser.fuzzy_match(metric, content):
                        issue_msg = f"Metric '{metric}' missing or mismatch from Google Doc."
                        page_issues.append(issue_msg)
                        if auto_ticket:
                            self.bh_client.create_ticket(project.get('bugherd_project_id'), issue_msg, page_url=url)

            # LINKS
            if check_links:
                broken = self.link_checker.check_page_links(url)
                if broken:
                    page_issues.append(f"Broken links: {', '.join(broken)}")

            results.append({"page_name": page_name, "url": url, "issues": page_issues})

        self.report_gen.generate_html_report(project['name'], results)
        return all(not r['issues'] for r in results)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="auto-bugherd QA Engine")
    parser.add_argument("project", nargs="?", help="Project ID from config.json")
    parser.add_argument("--url", help="Ad-hoc URL to check")
    parser.add_argument("--doc-url", help="Google Doc URL for comparison")
    parser.add_argument("--ticket", action="store_true", help="Auto-create BugHerd tickets")
    parser.add_argument("--check-links", action="store_true", help="Check for broken links on the page")
    parser.add_argument("--project-id", help="BugHerd Project ID (required for ad-hoc ticketing)")

    args = parser.parse_args()
    engine = BugHerdEngine()

    if args.url:
        success = engine.run_qa_ad_hoc(args.url, doc_url=args.doc_url, auto_ticket=args.ticket, project_id=args.project_id, check_links=args.check_links)
    elif args.project:
        success = engine.run_qa_project(args.project, auto_ticket=args.ticket, check_links=args.check_links)
    else:
        parser.print_help()
        sys.exit(1)

    sys.exit(0 if success else 1)
