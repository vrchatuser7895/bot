import discord
from discord.ext import commands
import json
import os
import re
import requests
import base64
import asyncio
from dotenv import load_dotenv
from http.server import SimpleHTTPRequestHandler
from socketserver import TCPServer
from threading import Thread

# Load environment variables from .env file
load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPO = os.getenv("GITHUB_REPO")
JSON_FILE_PATH = "Tags.json"
BRANCH = "main"
REQUIRED_ROLE_ID = 1524460541475819665

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Keep-alive web server to bypass free hosting limits on Render
class KeepAliveHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"Bot is alive!")

def run_web():
    port = int(os.getenv("PORT", 8080))
    TCPServer.allow_reuse_address = True
    try:
        with TCPServer(("0.0.0.0", port), KeepAliveHandler) as httpd:
            print(f"Web server running on port {port}")
            httpd.serve_forever()
    except Exception as e:
        print(f"Web server failed to start: {e}")

def keep_alive():
    t = Thread(target=run_web)
    t.daemon = True
    t.start()

def parse_hex_color(hex_str):
    if not hex_str or hex_str.lower() in ["none", "skip"]:
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
    if not asset_id or asset_id.lower() in ["none", "skip"]:
        return ""
    asset_id = asset_id.strip()
    if not asset_id.isdigit():
        digits = re.findall(r'\d+', asset_id)
        if digits:
            asset_id = digits[0]
        else:
            return asset_id
    return f"rbxassetid://{asset_id}"

# Fetch latest Tags.json directly from GitHub API to avoid stale local filesystem caches
def fetch_from_github():
    if not GITHUB_TOKEN or GITHUB_TOKEN == "your_github_token_here":
        return False, "GitHub Token is not set.", {"players": {}}
        
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{JSON_FILE_PATH}"
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    res = requests.get(url, headers=headers)
    if res.status_code == 200:
        data_json = res.json()
        sha = data_json.get("sha")
        content_b64 = data_json.get("content")
        try:
            content_str = base64.b64decode(content_b64).decode('utf-8')
            data = json.loads(content_str)
            if "players" not in data:
                data["players"] = {}
            return True, sha, data
        except Exception as e:
            return False, f"Failed to parse Tags.json: {e}", {"players": {}}
    elif res.status_code == 404:
        # File doesn't exist yet, return empty structure
        return True, None, {"players": {}}
    else:
        return False, f"GitHub API error: {res.text}", {"players": {}}

# Commit and upload changes to GitHub repository
def update_github(data, username, sha=None):
    if not GITHUB_TOKEN or GITHUB_TOKEN == "your_github_token_here":
        return False, "GitHub Token is not set."
        
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{JSON_FILE_PATH}"
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    
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

