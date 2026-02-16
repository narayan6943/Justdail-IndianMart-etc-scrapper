from .models import BusinessLead
from .config import config
import logging

logger = logging.getLogger("Scraper")

class DataPipeline:
    def __init__(self):
        self.seen_leads = set()
        self.processed_count = 0

    def process(self, raw_data, metadata):
        """
        Cleans, validates, and deduplicates the raw data.
        """
        # Add metadata
        raw_data.update(metadata)
        
        # Pydantic validation & cleaning
        try:
            lead = BusinessLead(**raw_data)
        except Exception as e:
            logger.warning(f"Validation error for data {raw_data.get('business_name', 'Unknown')}: {e}")
            return None
        
        # Deduplication
        dedup_key = (lead.phone, lead.business_name)
        if config.settings['processing']['deduplicate']:
            if dedup_key in self.seen_leads:
                logger.info(f"Duplicate detected: {lead.business_name} ({lead.phone})")
                return None
            self.seen_leads.add(dedup_key)
            
        self.processed_count += 1
        return lead.dict()
