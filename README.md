# Facebook Rental Bot

A Python bot that monitors Facebook rental groups for apartments in the Rehavia area of Jerusalem, analyzes posts using OpenAI, and sends notifications to Telegram when matching apartments are found.

## Features
- Scrapes Facebook group posts using Playwright
- Uses OpenAI to analyze and filter posts based on strict criteria
- Sends Telegram notifications for matching apartments
- Keeps track of seen posts to avoid duplicates
- Deployable on Fly.io with scheduled hourly runs

## Setup

### 1. Clone the repository
```bash
git clone https://github.com/gidonschreiber/facebook_rental_bot.git
cd facebook_rental_bot
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Environment Variables
Create a `.env` file in the project root with the following variables:
```
OPENAI_API_KEY=your_openai_api_key
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_telegram_chat_id
```

### 4. Facebook Cookies
Export your Facebook cookies to a file named `cookies.json` in the project root. (Use browser extensions like EditThisCookie to export cookies while logged in.)

## Running Locally
```bash
python3 main.py
```

## Deployment (Fly.io)
- The project includes a `Dockerfile` and `fly.toml` for easy deployment to Fly.io.
- The bot is set up to run every hour using cron inside the container.
- To deploy:
  1. Install the [Fly.io CLI](https://fly.io/docs/hands-on/install-flyctl/)
  2. Run `fly launch` and follow the prompts
  3. Deploy with `fly deploy`

## Usage
- The bot will send a Telegram message when it finds a new apartment post that matches all criteria.
- If no matching apartment is found, it will send a fallback message: `ran now, no apartment found`.

## Criteria for Matching Apartments
- Located in the Rehavia area (by neighborhood or specific street names)
- Offering an apartment for rent (not searching)
- Rent is 7000₪ or less (or not mentioned)
- Move-in date between 2025-07-15 and 2025-09-15
- Entire apartment (not just a room)

---

**Maintainer:** [Gidon Schreiber](https://github.com/gidonschreiber) 