import os, sqlite3, requests
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
SHOP = os.getenv("SHOPIFY_STORE")
SHOP_TOKEN = os.getenv("SHOPIFY_ACCESS_TOKEN")
API_VERSION = os.getenv("SHOPIFY_API_VERSION", "2026-07")
DB = "commerce.db"

def db():
    con = sqlite3.connect(DB)
    con.execute("""CREATE TABLE IF NOT EXISTS products(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        supplier_price REAL NOT NULL,
        sale_price REAL NOT NULL,
        stock INTEGER DEFAULT 0
    )""")
    con.commit()
    return con

def shopify_query(query, variables=None):
    if not SHOP or not SHOP_TOKEN:
        raise RuntimeError("Shopify is not configured.")
    url = f"https://{SHOP}/admin/api/{API_VERSION}/graphql.json"
    r = requests.post(url,
        headers={"X-Shopify-Access-Token": SHOP_TOKEN, "Content-Type": "application/json"},
        json={"query": query, "variables": variables or {}}, timeout=30)
    r.raise_for_status()
    data = r.json()
    if data.get("errors"):
        raise RuntimeError(str(data["errors"]))
    return data["data"]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 AI Commerce Bot V2\n\n"
        "/products — local catalog\n"
        "/shopify — Shopify products\n"
        "/orders — recent Shopify orders\n"
        "/add Name|buy|sell|stock — add local product\n"
        "/margin — local margins\n"
        "/status — system status"
    )

async def products(update, context):
    con = db()
    rows = con.execute("SELECT id,name,supplier_price,sale_price,stock FROM products").fetchall()
    con.close()
    if not rows:
        await update.message.reply_text("No local products yet.")
        return
    await update.message.reply_text("\n".join(
        f"#{r[0]} {r[1]} | buy ${r[2]:.2f} | sell ${r[3]:.2f} | stock {r[4]}" for r in rows
    ))

async def add(update, context):
    raw = " ".join(context.args)
    try:
        name, buy, sell, stock = [x.strip() for x in raw.split("|")]
        buy, sell, stock = float(buy), float(sell), int(stock)
        if min(buy, sell, stock) < 0: raise ValueError
    except ValueError:
        await update.message.reply_text("Format: /add Name|supplier_price|sale_price|stock")
        return
    con = db()
    con.execute("INSERT INTO products(name,supplier_price,sale_price,stock) VALUES(?,?,?,?)",
                (name, buy, sell, stock))
    con.commit(); con.close()
    await update.message.reply_text(f"✅ Added {name}. Gross/unit: ${sell-buy:.2f}")

async def margin(update, context):
    con = db()
    rows = con.execute("SELECT name,supplier_price,sale_price FROM products").fetchall()
    con.close()
    if not rows:
        await update.message.reply_text("No products.")
        return
    await update.message.reply_text("\n".join(
        f"{n}: ${s-b:.2f}/unit ({((s-b)/s*100 if s else 0):.1f}%)"
        for n,b,s in rows
    ))

async def shopify(update, context):
    try:
        data = shopify_query("""query {
          products(first: 20) { nodes { id title status } }
        }""")
        nodes = data["products"]["nodes"]
        if not nodes:
            await update.message.reply_text("Shopify has no products.")
            return
        await update.message.reply_text("\n".join(
            f"{n['title']} — {n['status']}" for n in nodes
        ))
    except Exception as e:
        await update.message.reply_text(f"Shopify error: {e}")

async def orders(update, context):
    try:
        data = shopify_query("""query {
          orders(first: 20, sortKey: CREATED_AT, reverse: true) {
            nodes { name displayFinancialStatus totalPriceSet { shopMoney { amount currencyCode } } }
          }
        }""")
        nodes = data["orders"]["nodes"]
        if not nodes:
            await update.message.reply_text("No orders returned.")
            return
        await update.message.reply_text("\n".join(
            f"{n['name']} — {n['displayFinancialStatus']} — "
            f"{n['totalPriceSet']['shopMoney']['amount']} {n['totalPriceSet']['shopMoney']['currencyCode']}"
            for n in nodes
        ))
    except Exception as e:
        await update.message.reply_text(f"Shopify error: {e}")

async def status(update, context):
    con = db()
    count = con.execute("SELECT COUNT(*) FROM products").fetchone()[0]
    con.close()
    shop = "configured" if SHOP and SHOP_TOKEN else "not configured"
    await update.message.reply_text(
        f"🟢 Bot online\nLocal products: {count}\nShopify: {shop}\n"
        "Automatic supplier purchases: OFF\nAutomatic payouts: OFF"
    )

def main():
    if not TOKEN:
        raise SystemExit("Set TELEGRAM_BOT_TOKEN in .env")
    db().close()
    app = Application.builder().token(TOKEN).build()
    for command, handler in [
        ("start", start), ("products", products), ("add", add),
        ("margin", margin), ("shopify", shopify), ("orders", orders), ("status", status)
    ]:
        app.add_handler(CommandHandler(command, handler))
    app.run_polling()

if __name__ == "__main__":
    main()
