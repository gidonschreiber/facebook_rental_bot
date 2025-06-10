import asyncio
from playwright.async_api import async_playwright

PROFILE_DIR = "fb_profile"  # This directory will store your session

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch_persistent_context(
            PROFILE_DIR,
            headless=False,
            slow_mo=100,
        )
        page = await browser.new_page()
        await page.goto("https://www.facebook.com/")
        print("Please log in to Facebook manually in the opened browser window.")
        print("You have up to 15 minutes. Only close the window after you see your news feed and are fully logged in.")
        await page.wait_for_timeout(1000 * 60 * 15)  # Wait up to 15 minutes for manual login
        await browser.close()

asyncio.run(main()) 