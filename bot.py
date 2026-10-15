import os
import discord
from discord.ext import commands
import requests
import time
import json
import base64
from flask import Flask
from threading import Thread

# Токены берутся из GitHub Secrets (не пиши их сюда!)
DISCORD_TOKEN = os.environ.get("DISCORD_TOKEN")
GITHUB_TOKEN  = os.environ.get("GITHUB_TOKEN")
GITHUB_REPO   = "adamabitov0905-byte/King-s-hub"
OWNER_ID      = int(os.environ.get("OWNER_ID", 0))

app = Flask('')

@app.route('/')
def home():
    return "King's Hub Bot is alive!"

def run_web():
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run_web)
    t.daemon = True
    t.start()

bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())

def load_keys():
    url = f"https://raw.githubusercontent.com/{GITHUB_REPO}/main/Keys.json"
    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            return r.json()
    except Exception as e:
        print(f"[!] Load error: {e}")
    return {"keys": {}}

def save_keys(data):
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/Keys.json"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    try:
        r = requests.get(url, headers=headers)
        sha = r.json().get("sha") if r.status_code == 200 else None
        content = base64.b64encode(json.dumps(data, indent=2).encode()).decode()
        payload = {"message": "update keys", "content": content}
        if sha:
            payload["sha"] = sha
        r = requests.put(url, headers=headers, json=payload)
        return r.status_code in (200, 201)
    except Exception as e:
        print(f"[!] Save error: {e}")
        return False

@bot.event
async def on_ready():
    print(f"OK: {bot.user}")
    print(f"Owner ID: {OWNER_ID}")

@bot.command()
async def help(ctx):
    await ctx.send(
        "**King's Hub Bot**\n"
        "`!addkey <HWID> <дни>`\n"
        "`!removekey <HWID>`\n"
        "`!list`\n"
        "`!check <HWID>`\n"
        "`!stats`"
    )

@bot.command()
async def addkey(ctx, hwid: str, days: int = 36500):
    if ctx.author.id != OWNER_ID: return
    data = load_keys()
    data["keys"][hwid] = {"expires": int(time.time()) + days * 86400, "name": str(ctx.author)}
    if save_keys(data):
        await ctx.send(f"OK: `{hwid}` на **{days}** дней")
    else:
        await ctx.send("FAIL: сохранение")

@bot.command()
async def removekey(ctx, hwid: str):
    if ctx.author.id != OWNER_ID: return
    data = load_keys()
    if hwid in data["keys"]:
        del data["keys"][hwid]
        save_keys(data)
        await ctx.send(f"Удалён: `{hwid}`")
    else:
        await ctx.send("Не найден")

@bot.command()
async def list(ctx):
    if ctx.author.id != OWNER_ID: return
    data = load_keys()
    if not data["keys"]:
        await ctx.send("Пусто"); return
    txt = "**Активные:**\n"
    for hwid, info in data["keys"].items():
        days = max(0, info["expires"] - int(time.time())) // 86400
        txt += f"`{hwid}` — {days} дн.\n"
    await ctx.send(txt)

@bot.command()
async def check(ctx, hwid: str):
    if ctx.author.id != OWNER_ID: return
    data = load_keys()
    info = data["keys"].get(hwid)
    if not info:
        await ctx.send("Нет доступа"); return
    days = max(0, info["expires"] - int(time.time())) // 86400
    await ctx.send(f"Осталось: **{days}** дней")

@bot.command()
async def stats(ctx):
    if ctx.author.id != OWNER_ID: return
    data = load_keys()
    await ctx.send(f"Всего: **{len(data['keys'])}**")

if __name__ == "__main__":
    keep_alive()
    try:
        bot.run(DISCORD_TOKEN)
    except Exception as e:
        print(f"Ошибка: {e}")
