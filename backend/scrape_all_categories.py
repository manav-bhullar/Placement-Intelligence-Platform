import os
import asyncio
from dotenv import load_dotenv
from playwright.async_api import async_playwright

load_dotenv()

COOKIE_STRING = os.getenv("TIETPREP_COOKIE")
BASE_URL = "https://tietprep.humblesolutions.in"

async def scrape_all():
    if not COOKIE_STRING:
        print("Error: TIETPREP_COOKIE not found in .env")
        return

    print("Launching Playwright for automated scraping...")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        await context.set_extra_http_headers({'Cookie': COOKIE_STRING})
        page = await context.new_page()
        
        print(f"Navigating to {BASE_URL}...")
        await page.goto(BASE_URL)
        await page.wait_for_timeout(3000)
        
        # Find all category links
        print("Searching for category links on dashboard...")
        links = await page.evaluate('''() => {
            return Array.from(document.querySelectorAll('a'))
                .map(a => a.href)
                .filter(href => href.includes('/question-sets/'));
        }''')
        
        # Make links unique
        unique_links = list(set(links))
        print(f"Found {len(unique_links)} category links to scrape!")
        
        if not unique_links:
            print("No category links found! Saving debug HTML.")
            html = await page.content()
            with open("dashboard_debug.html", "w", encoding="utf-8") as f:
                f.write(html)
            await browser.close()
            return
            
        print("Starting massive scrape...")
        for i, link in enumerate(unique_links):
            print(f"Scraping [{i+1}/{len(unique_links)}]: {link}")
            try:
                await page.goto(link, wait_until="domcontentloaded", timeout=60000)
                await page.wait_for_timeout(3000) # Give React time to render questions
                
                # Get the page text, cleaning up excess whitespace
                page_text = await page.evaluate("document.body.innerText")
                
                # Write progressively so we don't lose data if it crashes
                with open("../tietprep_all_scraped.txt", "a", encoding="utf-8") as f:
                    f.write(f"\n\n{'='*70}\nSOURCE: {link}\n{'='*70}\n\n")
                    f.write(page_text)
                    
            except Exception as e:
                print(f"Failed to scrape {link}: {e}")
                
        print("Finished scraping all categories! Data safely saved to tietprep_all_scraped.txt")
        await browser.close()

if __name__ == "__main__":
    # Clear the output file if it exists
    out_file = "../tietprep_all_scraped.txt"
    if os.path.exists(out_file):
        os.remove(out_file)
    asyncio.run(scrape_all())
