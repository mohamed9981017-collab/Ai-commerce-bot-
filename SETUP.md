# V2 setup

1. Create a Telegram bot with Telegram's official BotFather.
2. Copy the bot token into `.env` as `TELEGRAM_BOT_TOKEN`.
3. Create/connect a Shopify store and create an app with only the API scopes actually needed.
4. Put the store domain and access token into `.env`.
5. Run:
   `pip install -r requirements.txt`
   `python bot.py`
6. Open Telegram and send `/start`.

Security:
- Never send your token, Shopify access token, bank login, card PIN, or passwords to anyone.
- V2 intentionally does not place supplier purchases or move money automatically.
- Test with a development store before using a live store.
