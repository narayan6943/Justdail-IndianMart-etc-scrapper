from bs4 import BeautifulSoup
from .config import config
import logging

logger = logging.getLogger("Scraper")

class HTMLParser:
    def __init__(self):
        self.selectors = config.selectors

    def parse_listing(self, html_content):
        """Parses a single listing HTML block."""
        soup = BeautifulSoup(html_content, 'html.parser')
        data = {}
        
        for field, rules in self.selectors['fields'].items():
            selector = rules.get('selector')
            if not selector:
                continue
                
            element = soup.select_one(selector)
            value = None
            
            if element:
                extract_type = rules.get('type', 'text')
                if extract_type == 'text':
                    value = element.get_text(strip=True)
                elif extract_type == 'attribute':
                    attr = rules.get('attribute')
                    value = element.get(attr)
                elif extract_type == 'html':
                     value = str(element)
            
            data[field] = value
            
        return data

    def parse_page(self, page_html):
        """Parses variables from the page HTML."""
        soup = BeautifulSoup(page_html, 'html.parser')
        container_selector = self.selectors.get('listing_container')
        
        if not container_selector:
             logger.error("No listing_container selector defined in selectors.yaml")
             return []

        listings = soup.select(container_selector)
        parsed_items = []
        
        for listing in listings:
            # We pass the outer HTML of the listing to parse_listing
            # Or we could pass the element itself if we refactored parse_listing to take a Tag
            # For simplicity, convert back to string or modify parse_listing to take soup object.
            # Let's modify parse_listing to accept a soup Tag for efficiency.
            item_data = self._extract_from_tag(listing)
            parsed_items.append(item_data)
            
        return parsed_items

    def _extract_from_tag(self, tag):
        data = {}
        for field, rules in self.selectors['fields'].items():
            selector = rules.get('selector')
            if not selector:
                continue
            
            # Select within the current tag
            element = tag.select_one(selector)
            value = None
            
            if element:
                extract_type = rules.get('type', 'text')
                if extract_type == 'text':
                    value = element.get_text(strip=True)
                elif extract_type == 'attribute':
                    attr = rules.get('attribute')
                    value = element.get(attr)
            
            data[field] = value
        
        # Fallback for business_name if it's missing but product_name exists
        if not data.get('business_name') and data.get('product_name'):
            data['business_name'] = data['product_name']
        elif not data.get('business_name'):
            # Final fallback to first link text if nothing found
            first_link = tag.find('a')
            if first_link:
                data['business_name'] = first_link.get_text(strip=True)
            else:
                data['business_name'] = "Unnamed Business"
                
        return data

    def has_next_page(self, page_html):
        soup = BeautifulSoup(page_html, 'html.parser')
        next_selector = self.selectors.get('next_button')
        if next_selector:
            return bool(soup.select_one(next_selector))
        return False
