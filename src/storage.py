import pandas as pd
from .config import config
import os
import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger("Scraper")

class StorageManager:
    def __init__(self, search_term="default"):
        self.data = []
        
        # Clean the search term for use as a folder name (replace spaces and special chars)
        self.search_tag = "".join(c if c.isalnum() or c in ('-', '_') else '_' for c in search_term).lower()
        
        # Dynamic Output Directory: output/search_term/
        self.output_dir = config.output_dir / self.search_tag
        
        # Ensure directories are created safely without wiping content
        try:
            self.output_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Storage initialized at: {self.output_dir}")
        except Exception as e:
            logger.error(f"Failed to create output directory {self.output_dir}: {e}")
            # Fallback to base output dir if subfolder creation fails
            self.output_dir = config.output_dir

        self.base_filename = config.settings['output'].get('filename', 'leads_data')
        self.formats = config.settings['output'].get('format', 'csv').split(',')

    def add_record(self, record):
        if record:
            self.data.append(record)

    def save(self):
        if not self.data:
            logger.warning("No data to save.")
            return

        # Generate unique filename with timestamp: leads_data_20240218_231000
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        final_filename = f"{self.base_filename}_{timestamp}"
        
        df = pd.DataFrame(self.data)
        
        for fmt in self.formats:
            fmt = fmt.strip().lower()
            try:
                if fmt == 'csv':
                    path = self.output_dir / f"{final_filename}.csv"
                    df.to_csv(path, index=False, encoding='utf-8-sig')
                    logger.info(f"Saved {len(df)} records to {path}")
                elif fmt == 'json':
                    path = self.output_dir / f"{final_filename}.json"
                    df.to_json(path, orient='records', indent=4)
                    logger.info(f"Saved {len(df)} records to {path}")
                elif fmt == 'excel':
                    path = self.output_dir / f"{final_filename}.xlsx"
                    df.to_excel(path, index=False)
                    logger.info(f"Saved {len(df)} records to {path}")
            except Exception as e:
                logger.error(f"Error saving data in {fmt} format: {e}")