# Command error handling (e.g. missing role restriction)
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingRole):
        await ctx.send("You do not have the required role to run this command.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"Missing required arguments. Usage: `{ctx.prefix}{ctx.command.name} <username>`")
    else:
        print(f"Error running command: {error}")

@bot.command()
@commands.has_role(REQUIRED_ROLE_ID)
async def addtag(ctx):
    """
    Starts an interactive step-by-step setup wizard to create a custom nametag.
    """
    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel

    try:
        await ctx.send("Roblox Nametags Setup Wizard started!\nReply with `cancel` at any point to exit.")
        
        # 1. Target Username
        await ctx.send("Step 1: Enter the target Roblox username:")
        msg = await bot.wait_for('message', timeout=60.0, check=check)
        if msg.content.strip().lower() == 'cancel':
            await ctx.send("Cancelled wizard.")
            return
        username = msg.content.strip()
        if not username:
            await ctx.send("Username cannot be empty. Cancelled.")
            return
            
        # 2. Tag Text
        await ctx.send("Step 2: Enter the tag text (e.g. OWNER, STAFF, Xnoctis):")
        msg = await bot.wait_for('message', timeout=60.0, check=check)
        if msg.content.strip().lower() == 'cancel':
            await ctx.send("Cancelled wizard.")
            return
        tag_text = msg.content.strip()
        if not tag_text:
            await ctx.send("Tag text cannot be empty. Cancelled.")
            return

        # 3. Banner
        await ctx.send("Step 3: Enter the Banner/Background Asset ID (or reply `skip` for none):")
        msg = await bot.wait_for('message', timeout=60.0, check=check)
        if msg.content.strip().lower() == 'cancel':
            await ctx.send("Cancelled wizard.")
            return
        banner = "" if msg.content.strip().lower() == 'skip' else msg.content.strip()

        # 4. PFP
        await ctx.send("Step 4: Enter the PFP/Icon Asset ID (or reply `skip` for none):")
        msg = await bot.wait_for('message', timeout=60.0, check=check)
        if msg.content.strip().lower() == 'cancel':
            await ctx.send("Cancelled wizard.")
            return
        pfp = "" if msg.content.strip().lower() == 'skip' else msg.content.strip()

        # 5. Border Hex
        await ctx.send("Step 5: Enter the Border Color Hex (e.g. `#FF0000` or reply `skip` for none):")
        msg = await bot.wait_for('message', timeout=60.0, check=check)
        if msg.content.strip().lower() == 'cancel':
            await ctx.send("Cancelled wizard.")
            return
        border_hex = "" if msg.content.strip().lower() == 'skip' else msg.content.strip()

        # 6. Text color / gradient choice
        await ctx.send("Step 6: Do you want a text gradient? Reply `yes` or `no`:")
        msg = await bot.wait_for('message', timeout=60.0, check=check)
        if msg.content.strip().lower() == 'cancel':
            await ctx.send("Cancelled wizard.")
            return
        
        text_color = None
        text_gradient = None
        if msg.content.strip().lower() == 'yes':
            # Gradient colors
            await ctx.send("Step 6a: Enter the gradient start color Hex (e.g. `#FF0000`):")
            msg = await bot.wait_for('message', timeout=60.0, check=check)
            if msg.content.strip().lower() == 'cancel':
                await ctx.send("Cancelled wizard.")
                return
            start_hex = msg.content.strip()
            
            await ctx.send("Step 6b: Enter the gradient end color Hex (e.g. `#0000FF`):")
            msg = await bot.wait_for('message', timeout=60.0, check=check)
            if msg.content.strip().lower() == 'cancel':
                await ctx.send("Cancelled wizard.")
                return
            end_hex = msg.content.strip()
            
            c1 = parse_hex_color(start_hex)
            c2 = parse_hex_color(end_hex)
            if c1 and c2:
                text_gradient = [c1, c2]
            else:
                await ctx.send("Invalid colors entered for gradient. Skipping text gradient.")
        else:
            await ctx.send("Step 6a: Enter a single solid Text Color Hex (or reply `skip` for none):")
            msg = await bot.wait_for('message', timeout=60.0, check=check)
            if msg.content.strip().lower() == 'cancel':
                await ctx.send("Cancelled wizard.")
                return
            if msg.content.strip().lower() != 'skip':
                text_color = parse_hex_color(msg.content.strip())

        # 7. Tag Background Color
        await ctx.send("Step 7: Enter the Primary Background Color Hex (e.g. `#141414` or reply `skip` for default dark):")
        msg = await bot.wait_for('message', timeout=60.0, check=check)
        if msg.content.strip().lower() == 'cancel':
            await ctx.send("Cancelled wizard.")
            return
        bg_hex = msg.content.strip()
        bg_color = parse_hex_color(bg_hex) or [20, 20, 20]

        # Syncing...
        await ctx.send("Setup complete! Syncing tag to GitHub...")
        success, sha, data = fetch_from_github()
        if not success:
            await ctx.send(f"Failed to fetch current database: `{sha}`")
            return

        player_config = {
            "tag": tag_text,
            "bgImage": format_asset_id(banner),
            "image": format_asset_id(pfp),
            "borderColor": parse_hex_color(border_hex),
            "textColor": text_color,
            "textGradient": text_gradient,
            "primaryColor": bg_color
        }
        
        player_config = {k: v for k, v in player_config.items() if v is not None and v != ""}
        data["players"][username.lower()] = player_config
        
        # Save a local cache copy
        try:
            with open(JSON_FILE_PATH, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        except Exception:
            pass

        success, msg = update_github(data, username, sha)
        if success:
            await ctx.send(f"Successfully created/updated nametag for **{username}** on GitHub!")
        else:
            await ctx.send(f"Failed to sync changes to GitHub: `{msg}`")

    except asyncio.TimeoutError:
        await ctx.send("Setup wizard timed out due to inactivity (no reply for 60 seconds). Please try again.")
    except Exception as e:
        await ctx.send(f"An error occurred in the setup wizard: {e}")

@bot.command()
@commands.has_role(REQUIRED_ROLE_ID)
async def removetag(ctx, username: str):
    """
    Remove a player's nametag config.
    Usage: !removetag <username>
    """
    await ctx.send("Fetching latest database from GitHub...")
    success, sha, data = fetch_from_github()
    if not success:
        await ctx.send(f"Failed to fetch current tags from GitHub: `{sha}`")
        return
        
    if "players" not in data or username.lower() not in data["players"]:
        await ctx.send(f"No nametag config found for **{username}**.")
        return
        
    del data["players"][username.lower()]
    
    # Save a local cache copy
    try:
        with open(JSON_FILE_PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
    except Exception:
        pass

    await ctx.send("Syncing removal to GitHub...")
    success, msg = update_github(data, username, sha)
    if success:
        await ctx.send(f"Successfully removed nametag for **{username}** on GitHub!")
    else:
        await ctx.send(f"Failed to sync removal to GitHub: `{msg}`")

if __name__ == "__main__":
    if not TOKEN:
        print("Error: DISCORD_TOKEN is missing in the .env file.")
    else:
        keep_alive()
        bot.run(TOKEN)
