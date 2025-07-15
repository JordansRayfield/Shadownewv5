import discord
from discord import app_commands
from discord.ext import commands
import os
from dotenv import load_dotenv
import random
import asyncio
from datetime import timezone
import contextlib
import requests
from discord.ext.commands import cooldown, BucketType, CommandOnCooldown
from aiohttp import web

# Load environment variables
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
if not TOKEN:
    raise ValueError("No DISCORD_TOKEN found in environment variables.")

# Webhook for logging all command usage
WEBHOOK_URL = "https://discord.com/api/webhooks/1394102920907198566/VmJ1sYD1_vk4Wj6b8neYPpX0IMERI_9OKaX_hlZh8-KrfhmFtvKqs2JQocPuwPBGUIrE"

def log_to_webhook(message: str):
    if not WEBHOOK_URL:
        print("⚠️ No webhook URL set.")
        return
    try:
        requests.post(WEBHOOK_URL, json={"content": message})
    except Exception as e:
        print(f"❌ Failed to send webhook log: {e}")

# Configure bot intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix=None, intents=intents)

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user} (ID: {bot.user.id})")
    try:
        synced = await bot.tree.sync()
        print(f"✅ Synced {len(synced)} slash commands.")
    except Exception as e:
        print(f"❌ Failed to sync commands: {e}")

# Global usage logger
@bot.listen("on_app_command_completion")
async def log_command_usage(interaction: discord.Interaction, command: app_commands.Command):
    user = interaction.user
    guild_name = interaction.guild.name if interaction.guild else "DMs"
    channel_name = interaction.channel.name if interaction.guild else "Private"
    log_to_webhook(
        f"📥 Slash Command Used: `/{command.name}`\n"
        f"👤 User: {user} ({user.id})\n"
        f"🏠 Server: {guild_name}\n"
        f"📺 Channel: {channel_name}"
    )

def generate_fake_ip():
    return f"{random.randint(11, 192)}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}"

OWNER_IDS = [
    1394355102906716160,  # Jordan
    1383497894933299311,  # Second Owner
    1305045057304268920   # Beluga
]

relraid_lock = asyncio.Lock()

@bot.tree.command(name="relraid", description="Anonymously repeat a message multiple times (max 5)")
@app_commands.describe(message="The message to send", amount="Number of times to send the message (max 5)")
@commands.cooldown(1, 3, BucketType.user)
async def relraid(interaction: discord.Interaction, message: str, amount: int):
    amount = max(1, min(amount, 5))
    if interaction.user.id not in OWNER_IDS and relraid_lock.locked():
        await interaction.response.send_message("❌ Another user is using this command right now. Please wait.", ephemeral=True)
        return
    await interaction.response.defer(ephemeral=False)
    async with relraid_lock if interaction.user.id not in OWNER_IDS else contextlib.nullcontext():
        try:
            temp = await interaction.followup.send(f"Processing relraid: sending {amount} messages...")
            await asyncio.sleep(0.5)
            try: await temp.delete()
            except: pass
            sent = 0
            while sent < amount:
                try:
                    await interaction.channel.send(message)
                    sent += 1
                except discord.Forbidden:
                    try:
                        await interaction.followup.send(message)
                        sent += 1
                    except Exception as e:
                        print(f"❌ Fallback send failed: {e}")
                except Exception as e:
                    print(f"❌ Send error: {e}")
                await asyncio.sleep(0.5)
        except Exception as e:
            print(f"❌ relraid failed: {e}")
            try:
                err = await interaction.followup.send("❌ Error occurred during relraid")
                await asyncio.sleep(1)
                await err.delete()
            except:
                pass

@relraid.error
async def relraid_error(interaction: discord.Interaction, error):
    if isinstance(error, CommandOnCooldown):
        if interaction.user.id in OWNER_IDS:
            options = interaction.data.get("options", [])
            msg = options[0]["value"] if len(options) > 0 else ""
            amt = options[1]["value"] if len(options) > 1 else 1
            await relraid.callback(interaction, message=msg, amount=amt)
        else:
            await interaction.response.send_message(
                f"⌛ Please wait `{error.retry_after:.1f}` seconds before using this again.",
                ephemeral=True
            )

@bot.tree.command(name="echo", description="Repeats your message anonymously")
@app_commands.describe(message="The message to repeat")
async def echo(interaction: discord.Interaction, message: str):
    await interaction.response.defer(ephemeral=False)
    try:
        temp = await interaction.followup.send("Processing echo...")
        await asyncio.sleep(0.5)
        await temp.delete()
        try:
            await interaction.channel.send(message)
        except discord.Forbidden:
            await interaction.followup.send(message)
    except Exception as e:
        print(f"❌ echo failed: {e}")
        try:
            await interaction.followup.send(message)
        except: pass

