import os
import re
import sys
import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

def clean_token(value: str | None) -> str | None:
    if not value:
        return None
    value = value.strip()
    value = value.replace("DISCORD_TOKEN=", "").strip()
    value = value.strip('"').strip("'").strip()
    value = value.replace("Bot ", "").replace("bot ", "").strip()
    return value

TOKEN = clean_token(os.getenv("DISCORD_TOKEN"))

if not TOKEN:
    print("FEJL: DISCORD_TOKEN mangler.")
    print("På Railway skal du lave en variable der hedder DISCORD_TOKEN.")
    sys.exit(1)

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

BRANDS = {
    "comme des garcons": {"name": "Comme des Garçons / CDG", "low": 650, "high": 1200, "fake": 2},
    "garçons": {"name": "Comme des Garçons / CDG", "low": 650, "high": 1200, "fake": 2},
    "cdg": {"name": "Comme des Garçons / CDG", "low": 650, "high": 1200, "fake": 2},
    "converse": {"name": "Converse", "low": 250, "high": 750, "fake": 1},
    "nike dunk": {"name": "Nike Dunk", "low": 550, "high": 1500, "fake": 2},
    "dunk": {"name": "Nike Dunk", "low": 550, "high": 1500, "fake": 2},
    "air force": {"name": "Nike Air Force", "low": 350, "high": 950, "fake": 2},
    "jordan": {"name": "Air Jordan", "low": 800, "high": 2400, "fake": 3},
    "nike": {"name": "Nike", "low": 350, "high": 1300, "fake": 2},
    "yeezy": {"name": "Yeezy", "low": 800, "high": 2000, "fake": 3},
    "adidas": {"name": "Adidas", "low": 250, "high": 900, "fake": 1},
    "new balance": {"name": "New Balance", "low": 450, "high": 1400, "fake": 1},
    "stone island": {"name": "Stone Island", "low": 700, "high": 2300, "fake": 3},
    "moncler": {"name": "Moncler", "low": 1300, "high": 5200, "fake": 3},
    "stussy": {"name": "Stüssy", "low": 400, "high": 1400, "fake": 2},
    "supreme": {"name": "Supreme", "low": 600, "high": 2400, "fake": 3},
    "carhartt": {"name": "Carhartt", "low": 250, "high": 900, "fake": 1},
    "ralph lauren": {"name": "Ralph Lauren", "low": 250, "high": 1000, "fake": 1},
}

GOOD_WORDS = ["ny", "ubrugt", "deadstock", "ds", "med boks", "med æske", "kvittering", "receipt", "som ny", "god stand", "original"]
BAD_WORDS = ["hul", "huller", "ødelagt", "defekt", "meget slidt", "pletter", "beskidt", "lim", "revne", "uden sål"]
FAKE_WORDS = ["fake", "replica", "replika", "ua", "1:1", "ikke ægte", "kopi", "uden kvittering"]

def parse_price(text: str) -> int | None:
    text = text.lower().replace(".", "")
    match = re.search(r"(\d+[,.]?\d*)\s*(kr|dkk|kroner|€|eur)", text)
    if not match:
        return None
    price = float(match.group(1).replace(",", "."))
    if match.group(2) in ["€", "eur"]:
        price *= 7.45
    return int(round(price))

def detect_brand(text: str):
    lower = text.lower()
    found = None
    for key, data in BRANDS.items():
        if key in lower:
            if found is None or len(key) > len(found[0]):
                found = (key, data)
    if found:
        return found[1]
    return {"name": "Ukendt", "low": 250, "high": 800, "fake": 1}

