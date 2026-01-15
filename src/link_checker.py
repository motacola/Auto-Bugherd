import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

class LinkChecker:
    def __init__(self, user_agent, timeout=5):
        self.headers = {'User-Agent': user_agent}
        self.timeout = timeout
        # Social media platforms often block scrapers, causing false 403/400 errors
        self.ignored_domains = ['facebook.com', 'twitter.com', 'linkedin.com', 'instagram.com', 'youtube.com']

    def is_social_link(self, url):
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        return any(social in domain for social in self.ignored_domains)

    def check_page_links(self, url):
        """
        Finds all links on the page and checks their status code.
        Returns a list of broken links.
        """
        print(f"🔍 Checking all links on {url}...")
        try:
            response = requests.get(url, headers=self.headers, timeout=self.timeout)
            if response.status_code != 200:
                return [f"Page itself is unreachable: {response.status_code}"]
            
            soup = BeautifulSoup(response.text, 'html.parser')
            links = soup.find_all('a', href=True)
            broken_links = []
            
            # Avoid checking the same URL multiple times
            checked_urls = set()
            
            for link in links:
                href = link['href']
                absolute_url = urljoin(url, href)
                
                # Basic filter: skip anchors, mailto, tel
                if absolute_url.startswith(('mailto:', 'tel:', '#')) or absolute_url in checked_urls:
                    continue
                
                # Filter out social links to avoid false positives
                if self.is_social_link(absolute_url):
                    continue

                checked_urls.add(absolute_url)
                
                try:
                    # HEAD request is faster than GET
                    res = requests.head(absolute_url, headers=self.headers, timeout=self.timeout, allow_redirects=True)
                    if res.status_code >= 400:
                        # Retry with GET as some servers block HEAD
                        res = requests.get(absolute_url, headers=self.headers, timeout=self.timeout)
                        if res.status_code >= 400:
                            broken_links.append(f"{absolute_url} ({res.status_code})")
                except Exception as e:
                    broken_links.append(f"{absolute_url} (Error: {str(e)})")
            
            return broken_links
        except Exception as e:
            return [f"Link checker error: {str(e)}"]
