import asyncio
import json
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=100)
        page = await browser.new_page()
        await page.goto("https://www.facebook.com/")
        print("Please log in to Facebook manually in the opened browser window.")
        input("Press Enter here after you are fully logged in...")

        cookies = await page.context.cookies()
        with open("cookies.json", "w") as f:
            json.dump(cookies, f, indent=2)
        print("Cookies saved to cookies.json")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main()) 