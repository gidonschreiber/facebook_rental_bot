import os
import json
import openai
import requests
import asyncio
import re
from datetime import datetime, timedelta
from playwright.async_api import async_playwright
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

with open("cookies.json", "r") as f:
    COOKIES = json.load(f)

FB_GROUP_ID = "2231582410418022"
FB_URL = f"https://www.facebook.com/groups/{FB_GROUP_ID}"
SEEN_FILE = "seen_post_ids.json"

def load_seen_ids():
    try:
        with open(SEEN_FILE, "r") as f:
            return set(json.load(f))
    except FileNotFoundError:
        return set()

def save_seen_ids(seen_ids):
    with open(SEEN_FILE, "w") as f:
        json.dump(list(seen_ids), f)

def analyze_with_openai(text):
    prompt = f"""You are a real estate assistant. The following post contains a mixture of content, including metadata such as usernames, dates, irrelevant formatting, and comments to the post. 
    Extract and isolate the main post body (i.e., the written content by the poster).
    Then determine if it matches ALL of the following criteria:
definition of Rehavia area: if it says Rehavia neighbourhood, or if it is on one of the following streets:
rehavia_street_names = [
    "עזה", "אלפסי", "קק\"ל", "רמב\"ן", "אבן עזרא", "הרב הרצוג",
    "האר\"י", "הנשיא", "נילי", "רד\"ק", "בן מימון", "רש\"י",
    "שטיינברג", "בלפור", "אברבנאל", "רייכנברג", "דובנוב",
    "צייטלין", "רחל אמנו", "ישעיהו ברלין", "יהושע ייבין",
    "הפלמ\"ח", "הרב עוזיאל", "החבצלת", "לוצאטו", "דוד ילין",
    "יונה", "אולסוונגר", "בורוכוב", "המתמיד", "מרמורק",
    "מטודלה", "בן לברת", "שדרות בן צבי", "יוסף פישמן", "רבי חנינא",
    "שמואל הנגיד", "ש\"י עגנון", "הלל", "קרן היסוד"
]

- The poster is offering an apartment for rent (not searching for one)
- Rent is 7000₪ or less (if price is not mentioned, that's also OK)
- Located in the Rehavia area
- Move-in date is between 2025-07-15 and 2025-09-15 inclusive
- It is an entire apartment, not just a room


If it meets all criteria, output:
CRITERIA MET
מצאנו דירה בשבילך!
מיקום - [location]
מחיר - [price]
גודל - [size]
חדרים - [rooms]
תאריך כניסה - [move_in_date]
איש קשר - [contact]

Post:
{text}
"""

    try:
        response = client.chat.completions.create(
            #model="gpt-3.5-turbo",
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
        )
        result = response.choices[0].message.content
        return result.strip()
    except Exception as e:
        print("OpenAI error:", e)
        return None

# def send_telegram(info, link):
#     text = f"""**New Rental Match**
# Location: {info['location']}
# Price: {info['price']}
# Size: {info['size']}
# Rooms: {info['rooms']}
# Move-in: {info['move_in_date']} | Flexible: {info['flexible_move_in']}
# Contact: {info['contact']}
# [View Post]({link})"""
#     requests.post(
#         f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
#         json={"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode": "Markdown"}
#     )


def send_telegram(openai_result_text, link):
    # Extract only the part after 'CRITERIA MET'
    if "CRITERIA MET" in openai_result_text:
        message = openai_result_text.split("CRITERIA MET", 1)[1].strip()
    else:
        message = openai_result_text.strip()
    text = f"{message}\n\n[View Post]({link})"
    print(f"[DEBUG] Sending Telegram message: {text}")
    resp = requests.post(
        f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
        json={
            "chat_id": TELEGRAM_CHAT_ID,
            "text": text,
            "parse_mode": "Markdown"
        }
    )
    print(f"[DEBUG] Telegram API response: {resp.status_code} {resp.text}")


async def collect_post_links(page, max_posts=10):
    links = []
    articles = await page.query_selector_all("div[role='article']")

    for post in articles:
        try:
            a = await post.query_selector(f"a[href*='/groups/{FB_GROUP_ID}/posts/']")
            if not a:
                continue
            href = await a.get_attribute("href")
            if not href or "posts/" not in href:
                continue
            post_id = href.split("posts/")[-1].split("/")[0]
            clean_href = href.split("?")[0]
            full_url = f"https://www.facebook.com/groups/{FB_GROUP_ID}/posts/{post_id}/"

            if post_id and (post_id, full_url) not in links:
                links.append((post_id, full_url))
        except Exception as e:
            print("Link error:", e)
            continue

        if len(links) >= max_posts:
            break

    return links

async def run():
    seen_ids = load_seen_ids()
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36"
        )
        await context.add_cookies(COOKIES)
        group_page = await context.new_page()

        print("🔄 Loading group page...")
        await group_page.goto(FB_URL, timeout=60000)
        await group_page.wait_for_timeout(2000)

        scroll_attempts = 0
        links = []
        while True:
            new_links = await collect_post_links(group_page, max_posts=10)
            for link in new_links:
                if link not in links:
                    links.append(link)
            if len(links) >= 10:
                print("✅ Got 10 links. Done scrolling.")
                break
            if scroll_attempts >= 20:
                print("🛑 Hit scroll cap (20 attempts). Stopping.")
                break
            await group_page.mouse.wheel(0, 3000)
            await group_page.wait_for_selector("div[role='article']", timeout=8000)
            await group_page.wait_for_timeout(1000)
            scroll_attempts += 1

        links = await collect_post_links(group_page, max_posts=10)
        print(f"🔗 Found {len(links)} post links")
        apartment_found = False

        for post_id, link in links:
            if post_id in seen_ids:
                continue

            try:
                print(f"\n➡️ Visiting post {post_id}")
                post_page = await context.new_page()
                await post_page.goto(link, timeout=60000)
                await post_page.wait_for_timeout(2000)
                #await post_page.screenshot(path=f"post_{post_id}.png", full_page=True)

                try:
                    see_more = await post_page.query_selector("div[role='button']:has-text('See more')")
                    if see_more:
                        await see_more.click()
                        await post_page.wait_for_timeout(1000)
                except:
                    pass

                dialog = await post_page.query_selector("div[role='dialog']")
                if not dialog:
                    print("❌ Skipped: post dialog not found.")
                    await post_page.close()
                    continue
                post_text_nodes = await dialog.query_selector_all("div[dir='auto']")
                all_text_parts = [await node.inner_text() for node in post_text_nodes]
                all_text = "".join(all_text_parts)
                print(f"✅ Post content:{all_text}")
                

                try:
                    result = analyze_with_openai(all_text)
                    print("🤖 OpenAI result:", repr(result))
                    send_notification = isinstance(result, str) and result and result.lstrip().upper().startswith("CRITERIA MET")
                    print(f"[DEBUG] send_notification: {send_notification}")
                except Exception as err:
                    print(f"❗ OpenAI parsing error for post {post_id}:", err)
                    result = None
                    send_notification = False

                if send_notification:
                    send_telegram(result, link)
                    apartment_found = True
                seen_ids.add(post_id)

                await post_page.close()

            except Exception as e:
                print(f"❗ Error visiting post {post_id}:", e)

        if not apartment_found:
            send_telegram("ran now, no apartment found", "N/A")
        await browser.close()
        save_seen_ids(seen_ids)

if __name__ == "__main__":
    asyncio.run(run())
