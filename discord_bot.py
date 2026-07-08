import discord
from discord.ext import commands
import json
import os
import re
import requests
import base64
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPO = os.getenv("GITHUB_REPO")
JSON_FILE_PATH = "Tags.json"
BRANCH = "main"

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

def parse_hex_color(hex_str):
    if not hex_str or hex_str.lower() == "none":
        return None
    hex_str = hex_str.strip().lstrip('#')
    if len(hex_str) == 3:
        hex_str = ''.join([c*2 for c in hex_str])
    if len(hex_str) != 6:
        return None
    try:
        r = int(hex_str[0:2], 16)
        g = int(hex_str[2:4], 16)
        b = int(hex_str[4:6], 16)
        return [r, g, b]
    except ValueError:
        return None

def format_asset_id(asset_id):
    if not asset_id or asset_id.lower() == "none":
        return ""
    asset_id = asset_id.strip()
    if not asset_id.isdigit():
        digits = re.findall(r'\d+', asset_id)
        if digits:
            asset_id = digits[0]
        else:
            return asset_id
    return f"rbxassetid://{asset_id}"

def update_github(data, username):
    if not GITHUB_TOKEN or GITHUB_TOKEN == "your_github_token_here":
        return False, "GitHub Token is not set in the .env file."
    
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{JSON_FILE_PATH}"
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    # Get current file info (especially sha)
    res = requests.get(url, headers=headers)
    sha = None
    if res.status_code == 200:
        sha = res.json().get("sha")
        
    content_str = json.dumps(data, indent=2)
    content_bytes = content_str.encode('utf-8')
    content_b64 = base64.b64encode(content_bytes).decode('utf-8')
    
    payload = {
        "message": f"Update nametag for {username} via Discord Bot",
        "content": content_b64,
        "branch": BRANCH
    }
    if sha:
        payload["sha"] = sha
        
    put_res = requests.put(url, headers=headers, json=payload)
    if put_res.status_code in [200, 201]:
        return True, "Success"
    else:
        try:
            err_msg = put_res.json().get("message", put_res.text)
        except Exception:
            err_msg = put_res.text
        return False, f"GitHub API error: {err_msg}"

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name} ({bot.user.id})")

@bot.command()
async def addtag(ctx, username: str, tag_text: str, banner: str = "none", pfp: str = "none", border: str = "none", text: str = "none", bg: str = "none"):
    """
    Add or update a player's nametag.
    Usage: !addtag <username> <tag_text> [banner_id] [pfp_id] [border_hex] [text_hex] [bg_hex]
    Use 'none' to skip optional parameters.
    """
    # Load current local JSON
    data = {"players": {}}
    if os.path.exists(JSON_FILE_PATH):
        try:
            with open(JSON_FILE_PATH, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if "players" not in data:
                    data["players"] = {}
        except Exception:
            pass

    bg_color = parse_hex_color(bg) or [20, 20, 20]
    
    player_config = {
        "tag": tag_text,
        "bgImage": format_asset_id(banner),
        "image": format_asset_id(pfp),
        "borderColor": parse_hex_color(border),
        "textColor": parse_hex_color(text),
        "primaryColor": bg_color
    }
    
    # Filter out None / empty values
    player_config = {k: v for k, v in player_config.items() if v is not None and v != ""}
    
    data["players"][username.lower()] = player_config
    
    # Save local copy
    try:
        with open(JSON_FILE_PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        await ctx.send(f"⚠️ Failed to save local Tags.json: {e}")
        return

    # Sync to GitHub
    await ctx.send("🔄 Syncing changes to GitHub...")
    success, msg = update_github(data, username)
    if success:
        await ctx.send(f"✅ Successfully updated nametag for **{username}** on GitHub!")
    else:
        await ctx.send(f"⚠️ Local Tags.json updated, but failed to sync to GitHub: `{msg}`")

@bot.command()
async def removetag(ctx, username: str):
    """
    Remove a player's nametag config.
    Usage: !removetag <username>
    """
    if not os.path.exists(JSON_FILE_PATH):
        await ctx.send("⚠️ Tags.json does not exist locally.")
        return
        
    try:
        with open(JSON_FILE_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        await ctx.send(f"⚠️ Failed to read Tags.json: {e}")
        return
        
    if "players" not in data or username.lower() not in data["players"]:
        await ctx.send(f"❓ No nametag config found for **{username}**.")
        return
        
    del data["players"][username.lower()]
    
    try:
        with open(JSON_FILE_PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        await ctx.send(f"⚠️ Failed to save local Tags.json: {e}")
        return

    await ctx.send("🔄 Syncing changes to GitHub...")
    success, msg = update_github(data, username)
    if success:
        await ctx.send(f"✅ Successfully removed nametag for **{username}** on GitHub!")
    else:
        await ctx.send(f"⚠️ Local configuration removed, but failed to sync to GitHub: `{msg}`")

if __name__ == "__main__":
    if not TOKEN:
        print("Error: DISCORD_TOKEN is missing in the .env file.")
    else:
        bot.run(TOKEN)
