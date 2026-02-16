import yaml
import os
from pathlib import Path
from urllib.parse import quote_plus

class Config:
    def __init__(self):
        self.base_dir = Path(__file__).resolve().parent.parent
        self.settings = self._load_yaml("config/settings.yaml")
        self.selectors = self._load_yaml("config/selectors.yaml")
        
    def _load_yaml(self, path):
        full_path = self.base_dir / path
        if not full_path.exists():
            raise FileNotFoundError(f"Config file not found: {full_path}")
        with open(full_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

    @property
    def target_url(self):
        return self.settings['scraper']['target_url']

    @property
    def max_pages(self):
        return self.settings['scraper']['max_pages']

    @property
    def target_records(self):
        return self.settings['scraper'].get('target_records', 100)

    @property
    def output_dir(self):
        return self.base_dir / self.settings['output']['directory']
    
    @property
    def log_file(self):
        return self.base_dir / self.settings['logging']['file']

    def get_platform_url(self, platform, location, query):
        """Generates URL based on platform pattern."""
        platform_config = self.selectors.get('platforms', {}).get(platform)
        if not platform_config:
            raise ValueError(f"Unknown platform: {platform}")
        
        pattern = platform_config.get('url_pattern')
        # URL Encode the parameters
        return pattern.format(location=quote_plus(location), query=quote_plus(query))
    
    def get_platform_selectors(self, platform):
        """Returns specific selectors for a platform."""
        if platform == 'custom':
            return self.selectors.get('generic')
        return self.selectors.get('platforms', {}).get(platform)


config = Config()
