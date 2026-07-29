import os
import asyncio
from dotenv import load_dotenv
from playwright.async_api import async_playwright

load_dotenv()

USERNAME = os.getenv("TIETPREP_USERNAME")
PASSWORD = os.getenv("TIETPREP_PASSWORD")
BASE_URL = "https://tietprep.humblesolutions.in"

async def test_login():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        
        print("Navigating to homepage...")
        await page.goto(BASE_URL)
        await page.wait_for_timeout(3000)
        
        print("Trying to find email input...")
        try:
            await page.fill('input[type="email"]', USERNAME)
            await page.fill('input[type="password"]', PASSWORD)
            await page.click('button')
            print("Clicked login button, waiting 5 seconds...")
            await page.wait_for_timeout(5000)
            
            html = await page.content()
            with open("post_login.html", "w", encoding="utf-8") as f:
                f.write(html)
            print("Successfully logged in! Saved post_login.html")
        except Exception as e:
            print(f"Login failed: {e}")
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_login())