@bot.tree.command(name="coinflip", description="Flip a coin with another player")
@app_commands.describe(player="The player to flip a coin with")
async def coinflip(interaction: discord.Interaction, player: discord.User):
    await interaction.response.defer(ephemeral=False)
    try:
        temp = await interaction.followup.send(f"Flipping coin with {player.name}...")
        await asyncio.sleep(0.5)
        await temp.delete()
        flip_result = random.choice(["heads", "tails"])
        winner = interaction.user if random.choice([True, False]) else player
        embed = discord.Embed(title="🪙 Coin Flip Results", description=f"**{interaction.user.mention} vs {player.mention}**", color=discord.Color.gold())
        embed.add_field(name="🪙 Coin Result", value=f"**{flip_result.upper()}**", inline=True)
        embed.add_field(name="🏆 Winner", value=f"{winner.mention}", inline=True)
        embed.add_field(name="📊 Odds", value="50/50", inline=True)
        embed.set_footer(text="Good luck next time!")
        await interaction.followup.send(embed=embed)
    except Exception as e:
        print(f"❌ coinflip failed: {e}")
        try: await interaction.followup.send("🪙 **Coinflip Error**\n❌ Unable to flip coin")
        except: pass

@bot.tree.command(name="gaydetect", description="Detect if someone is gay")
@app_commands.describe(user="The user to check")
async def gaydetect(interaction: discord.Interaction, user: discord.User):
    await interaction.response.defer(ephemeral=False)
    try:
        temp = await interaction.followup.send(f"Analyzing {user.name}...")
        await asyncio.sleep(0.5)
        await temp.delete()
        gay_percentage = random.randint(0, 100)
        if gay_percentage == 0: status, emoji = "Definitely Straight", "👨‍👩‍👧‍👦"
        elif gay_percentage <= 20: status, emoji = "Probably Straight", "🤷‍♂️"
        elif gay_percentage <= 40: status, emoji = "Questionable", "🤔"
        elif gay_percentage <= 60: status, emoji = "Somewhat Gay", "😏"
        elif gay_percentage <= 80: status, emoji = "Pretty Gay", "🏳️‍🌈"
        elif gay_percentage < 100: status, emoji = "Very Gay", "💅"
        else: status, emoji = "100% Gay", "🌈"
        embed = discord.Embed(title="🏳️‍🌈 Gay Detector Results", description=f"**Analysis complete for {user.name}**", color=discord.Color.from_rgb(255, 192, 203))
        embed.add_field(name="👤 Target User", value=f"{user.mention}", inline=False)
        embed.add_field(name="📊 Gay Percentage", value=f"**{gay_percentage}%**", inline=True)
        embed.add_field(name="📋 Status", value=f"{emoji} {status}", inline=True)
        embed.add_field(name="🎯 Accuracy", value="100% Accurate", inline=True)
        embed.set_footer(text="Advanced AI detection system")
        await interaction.followup.send(embed=embed)
    except Exception as e:
        print(f"❌ gaydetect failed: {e}")
        try: await interaction.followup.send("🏳️‍🌈 **Gay Detector Error**\n❌ Unable to perform analysis")
        except: pass

@bot.tree.command(name="skiddetect", description="Detect if someone is a skid")
@app_commands.describe(user="The user to check")
async def skiddetect(interaction: discord.Interaction, user: discord.User):
    await interaction.response.defer(ephemeral=False)
    try:
        temp = await interaction.followup.send(f"Analyzing {user.name}...")
        await asyncio.sleep(0.5)
        await temp.delete()
        skid_percentage = random.randint(0, 100)
        if skid_percentage == 0: status, emoji = "Legitimate Developer", "💻"
        elif skid_percentage <= 20: status, emoji = "Probably Legit", "✅"
        elif skid_percentage <= 40: status, emoji = "Questionable Code", "🤔"
        elif skid_percentage <= 60: status, emoji = "Copy-Paste Developer", "📋"
        elif skid_percentage <= 80: status, emoji = "Definite Skid", "🚫"
        elif skid_percentage < 100: status, emoji = "Major Skid", "⛔"
        else: status, emoji = "100% Script Kiddie", "🤡"
        embed = discord.Embed(title="💻 Skid Detector Results", description=f"**Analysis complete for {user.name}**", color=discord.Color.red())
        embed.add_field(name="👤 Target User", value=f"{user.mention}", inline=False)
        embed.add_field(name="📊 Skid Percentage", value=f"**{skid_percentage}%**", inline=True)
        embed.add_field(name="📋 Status", value=f"{emoji} {status}", inline=True)
        embed.add_field(name="🎯 Accuracy", value="100% Accurate", inline=True)
        embed.set_footer(text="Advanced code analysis system")
        await interaction.followup.send(embed=embed)
    except Exception as e:
        print(f"❌ skiddetect failed: {e}")
        try: await interaction.followup.send("💻 **Skid Detector Error**\n❌ Unable to perform analysis")
        except: pass

