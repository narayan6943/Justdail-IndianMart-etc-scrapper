import pandas as pd
from .config import config
import os
import logging

logger = logging.getLogger("Scraper")

class StorageManager:
    def __init__(self):
        self.data = []
        self.output_dir = config.output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        self.filename = config.settings['output']['filename']
        self.formats = config.settings['output'].get('format', 'csv').split(',')

    def add_record(self, record):
        if record:
            self.data.append(record)

    def save(self):
        if not self.data:
            logger.warning("No data to save.")
            return

        df = pd.DataFrame(self.data)
        
        base_path = self.output_dir / self.filename
        
        for fmt in self.formats:
            fmt = fmt.strip().lower()
            if fmt == 'csv':
                path = base_path.with_suffix('.csv')
                df.to_csv(path, index=False, encoding='utf-8-sig')
                logger.info(f"Saved {len(df)} records to {path}")
            elif fmt == 'json':
                path = base_path.with_suffix('.json')
                df.to_json(path, orient='records', indent=4)
                logger.info(f"Saved {len(df)} records to {path}")
            elif fmt == 'excel':
                path = base_path.with_suffix('.xlsx')
                df.to_excel(path, index=False)
                logger.info(f"Saved {len(df)} records to {path}")
