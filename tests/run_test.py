import os
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from src.scraper import ScraperEngine
from src.config import config
import asyncio

async def test_run():
    # Update config to use test settings
    cwd = str(Path(__file__).resolve().parent.parent).replace('\\', '/')
    test_settings_path = Path("tests/test_settings.yaml")
    
    # Overwrite the global config's settings load (hacky but effective for test)
    # We need to re-initialize the config or manually load the test settings
    # For this test, let's just point the target_url to the absolute path of mock_page_1.html
    
    mock_url = f"file:///{cwd}/tests/mock_page_1.html"
    print(f"Testing with URL: {mock_url}")
    
    # Inject test config values
    config.settings['scraper']['target_url'] = mock_url
    config.settings['scraper']['max_pages'] = 2
    config.settings['output']['directory'] = "tests/output"
    config.settings['output']['filename'] = "test_results"
    config.settings['logging']['file'] = "tests/logs/test.log"
    
    # Ensure Test Selectors match Mock HTML
    # We are using the default selectors.yaml which matches the mock classes (.business-listing, etc.)
    
    print("Starting Test Scraper...")
    scraper = ScraperEngine()
    await scraper.run()
    print("Test Complete. Check tests/output/")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    asyncio.run(test_run())
