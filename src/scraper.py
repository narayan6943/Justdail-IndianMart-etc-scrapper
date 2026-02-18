from playwright.async_api import async_playwright
import asyncio
import logging
from datetime import datetime
from .config import config
from .parser import HTMLParser
from .pipeline import DataPipeline
from .storage import StorageManager
from .utils import logger
import random

class ScraperEngine:
    def __init__(self, platform='custom', location=None, query=None):
        self.platform = platform
        self.location = location
        self.query = query
        
        # Construct search term for dynamic folder naming
        search_term = "custom_run"
        if query and location:
            search_term = f"{query}_{location}"
        elif query:
            search_term = query
        elif platform != 'custom':
            search_term = platform

        self.pipeline = DataPipeline()
        self.storage = StorageManager(search_term=search_term)
        
        if platform == 'custom':
            self.start_url = config.settings['scraper']['target_url']
            self.selectors = config.selectors.get('generic') # Fallback
        else:
            self.start_url = config.get_platform_url(platform, location, query)
            self.selectors = config.get_platform_selectors(platform)
            
        # Re-initialize parser with specific selectors
        self.parser = HTMLParser() 
        self.parser.selectors = self.selectors # Override parser selectors manually

    async def _apply_stealth(self, page):
        """Manually applies stealth scripts to mask automation."""
        await page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)
        await page.add_init_script("""
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en']
            });
        """)
        await page.add_init_script("""
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });
        """)
        await page.add_init_script("""
            window.chrome = { runtime: {} };
        """)
        await page.add_init_script("""
            const originalQuery = window.navigator.permissions.query;
            return window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                    Promise.resolve({ state: Notification.permission }) :
                    originalQuery(parameters)
            );
        """)

    async def run(self):
        if not self.selectors:
             logger.error("No selectors found for this configuration.")
             return

        async with async_playwright() as p:
            # Launch Browser - "Expert" settings for speed but MORE HUMAN for Justdial
            browser = await p.chromium.launch(
                headless=False, # Justdial often blocks Headless mode completely. We need HEADFUL.
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--disable-infobars",
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-http2",
                ]
            )
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                viewport={'width': 1366, 'height': 768},
                java_script_enabled=True,
                locale='en-US'
            )
            
            # Block resources for speed - KEEP THIS but maybe allow images if detection is visual
            await context.route("**/*", lambda route: route.abort() 
                if route.request.resource_type in ["media", "font"] 
                else route.continue_()
            )
            
            page = await context.new_page()
            
            # Apply Manual Stealth
            await self._apply_stealth(page)
            
            # Navigation
            # Navigation
            current_page = 1
            max_pages = config.settings['scraper']['max_pages']
            
            try:
                logger.info(f"Navigating to {self.start_url} (Platform: {self.platform})")
                try:
                    await page.goto(self.start_url, timeout=90000, wait_until='load')
                except Exception as e:
                    logger.warning(f"Initial navigation warning (continuing anyway): {e}")
                
                await asyncio.sleep(random.uniform(5, 8)) # Give extra time for JS hydration
                
                # Check for "Select City" popups or overlays which are common on IndiaMART/Justdial
                try:
                    for popup_selector in ['.city-pop', '.modal-close', '#close_location_popup']:
                        if await page.is_visible(popup_selector):
                            await page.click(popup_selector)
                            await asyncio.sleep(1)
                except:
                    pass

                total_scraped = 0
                target = config.target_records
                
                while current_page <= max_pages and total_scraped < target:
                    # Check if browser is still connected
                    if not browser.is_connected():
                        logger.error("Browser connection lost.")
                        break

                    logger.info(f"Scraping page {current_page} (Total collected: {total_scraped}/{target})")
                    
                    # Wait for at least one listing to appear before starting
                    try:
                        container_sel = self.selectors.get('listing_container', '.card').split(',')[0].strip()
                        await page.wait_for_selector(container_sel, timeout=15000)
                    except:
                        logger.warning("Timeout waiting for listing containers. Site might be slow or blocked.")

                    # Specialized behavior for infinite scroll sites
                    if self.platform in ['justdial', 'indiamart']:
                        await self._aggressive_scroll(page, target=target)
                    
                    # Parse Content
                    content = await page.content()
                    raw_items = self.parser.parse_page(content)
                    
                    new_items_count = 0
                    for item in raw_items:
                        metadata = {
                            "source_url": page.url,
                            "date_collected": datetime.now().isoformat(),
                            "has_website": bool(item.get('website')),
                            "city": getattr(self, 'location', 'N/A'),
                            "category": getattr(self, 'query', 'N/A')
                        }
                        # Merge location/query if they were passed
                        if hasattr(self, 'location') and not item.get('city'):
                            item['city'] = self.location
                        if hasattr(self, 'query') and not item.get('category'):
                            item['category'] = self.query

                        PROCESSED_DATA = self.pipeline.process(item, metadata)
                        if PROCESSED_DATA:
                            self.storage.add_record(PROCESSED_DATA)
                            new_items_count += 1
                            
                    total_scraped = len(self.storage.data)
                    logger.info(f"Page {current_page}: Found {len(raw_items)} items, Added {new_items_count} new. Total: {total_scraped}")
                    
                    if total_scraped >= target:
                        logger.info("Target records reached!")
                        break

                    if current_page < max_pages:
                        next_selector = self.selectors.get('next_button')
                        
                        # DATA DUMP FOR DEBUGGING IF STUCK
                        if new_items_count == 0:
                            logger.warning(f"Page {current_page} yielded 0 items. Dumping HTML for inspection.")
                            debug_file = self.storage.output_dir / f"debug_page_{current_page}.html"
                            with open(debug_file, "w", encoding="utf-8") as f:
                                f.write(content)
                        
                        # Try standard Next Button
                        if next_selector and await page.query_selector(next_selector):
                            try:
                                await page.click(next_selector)
                                await page.wait_for_load_state('networkidle', timeout=10000)
                                await asyncio.sleep(random.uniform(2, 4)) 
                                current_page += 1
                                continue # Successfully clicked next
                            except Exception as e:
                                logger.warning(f"Failed to click next: {e}")
                        
                        # Fallback: Forced URL Manipulation (The "Expert" Move)
                        if self.platform == 'justdial':
                            logger.info(f"Standard navigation failed. Attempting forced URL for page {current_page + 1}")
                            # Justdial Pattern: /page-2, /page-3
                            # We need to construct it carefully. 
                            # If start_url is .../Pune/Plumber, next is .../Pune/Plumber/page-2
                            
                            # Remove existing /page-X if present (simple check)
                            base_clean = self.start_url.split('/page-')[0]
                            next_url = f"{base_clean}/page-{current_page + 1}"
                            
                            logger.info(f"Force navigating to: {next_url}")
                            await page.goto(next_url, timeout=60000, wait_until='domcontentloaded')
                            await asyncio.sleep(random.uniform(3, 5))
                            current_page += 1
                        else:
                            # If no next button and not Justdial, we are truly stuck
                            logger.info("No next page button found and no fallback available.")
                            break
                    else:
                        break
                        
            except Exception as e:
                logger.error(f"Fatal error during scraping: {e}")
                # Log traceback for expert debugging
                import traceback
                logger.error(traceback.format_exc())
            finally:
                # Expert mode: Force save before browser close
                try:
                    self.storage.save()
                    logger.info("State preserved successfully.")
                except Exception as save_err:
                    logger.error(f"Critical error saving state: {save_err}")
                
                try:
                    if 'browser' in locals() and browser:
                        await browser.close()
                    logger.info("Browser closed safely.")
                except:
                    pass

    async def _aggressive_scroll(self, page, target=100):
        """Scrolls progressively to trigger lazy loading."""
        logger.info(f"Aggressive scrolling... Aiming for ~{target} items")
        
        previous_height = await page.evaluate("document.body.scrollHeight")
        no_change_count = 0
        
        for i in range(25): # Max 25 scroll cycles
            # Scroll to current bottom
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await asyncio.sleep(random.uniform(1.5, 2.5))
            
            # Scroll up slightly to trigger "above fold" loaders
            await page.evaluate("window.scrollBy(0, -800)")
            await asyncio.sleep(0.5)
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            
            new_height = await page.evaluate("document.body.scrollHeight")
            
            if new_height == previous_height:
                no_change_count += 1
                if no_change_count >= 3:
                     # Check if we still need more items by counting containers
                     cards = await page.query_selector_all(self.selectors.get('listing_container', '.card'))
                     if len(cards) >= target * 0.8: # Close enough
                         logger.info(f"Loaded {len(cards)} items. Stopping scroll.")
                         break
                     else:
                         logger.info("Height stable but target not met. Waiting a bit longer...")
                         await asyncio.sleep(3)
                         no_change_count = 0 # Reset to try again
            else:
                no_change_count = 0
                
            previous_height = new_height
            if i % 5 == 0:
                logger.info(f"Scroll cycle {i}/25... Current page height: {new_height}")