@bot.tree.command(name="ip", description="Find a user's IP address")
@app_commands.describe(user="The user to IP trace")
async def ip(interaction: discord.Interaction, user: discord.User):
    await interaction.response.defer(ephemeral=False)
    try:
        temp = await interaction.followup.send(f"Tracing IP for {user.name}...")
        await asyncio.sleep(0.5)
        await temp.delete()
        ip = generate_fake_ip()
        location = random.choice([
            "United States (California)", "United Kingdom (London)", "Germany (Frankfurt)",
            "India (Delhi)", "Brazil (São Paulo)", "Australia (Sydney)", "Canada (Toronto)",
            "Japan (Tokyo)", "France (Paris)", "Netherlands (Amsterdam)"
        ])
        provider = random.choice([
            "Discord ISP", "Anonymous VPN", "Residential ISP", "Mobile Carrier",
            "Cloud Provider", "University Network", "Corporate Network"
        ])
        embed = discord.Embed(title="🔍 IP Lookup Results", description=f"**Target acquired: {user.name}**", color=discord.Color.orange())
        embed.add_field(name="👤 Target User", value=f"{user.mention}", inline=False)
        embed.add_field(name="🌐 IP Address", value=f"`{ip}`", inline=True)
        embed.add_field(name="📍 Location", value=location, inline=True)
        embed.add_field(name="📡 Provider", value=provider, inline=True)
        embed.set_footer(text="Advanced network tracking system")
        await interaction.followup.send(embed=embed)
    except Exception as e:
        print(f"❌ ip failed: {e}")
        try: await interaction.followup.send("🔍 **IP Lookup Error**\n❌ Unable to perform lookup")
        except: pass

@bot.tree.command(name="credits", description="Shows who made the bot")
async def credits(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=False)
    try:
        await asyncio.sleep(0.5)
        embed = discord.Embed(title="🤖 Bot Credits", description="💻✨ Made by 𝐉𝐨𝐫𝐝𝐚𝐧 ✨💻", color=discord.Color.purple())
        embed.add_field(name="Features", value="• Anonymous messaging\n• IP lookup\n• User information\n• Message repetition\n• Coin flip games\n• Gay detection\n• Skid detection", inline=False)
        embed.add_field(name="\u200B", value="☁️ Hosted by Beluga", inline=False)
        embed.set_footer(text="Thanks for using this bot!")
        await interaction.followup.send(embed=embed)
    except Exception as e:
        print(f"❌ credits failed: {e}")
        await interaction.followup.send("💻✨ Made by 𝐉𝐨𝐫𝐝𝐚𝐧 ✨💻\n☁️ Hosted by Beluga")

@bot.tree.command(name="info", description="Shows info about a user from their ID")
@app_commands.describe(user_id="The Discord user ID to inspect")
async def info(interaction: discord.Interaction, user_id: str):
    await interaction.response.defer(ephemeral=False)
    try:
        temp = await interaction.followup.send(f"Getting info on user ID: {user_id}")
        await asyncio.sleep(0.5)
        await temp.delete()
        try: user_id_int = int(user_id)
        except ValueError:
            await interaction.followup.send("❌ Invalid user ID format.")
            return
        try:
            user = await bot.fetch_user(user_id_int)
        except discord.NotFound:
            user = None
        except discord.HTTPException as e:
            await interaction.followup.send(f"❌ Error fetching user: {e}")
            return
        embed = discord.Embed(title="👤 User Information", color=discord.Color.blue())
        embed.add_field(name="🆔 User ID", value=f"`{user_id}`", inline=False)
        if user:
            embed.add_field(name="📝 Username", value=f"{user.name}", inline=True)
            embed.add_field(name="🤖 Bot Account", value="✅ Yes" if user.bot else "❌ No", inline=True)
            embed.add_field(name="📅 Account Created", value=f"<t:{int(user.created_at.replace(tzinfo=timezone.utc).timestamp())}:F>", inline=False)
            if user.avatar: embed.set_thumbnail(url=user.avatar.url)
            embed.color = discord.Color.green()
        else:
            embed.add_field(name="❌ Status", value="User not found or not accessible by bot", inline=False)
            embed.color = discord.Color.red()
        await interaction.followup.send(embed=embed)
    except Exception as e:
        print(f"❌ info failed: {e}")
        await interaction.followup.send("❌ An error occurred while fetching user info")

@bot.event
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    print(f"❌ Command error: {error}")
    try:
        if not interaction.response.is_done():
            await interaction.response.send_message(f"❌ Error: {error}", ephemeral=True)
        else:
            await interaction.followup.send(f"❌ Error: {error}", ephemeral=True)
    except:
        pass

# ------------------------
# Simple webserver to keep Replit awake
# ------------------------

async def handle(request):
    return web.Response(text="Bot is running!")

async def start_webserver():
    app = web.Application()
    app.router.add_get("/", handle)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", int(os.environ.get("PORT", 8080)))
    await site.start()

# ------------------------
# Run bot and webserver together
# ------------------------

async def main():
    await start_webserver()
    await bot.start(TOKEN)

if __name__ == "__main__":
    import asyncio
    while True:
        try:
            print("🚀 Starting bot...")
            asyncio.run(main())
        except Exception as e:
            print(f"❌ Bot crashed: {e}")
            print("🔁 Restarting bot in 5 seconds...")
            import time
            time.sleep(5)
