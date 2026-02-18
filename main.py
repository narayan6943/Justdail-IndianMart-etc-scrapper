import asyncio
from src.scraper import ScraperEngine
from src.utils import logger
import sys

def main():
    print("=== Expert Business Lead Scraper ===")
    print("1. Justdial")
    print("2. IndiaMART")
    print("3. Custom URL (from settings.yaml)")
    
    choice = input("Select Platform (1-3): ").strip()    
    platform = 'custom'
    location = None
    query = None
    
    if choice == '1':
        platform = 'justdial'
        location = input("Enter Location (e.g., Pune, Mumbai): ").strip()
        query = input("Enter Service/Product (e.g., Plumbers, Lawyers): ").strip()
    elif choice == '2':
        platform = 'indiamart'
        location = input("Enter City (e.g., Pune): ").strip()
        query = input("Enter Service/Product (e.g., Plumbers): ").strip()
    
    logger.info(f"Starting Web Scraper for {platform}...")
    scraper = ScraperEngine(platform=platform, location=location, query=query)
    
    try:
        asyncio.run(scraper.run())
        logger.info("Scraping completed successfully.")
    except KeyboardInterrupt:
        logger.info("Scraping interrupted by user.")
    except Exception as e:
        logger.critical(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
