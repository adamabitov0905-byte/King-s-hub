import os
import discord
from discord.ext import commands
import requests
import time
import json
import base64
from flask import Flask
from threading import Thread

# ==========================================
# ВСТАВЬ СВОИ ЗНАЧЕНИЯ СЮДА (замени "..."):
# ==========================================
DISCORD_TOKEN = "MTU1OTg1MDY3MjAyMTcwMDYwOA.G567qa.VSWWkTWN7cRakBzU4Xdi-vObPTAW6ldCtrjap0"
GITHUB_TOKEN  = "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"
GITHUB_REPO   = "adamabitov0905-byte/king's hub"
OWNER_ID      = 1496466575052636211    # ← вставь свой Discord ID (число БЕЗ кавычек)
# ==========================================

# --- Мини-веб-сервер для Render (чтобы бот не засыпал) ---
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
# --------------------------------------------------------

bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())

def load_keys():
    url = f"https://raw.githubusercontent.com/{GITHUB_REPO}/main/Keys.json"
    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            return r.json()
    except Exception as e:
        print(f"[!] Ошибка загрузки: {e}")
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
        print(f"[!] Ошибка сохранения: {e}")
        return False

@bot.event
async def on_ready():
    print(f"✅ Бот {bot.user} готов!")
    print(f"👤 Владелец ID: {OWNER_ID}")
    print("Напиши !help в Discord")

@bot.command()
async def help(ctx):
    await ctx.send(
        "**👑 King's Hub Bot**\n"
        "`!addkey <HWID> <дни>` — добавить ключ\n"
        "`!removekey <HWID>` — удалить ключ\n"
        "`!list` — список всех ключей\n"
        "`!check <HWID>` — проверить статус\n"
        "`!stats` — сколько пользователей"
    )

@bot.command()
async def addkey(ctx, hwid: str, days: int = 7):
    if ctx.author.id != OWNER_ID:
        return
    data = load_keys()
    exp = int(time.time()) + days * 86400
    data["keys"][hwid] = {"expires": exp, "name": str(ctx.author)}
    if save_keys(data):
        await ctx.send(f"✅ HWID `{hwid}` добавлен на **{days}** дней")
    else:
        await ctx.send("❌ Ошибка сохранения в GitHub")

@bot.command()
async def removekey(ctx, hwid: str):
    if ctx.author.id != OWNER_ID:
        return
    data = load_keys()
    if hwid in data["keys"]:
        del data["keys"][hwid]
        save_keys(data)
        await ctx.send(f"🗑 HWID `{hwid}` удалён")
    else:
        await ctx.send("❌ HWID не найден")

@bot.command()
async def list(ctx):
    if ctx.author.id != OWNER_ID:
        return
    data = load_keys()
    if not data["keys"]:
        await ctx.send("📭 Список пуст")
        return
    txt = "**📋 Активные HWID:**\n"
    for hwid, info in data["keys"].items():
        exp = info["expires"]
        left = max(0, exp - int(time.time()))
        days = left // 86400
        txt += f"`{hwid}` — **{days}** дней\n"
    await ctx.send(txt)

@bot.command()
async def check(ctx, hwid: str):
    if ctx.author.id != OWNER_ID:
        return
    data = load_keys()
    info = data["keys"].get(hwid)
    if not info:
        await ctx.send("❌ Нет доступа")
        return
    left = max(0, info["expires"] - int(time.time()))
    await ctx.send(f"✅ Доступ активен, осталось **{left // 86400}** дней")

@bot.command()
async def stats(ctx):
    if ctx.author.id != OWNER_ID:
        return
    data = load_keys()
    await ctx.send(f"👥 Всего пользователей: **{len(data['keys'])}**")

# --- Запуск ---
if __name__ == "__main__":
    keep_alive()
    try:
        bot.run(DISCORD_TOKEN)
    except Exception as e:
        print(f"❌ Ошибка запуска: {e}")
