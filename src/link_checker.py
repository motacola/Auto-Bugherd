import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging

logger = logging.getLogger(__name__)

class LinkChecker:
    def __init__(self, user_agent, timeout=5, max_workers=10):
        self.headers = {'User-Agent': user_agent}
        self.timeout = timeout
        self.max_workers = max_workers
        self.ignored_domains = ['facebook.com', 'twitter.com', 'linkedin.com', 'instagram.com', 'youtube.com']

    def is_social_link(self, url):
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        return any(social in domain for social in self.ignored_domains)

    def _check_single_link(self, absolute_url):
        try:
            # HEAD request is faster than GET
            res = requests.head(absolute_url, headers=self.headers, timeout=self.timeout, allow_redirects=True)
            if res.status_code >= 400:
                # Retry with GET as some servers block HEAD
                res = requests.get(absolute_url, headers=self.headers, timeout=self.timeout)
                if res.status_code >= 400:
                    return f"{absolute_url} ({res.status_code})"
            return None
        except Exception as e:
            return f"{absolute_url} (Error: {str(e)})"

    def check_page_links(self, url):
        """
        Finds all links on the page and checks their status code in parallel.
        Returns a list of broken links.
        """
        logger.info(f"🔍 Checking all links on {url}...")
        try:
            response = requests.get(url, headers=self.headers, timeout=self.timeout)
            if response.status_code != 200:
                return [f"Page itself is unreachable: {response.status_code}"]
            
            soup = BeautifulSoup(response.text, 'html.parser')
            links = soup.find_all('a', href=True)
            broken_links = []
            
            # Avoid checking the same URL multiple times
            target_urls = set()
            
            for link in links:
                href = link['href']
                absolute_url = urljoin(url, href)
                
                # Basic filter: skip anchors, mailto, tel
                if absolute_url.startswith(('mailto:', 'tel:', '#')):
                    continue
                
                # Filter out social links
                if self.is_social_link(absolute_url):
                    continue

                target_urls.add(absolute_url)

            # Parallel checking
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                future_to_url = {executor.submit(self._check_single_link, l_url): l_url for l_url in target_urls}
                for future in as_completed(future_to_url):
                    result = future.result()
                    if result:
                        broken_links.append(result)
            
            return broken_links
        except Exception as e:
            logger.error(f"Link checker fatal error: {e}")
            return [f"Link checker error: {str(e)}"]
