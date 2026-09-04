# AI Commerce Telegram Bot — V1

A starter Telegram-controlled e-commerce automation system.

## What V1 does
- Telegram commands for products, margins, and status
- Product catalog stored locally in SQLite
- Margin calculation
- Simple product import through a JSON file
- Safety-first order workflow: no automatic purchases or payouts

## Run
1. Install Python 3.11+.
2. Install dependencies:
   `pip install -r requirements.txt`
3. Create a Telegram bot with BotFather and set `TELEGRAM_BOT_TOKEN` as an environment variable.
4. Run:
   `python bot.py`

Never put your bank password, card PIN, or banking login in this project.
