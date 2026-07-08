import discord
from discord.ext import commands
from discord import app_commands
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
            print(f"Keep-alive web server running on port {port}")
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

def parse_text_color_or_gradient(text_val):
    if not text_val or text_val.lower() in ["none", "skip"]:
        return None, None
    for sep in ['-', ',', '_']:
        if sep in text_val:
            parts = text_val.split(sep)
            if len(parts) >= 2:
                c1 = parse_hex_color(parts[0])
                c2 = parse_hex_color(parts[1])
                if c1 and c2:
                    return None, [c1, c2]
    return parse_hex_color(text_val), None

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

# Helper function to check role permissions
def is_user_authorized(member):
    # 1. Allow bot developers/owners if configured, or server owner/administrators
    if member.guild_permissions.administrator or member == member.guild.owner:
        return True
        
    if hasattr(member, "roles"):
        user_role_ids = [r.id for r in member.roles]
        user_role_names = [r.name.lower() for r in member.roles]
        
        # Check by role ID
        if REQUIRED_ROLE_ID in user_role_ids:
            return True
        # Check by role name (case insensitive)
        if "for support" in user_role_names or "support" in user_role_names:
            return True
            
    return False

# Local configurations storage helper
def save_local_cache(data):
    try:
        with open(JSON_FILE_PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
    except Exception:
        pass

# ================= Discord UI Component Interactions =================

# Modal for Border Color
class BorderColorModal(discord.ui.Modal, title="Set Border Color"):
    def __init__(self, username):
        super().__init__()
        self.username = username

    color = discord.ui.TextInput(
        label="Border Hex Color",
        placeholder="e.g. #FF0000 or skip/none to remove border",
        required=True
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()
        success, sha, data = fetch_from_github()
        if not success:
            await interaction.followup.send(f"Failed to fetch tags: `{sha}`", ephemeral=True)
            return

        user_lower = self.username.lower()
        if user_lower in data["players"]:
            c = parse_hex_color(self.color.value.strip())
            if c:
                data["players"][user_lower]["borderColor"] = c
            else:
                data["players"][user_lower].pop("borderColor", None)
            save_local_cache(data)
            
            # Re-send styling dashboard
            view = StylingOptionsView(self.username)
            await interaction.followup.send(
                f"Border Color updated! Configure additional styling options for **{self.username}**:",
                view=view,
                ephemeral=True
            )
        else:
            await interaction.followup.send("Player configuration not found.", ephemeral=True)

# Modal for Background Color
class BgColorModal(discord.ui.Modal, title="Set Background Color"):
    def __init__(self, username):
        super().__init__()
        self.username = username

    color = discord.ui.TextInput(
        label="Primary Background Hex Color",
        placeholder="e.g. #141414 or skip/none for default dark",
        required=True
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()
        success, sha, data = fetch_from_github()
        if not success:
            await interaction.followup.send(f"Failed to fetch tags: `{sha}`", ephemeral=True)
            return

        user_lower = self.username.lower()
        if user_lower in data["players"]:
            c = parse_hex_color(self.color.value.strip()) or [20, 20, 20]
            data["players"][user_lower]["primaryColor"] = c
            save_local_cache(data)
            
            # Re-send styling dashboard
            view = StylingOptionsView(self.username)
            await interaction.followup.send(
                f"Background Color updated! Configure additional styling options for **{self.username}**:",
                view=view,
                ephemeral=True
            )
        else:
            await interaction.followup.send("Player configuration not found.", ephemeral=True)

# Modal for Username (Display Name) Color
class UserColorModal(discord.ui.Modal, title="Set Username Text Color"):
    def __init__(self, username):
        super().__init__()
        self.username = username

    color = discord.ui.TextInput(
        label="Username Text Hex Color",
        placeholder="e.g. #A0A0A0 or skip/none for default gray",
        required=True
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()
        success, sha, data = fetch_from_github()
        if not success:
            await interaction.followup.send(f"Failed to fetch tags: `{sha}`", ephemeral=True)
            return

        user_lower = self.username.lower()
        if user_lower in data["players"]:
            c = parse_hex_color(self.color.value.strip())
            if c:
                data["players"][user_lower]["displayNameColor"] = c
            else:
                data["players"][user_lower].pop("displayNameColor", None)
            save_local_cache(data)
            
            # Re-send styling dashboard
            view = StylingOptionsView(self.username)
            await interaction.followup.send(
                f"Username Color updated! Configure additional styling options for **{self.username}**:",
                view=view,
                ephemeral=True
            )
        else:
            await interaction.followup.send("Player configuration not found.", ephemeral=True)

# Dashboard styling options view
class StylingOptionsView(discord.ui.View):
    def __init__(self, username):
        super().__init__(timeout=180.0)
        self.username = username

    @discord.ui.button(label="Outline/Border Color", style=discord.ButtonStyle.secondary)
    async def set_border(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(BorderColorModal(self.username))

    @discord.ui.button(label="Background Color", style=discord.ButtonStyle.secondary)
    async def set_bg(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(BgColorModal(self.username))

    @discord.ui.button(label="Username Color", style=discord.ButtonStyle.secondary)
    async def set_username_color(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(UserColorModal(self.username))

    @discord.ui.button(label="Save & Sync to GitHub", style=discord.ButtonStyle.success)
    async def finish_sync(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        success, sha, data = fetch_from_github()
        if not success:
            await interaction.followup.send(f"Failed to fetch current database: `{sha}`", ephemeral=True)
            return

        ok, err = update_github(data, self.username, sha)
        if ok:
            await interaction.followup.send(f"Successfully configured and synced nametag for **{self.username}** on GitHub!", ephemeral=True)
        else:
            await interaction.followup.send(f"Failed to sync changes to GitHub: `{err}`", ephemeral=True)

# Main Creation Modal Dialog popup
class CreateNametagModal(discord.ui.Modal, title="Create / Edit Nametag"):
    username = discord.ui.TextInput(
        label="Roblox Username",
        placeholder="e.g. vrchatuser7895",
        required=True
    )
    tag_text = discord.ui.TextInput(
        label="Tag Text",
        placeholder="e.g. OWNER, DEVELOPER, Xnoctis",
        required=True
    )
    pfp_id = discord.ui.TextInput(
        label="PFP Asset ID (Optional)",
        placeholder="e.g. 128634152988614 (or skip)",
        required=False
    )
    banner_id = discord.ui.TextInput(
        label="Banner Asset ID (Optional)",
        placeholder="e.g. 137782422455419 (or skip)",
        required=False
    )
    text_color = discord.ui.TextInput(
        label="Text Color Hex or Gradient (Optional)",
        placeholder="e.g. #FFFFFF or #FF0000-#0000FF (gradient)",
        required=False
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()
        success, sha, data = fetch_from_github()
        if not success:
            await interaction.followup.send(f"Failed to fetch current database: `{sha}`", ephemeral=True)
            return

        user_lower = self.username.value.strip().lower()
        tag = self.tag_text.value.strip()
        pfp = self.pfp_id.value.strip()
        banner = self.banner_id.value.strip()
        text = self.text_color.value.strip()

        # Parse text color or gradient
        tc, tg = parse_text_color_or_gradient(text)

        # Build configurations
        player_config = {
            "tag": tag,
            "bgImage": format_asset_id(banner),
            "image": format_asset_id(pfp),
            "textColor": tc,
            "textGradient": tg,
            "primaryColor": [20, 20, 20] # default background
        }

        # Keep existing custom border/background/username styling if editing an existing user
        if user_lower in data["players"]:
            existing = data["players"][user_lower]
            if "borderColor" in existing:
                player_config["borderColor"] = existing["borderColor"]
            if "primaryColor" in existing:
                player_config["primaryColor"] = existing["primaryColor"]
            if "displayNameColor" in existing:
                player_config["displayNameColor"] = existing["displayNameColor"]

        player_config = {k: v for k, v in player_config.items() if v is not None and v != ""}
        data["players"][user_lower] = player_config
        save_local_cache(data)

        # Offer further custom color settings
        view = StylingOptionsView(self.username.value.strip())
        await interaction.followup.send(
            f"Base nametag config registered for **{self.username.value.strip()}**.\n"
            f"Would you like to customize background, border, or username colors?",
            view=view,
            ephemeral=True
        )

# View holding a single button to trigger the creation modal
class TriggerModalView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=60.0)

    @discord.ui.button(label="Open Editor Modal", style=discord.ButtonStyle.primary)
    async def open_modal(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(CreateNametagModal())

# ================= Discord Bot Commands =================

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name} ({bot.user.id})")
    # Sync Slash Commands
    try:
        synced = await bot.tree.sync()
        print(f"Successfully synced {len(synced)} Slash Commands.")
    except Exception as e:
        print(f"Failed to sync Slash Commands: {e}")

# Command error handling (e.g. missing role restriction)
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.send("You do not have the required role to run this command.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"Missing required arguments. Usage: `{ctx.prefix}{ctx.command.name} <username>`")
    else:
        print(f"Error running command: {error}")

# Slash Command for /addtag to trigger modal immediately
@bot.tree.command(name="addtag", description="Add or edit a player nametag")
async def slash_addtag(interaction: discord.Interaction):
    if not is_user_authorized(interaction.user):
        await interaction.response.send_message("You do not have the required role to run this command.", ephemeral=True)
        return
    # Immediately trigger popup modal window
    await interaction.response.send_modal(CreateNametagModal())

# Prefix Command for !addtag (sends a single button to open modal)
@bot.command()
async def addtag(ctx):
    if not is_user_authorized(ctx.author):
        await ctx.send("You do not have the required role to run this command.")
        return
    
    view = TriggerModalView()
    await ctx.send("Click the button below to open the configuration popup:", view=view)

@bot.command()
async def removetag(ctx, username: str):
    if not is_user_authorized(ctx.author):
        await ctx.send("You do not have the required role to run this command.")
        return

    await ctx.send("Fetching latest database from GitHub...")
    success, sha, data = fetch_from_github()
    if not success:
        await ctx.send(f"Failed to fetch current tags from GitHub: `{sha}`")
        return
        
    if "players" not in data or username.lower() not in data["players"]:
        await ctx.send(f"No nametag config found for **{username}**.")
        return
        
    del data["players"][username.lower()]
    save_local_cache(data)

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
