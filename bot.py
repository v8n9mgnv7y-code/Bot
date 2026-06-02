from dotenv import load_dotenv
import discord
from discord.ext import commands
import json
import time
import os
import traceback

load_dotenv()

TOKEN = os.getenv("TOKEN")

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

DATA_FILE = "voice_time.json"

if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        voice_data = json.load(f)
else:
    voice_data = {}

active_sessions = {}

VOICE_ROLES = [
    (100 * 3600, "Гуру войса"),
    (70 * 3600, "Свояк"),
    (30 * 3600, "Крутой Парень"),
    (10 * 3600, "Я конкретно знаю че происходит"),
    (5 * 3600, "Думаешь я не шарю ?"),
    (1 * 3600, "Я тут пока посижу"),
]

def format_time(seconds):
    seconds = int(seconds)
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    return f"{hours} ч. {minutes} мин."


async def update_roles(member, total_time):
    guild = member.guild

    for time_req, role_name in VOICE_ROLES:
        role = discord.utils.get(guild.roles, name=role_name)
        if not role:
            continue

        if total_time >= time_req:
            if role not in member.roles:
                await member.add_roles(role)
        else:
            if role in member.roles:
                await member.remove_roles(role)


@bot.event
async def on_ready():
    print(f"Бот запущен как {bot.user}")


@bot.event
async def on_voice_state_update(member, before, after):
    try:
        print("VOICE EVENT:", member, before.channel, "->", after.channel)

        user_id = str(member.id)

        # вход в войс
        if before.channel is None and after.channel is not None:
            active_sessions[user_id] = time.time()

        # выход из войса
        elif before.channel is not None and after.channel is None:
            start = active_sessions.pop(user_id, None)

            if start is None:
                return

            session_time = int(time.time() - start)

            voice_data[user_id] = voice_data.get(user_id, 0) + session_time

            save_data()

    except Exception:
        print("❌ ERROR IN VOICE EVENT:")
        traceback.print_exc()


@bot.command()
async def voice(ctx, member: discord.Member = None):
    if member is None:
        member = ctx.author

    user_id = str(member.id)

    total = voice_data.get(user_id, 0)

    if user_id in active_sessions:
        total += time.time() - active_sessions[user_id]

    await ctx.send(
        f"{member.display_name} провёл в голосовых каналах: {format_time(total)}"
    )


@bot.command()
async def topvoice(ctx):
    ranking = []

    for user_id, total_time in voice_data.items():
        member = ctx.guild.get_member(int(user_id))

        if member:
            live = 0

            if user_id in active_sessions:
                live = time.time() - active_sessions[user_id]

            ranking.append((member.display_name, total_time + live))

    ranking.sort(key=lambda x: x[1], reverse=True)

    if not ranking:
        await ctx.send("Статистика пока пуста.")
        return

    text = "🏆 Топ по голосовому времени:\n\n"

    for i, (name, total) in enumerate(ranking[:10], start=1):
        text += f"{i}. {name} — {format_time(total)}\n"

    await ctx.send(text)


bot.run(os.getenv("TOKEN"))