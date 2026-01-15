import datetime
import os
import logging
from typing import Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ReportGenerator:
    def __init__(self, output_dir="reports"):
        self.output_dir = output_dir
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

    def generate_html_report(self, project_name: str, results: list[dict]) -> Optional[str]:
        """
        Generate an HTML report for the QA results.
        
        Args:
            project_name: Name of the project for the report.
            results: List of dictionaries containing page_name, url, and issues.
        
        Returns:
            Path to the generated HTML report file, or None if an error occurs.
        """
        if not project_name or not results:
            logger.error("Invalid input: project_name and results must be provided.")
            return None
        
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        filename = f"report_{project_name.lower().replace(' ', '_')}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        filepath = os.path.join(self.output_dir, filename)

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>QA Report - {project_name}</title>
            <style>
                body {{ font-family: 'Inter', sans-serif; background: #f4f7f6; color: #333; margin: 0; padding: 40px; }}
                .container {{ max-width: 1000px; margin: auto; background: white; padding: 30px; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.08); }}
                h1 {{ color: #1a1a1a; margin-top: 0; }}
                .meta {{ color: #666; font-size: 0.9em; margin-bottom: 30px; border-bottom: 1px solid #eee; padding-bottom: 20px; }}
                .card {{ border: 1px solid #eee; border-radius: 8px; padding: 20px; margin-bottom: 20px; }}
                .card.pass {{ border-left: 6px solid #2ecc71; }}
                .card.fail {{ border-left: 6px solid #e74c3c; }}
                .status-badge {{ display: inline-block; padding: 4px 12px; border-radius: 20px; font-size: 0.8em; font-weight: bold; text-transform: uppercase; }}
                .pass .status-badge {{ background: #eafaf1; color: #2ecc71; }}
                .fail .status-badge {{ background: #fdf2f2; color: #e74c3c; }}
                .issue-list {{ margin-top: 15px; padding-left: 20px; color: #555; }}
                .issue-item {{ margin-bottom: 8px; }}
                a {{ color: #3498db; text-decoration: none; }}
                a:hover {{ text-decoration: underline; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>QA Automation Report</h1>
                <div class="meta">
                    <strong>Project:</strong> {project_name}<br>
                    <strong>Generated:</strong> {timestamp}
                </div>
                
                {"".join([self._render_card(r) for r in results])}
            </div>
        </body>
        </html>
        """
        
        try:
            with open(filepath, 'w') as f:
                f.write(html_content)
            logger.info(f"✅ HTML Report generated: {filepath}")
            return filepath
        except IOError as e:
            logger.error(f"Failed to write report file: {e}")
            return None

    def _render_card(self, result: dict) -> str:
        """
        Render an individual card for the report.
        
        Args:
            result: Dictionary containing page_name, url, and issues.
        
        Returns:
            HTML string for the card.
        """
        if not isinstance(result, dict) or 'page_name' not in result or 'url' not in result:
            logger.error("Invalid result format: missing required keys.")
            return ""
        
        status_class = "pass" if not result['issues'] else "fail"
        status_text = "PASSED" if not result['issues'] else "FAILED"
        
        issues_html = ""
        if result['issues']:
            issues_html = '<ul class="issue-list">' + "".join([f'<li class="issue-item">{i}</li>' for i in result['issues']]) + '</ul>'
        
        return f"""
        <div class="card {status_class}">
            <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                <div>
                    <h3 style="margin: 0 0 5px 0;">{result['page_name']}</h3>
                    <a href="{result['url']}" target="_blank">{result['url']}</a>
                </div>
                <span class="status-badge">{status_text}</span>
            </div>
            {issues_html}
        </div>
        """
