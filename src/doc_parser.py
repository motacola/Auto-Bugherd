import requests
from bs4 import BeautifulSoup
import re

class GoogleDocParser:
    def __init__(self, user_agent):
        self.headers = {'User-Agent': user_agent}

    def fetch_text_public(self, url):
        if not url:
            return None
        """
        Fetches text from a public Google Doc by export/view mode.
        """
        if "/edit" in url:
            pub_url = url.replace("/edit", "/pub")
        else:
            pub_url = url
            
        try:
            response = requests.get(pub_url, headers=self.headers, timeout=10)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                content_div = soup.find('div', id='contents') or soup.body
                if content_div:
                    return content_div.get_text(separator=' ', strip=True)
            return None
        except Exception as e:
            print(f"Error fetching Google Doc: {e}")
            return None

    def extract_seo_metadata(self, text):
        """
        Extracts Title, Meta Description, and H1 from the text content.
        Uses more flexible regex to handle various formatting.
        """
        metadata = {
            "title": None,
            "description": None,
            "h1": None
        }
        
        # Patterns for Title (Improved)
        title_match = re.search(r"(?:SEO\s+Title|Title\s+Tag|Page\s+Title)[:\s]+(.*?)(?:\n|$|\s{2,})", text, re.IGNORECASE)
        if title_match:
            metadata["title"] = title_match.group(1).strip()
            
        # Patterns for Description (Improved)
        desc_match = re.search(r"(?:Meta\s+Description|SEO\s+Description|Description)[:\s]+(.*?)(?:\n|$|\s{2,})", text, re.IGNORECASE)
        if desc_match:
            metadata["description"] = desc_match.group(1).strip()
            
        # Patterns for H1 (Improved)
        h1_match = re.search(r"(?:H1\s+Header|H1\s+Tag|H1)[:\s]+(.*?)(?:\n|$|\s{2,})", text, re.IGNORECASE)
        if h1_match:
            metadata["h1"] = h1_match.group(1).strip()
            
        return metadata

    def find_metrics_block(self, text):
        """
        Attempts to extract the metrics section specifically.
        """
        metrics_pattern = re.compile(r"(\d+\+?\s+Years|\d\.\d\s+Stars|\d+\+\s+Service areas)", re.IGNORECASE)
        matches = metrics_pattern.findall(text)
        return list(set(matches)) # Unique only

    def fuzzy_match(self, needle, haystack, threshold=0.8):
        """
        Simple fuzzy matching to find text even with minor variations.
        """
        from difflib import SequenceMatcher
        if not needle or not haystack:
            return False
            
        needle = needle.lower().strip()
        haystack = haystack.lower()
        
        if needle in haystack:
            return True
            
        # Check if any segment of haystack is close to needle
        words = haystack.split()
        needle_words = needle.split()
        n_len = len(needle_words)
        
        for i in range(len(words) - n_len + 1):
            segment = " ".join(words[i:i+n_len])
            ratio = SequenceMatcher(None, needle, segment).ratio()
            if ratio >= threshold:
                return True
        return False
