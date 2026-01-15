import logging
from bs4 import BeautifulSoup, Tag

logger = logging.getLogger(__name__)

class ElementLocator:
    """
    Generates CSS selectors and XPath for BeautifulSoup elements
    to help developers locate issues in the DOM.
    """
    
    @staticmethod
    def get_css_selector(element):
        """
        Generate a CSS selector for the given element.
        Tries to create a unique, readable selector.
        """
        if not isinstance(element, Tag):
            return None
            
        # Build selector from element and its parents
        parts = []
        current = element
        
        while current and current.name != '[document]':
            selector_part = current.name
            
            # Add ID if present (most specific)
            if current.get('id'):
                selector_part = f"#{current.get('id')}"
                parts.insert(0, selector_part)
                break  # ID is unique, stop here
            
            # Add classes if present
            classes = current.get('class', [])
            if classes:
                class_str = '.'.join(classes)
                selector_part = f"{current.name}.{class_str}"
            
            # Add nth-child if needed for uniqueness
            if current.parent:
                siblings = [s for s in current.parent.children if isinstance(s, Tag) and s.name == current.name]
                if len(siblings) > 1:
                    index = siblings.index(current) + 1
                    selector_part = f"{selector_part}:nth-child({index})"
            
            parts.insert(0, selector_part)
            current = current.parent
            
            # Limit depth to keep selector readable
            if len(parts) >= 5:
                break
        
        return ' > '.join(parts) if parts else None
    
    @staticmethod
    def get_xpath(element):
        """
        Generate an XPath for the given element.
        """
        if not isinstance(element, Tag):
            return None
            
        parts = []
        current = element
        
        while current and current.name != '[document]':
            # Count siblings with same tag name
            siblings = [s for s in current.parent.children if isinstance(s, Tag) and s.name == current.name] if current.parent else [current]
            
            if len(siblings) > 1:
                index = siblings.index(current) + 1
                parts.insert(0, f"{current.name}[{index}]")
            else:
                parts.insert(0, current.name)
            
            current = current.parent
            
            # Limit depth
            if len(parts) >= 8:
                break
        
        return '/' + '/'.join(parts) if parts else None
    
    @staticmethod
    def get_element_context(element, chars=100):
        """
        Extract surrounding text context for the element.
        Useful for identifying the element in the page.
        """
        if not isinstance(element, Tag):
            return None
            
        text = element.get_text(strip=True)
        
        # Truncate if too long
        if len(text) > chars:
            text = text[:chars] + "..."
        
        return text if text else "[No text content]"
    
    @staticmethod
    def get_element_info(element):
        """
        Get comprehensive location info for an element.
        Returns a dict with css_selector, xpath, and context.
        """
        if not element:
            return None
            
        return {
            "tag": element.name if isinstance(element, Tag) else None,
            "css_selector": ElementLocator.get_css_selector(element),
            "xpath": ElementLocator.get_xpath(element),
            "context": ElementLocator.get_element_context(element)
        }
