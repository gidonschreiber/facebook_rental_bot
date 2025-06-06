FROM python:3.10-slim

# Install system dependencies including cron and required libraries
RUN apt-get update && apt-get install -y cron gcc g++ libpq-dev && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy the requirements file and install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Install Playwright and its browsers
RUN pip install playwright && playwright install --with-deps

# Copy the rest of the application code
COPY . .

# Setup cron job to run the bot every hour at minute 0
RUN echo "0 * * * * cd /app && python main.py >> cron.log 2>&1" > /etc/cron.d/facebook_rental_bot_cron \
    && chmod 0644 /etc/cron.d/facebook_rental_bot_cron \
    && crontab /etc/cron.d/facebook_rental_bot_cron

# Create the cron log file
RUN touch cron.log

# Run cron in foreground and tail the log file so the container doesn't exit
CMD cron && tail -f cron.log
