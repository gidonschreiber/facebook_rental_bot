import asyncio
from playwright.async_api import async_playwright
import os
import json

FB_GROUP_ID = "2231582410418022"
FB_URL = f"https://www.facebook.com/groups/{FB_GROUP_ID}"

# Load cookies from your existing file
with open("cookies.json", "r") as f:
    COOKIES = json.load(f)

async def check_for_utime():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=100)
        context = await browser.new_context(user_agent="Mozilla/5.0")
        await context.add_cookies(COOKIES)
        page = await context.new_page()
        await page.goto(FB_URL, timeout=60000)
        await page.wait_for_timeout(3000)

        articles = await page.query_selector_all("div[role='article']")
        print(f"Found {len(articles)} articles.")

        for idx, article in enumerate(articles[:10]):
            abbr = await article.query_selector("abbr[data-utime]")
            if abbr:
                utime = await abbr.get_attribute("data-utime")
                print(f"✅ Article {idx+1} has data-utime: {utime}")
            else:
                print(f"❌ Article {idx+1} has no data-utime.")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(check_for_utime())