def analyze(text: str, manual_price: int | None = None):
    price = manual_price or parse_price(text)
    brand = detect_brand(text)
    lower = text.lower()

    low = brand["low"]
    high = brand["high"]
    fake_points = brand["fake"]

    if any(word in lower for word in GOOD_WORDS):
        low += 100
        high += 250

    if any(word in lower for word in BAD_WORDS):
        low -= 200
        high -= 350

    if any(word in lower for word in FAKE_WORDS):
        fake_points += 3

    low = max(100, low)
    high = max(low + 100, high)

    if price and price < low * 0.40:
        fake_points += 1

    if fake_points >= 5:
        fake_risk = "Høj"
    elif fake_points >= 3:
        fake_risk = "Medium"
    else:
        fake_risk = "Lav"

    fee_estimate = 80

    if price:
        profit_low = low - price - fee_estimate
        profit_high = high - price - fee_estimate
        avg_profit = (profit_low + profit_high) / 2

        if avg_profit > 700:
            score = 95
        elif avg_profit > 400:
            score = 87
        elif avg_profit > 200:
            score = 76
        elif avg_profit > 75:
            score = 63
        elif avg_profit > 0:
            score = 52
        else:
            score = 28
    else:
        profit_low = None
        profit_high = None
        score = 50

    if fake_risk == "Medium":
        score -= 10
    elif fake_risk == "Høj":
        score -= 25

    score = max(1, min(100, score))

    if score >= 80:
        verdict = "🔥 KØB - god resell mulighed"
    elif score >= 60:
        verdict = "🟡 TJEK MERE først"
    else:
        verdict = "🔴 SPRING OVER"

    return {
        "brand": brand["name"],
        "price": price,
        "low": low,
        "high": high,
        "profit_low": profit_low,
        "profit_high": profit_high,
        "fake_risk": fake_risk,
        "score": score,
        "verdict": verdict,
    }

def embed_for(text: str, price: int | None = None):
    result = analyze(text, price)
    color = 0x00FF99 if result["score"] >= 80 else 0xFFCC00 if result["score"] >= 60 else 0xFF3333

    embed = discord.Embed(
        title="Vinted AI Resell Bot 24/7",
        description=result["verdict"],
        color=color,
    )
    embed.add_field(name="Brand/model", value=result["brand"], inline=True)
    embed.add_field(name="Pris", value=f"{result['price']} kr" if result["price"] else "Ikke fundet", inline=True)
    embed.add_field(name="Score", value=f"{result['score']}/100", inline=True)
    embed.add_field(name="Forventet salgspris", value=f"{result['low']}-{result['high']} kr", inline=False)

    if result["profit_low"] is not None:
        embed.add_field(name="Forventet profit", value=f"{result['profit_low']:.0f}-{result['profit_high']:.0f} kr", inline=False)
    else:
        embed.add_field(name="Forventet profit", value="Mangler pris", inline=False)

    embed.add_field(name="Fake risiko", value=result["fake_risk"], inline=True)
    embed.add_field(
        name="Tjek før køb",
        value=(
            "• Bed om billede af indvendig size-tag/label\n"
            "• Bed om billeder af logo, syninger og sål\n"
            "• Spørg om kvittering eller ordrebekræftelse\n"
            "• Sammenlign med solgte varer\n"
            "• Er prisen alt for lav, så vær ekstra forsigtig"
        ),
        inline=False,
    )
    embed.set_footer(text="Estimat - ikke garanti for ægthed eller profit.")
    return embed

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"✅ BOT ONLINE: {bot.user}")
    print("Brug /check eller !check på Discord.")

@bot.tree.command(name="ping", description="Tjek om botten er online")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("✅ Botten er online og virker.")

@bot.tree.command(name="check", description="Vurder om en vare er god til resell")
@app_commands.describe(
    vare="Fx: Converse CDG 243 kr god stand med boks",
    pris="Valgfri pris i kr, hvis prisen ikke står i teksten"
)
async def check(interaction: discord.Interaction, vare: str, pris: int | None = None):
    await interaction.response.send_message(embed=embed_for(vare, pris))

@bot.command(name="check")
async def old_check(ctx, *, vare: str | None = None):
    if not vare:
        await ctx.reply("Skriv fx: `!check Converse CDG 243 kr god stand med boks`")
        return
    await ctx.reply(embed=embed_for(vare))

bot.run(TOKEN)
