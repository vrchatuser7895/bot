import discord
from discord.ext import commands
import json
import os
import re
import requests
import base64
from dotenv import load_dotenv
from http.server import BaseHTTPRequestHandler
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

# Pure Black and White Premium Responsive Control Panel
HTML_PANEL_CONTENT = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Xnoctis Overhead Control Panel</title>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&family=Fredoka:wght@600;700&family=Press+Start+2P&family=Orbitron:wght@700&family=Patrick+Hand&family=Special+Elite&family=Creepster&family=Luckiest+Guy&family=Roboto:wght@500;700&family=Source+Sans+3:wght@300;400&family=EB+Garamond&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-black: #000000;
            --card-black: #0c0c0c;
            --input-black: #121212;
            --border-gray: #1f1f1f;
            --border-focus: #444444;
            --text-white: #ffffff;
            --text-muted: #888888;
            --error-red: #ff3b30;
        }

        * {
            box-sizing: border-box;
            font-family: 'Outfit', sans-serif;
            margin: 0;
            padding: 0;
        }

        body {
            background-color: var(--bg-black);
            color: var(--text-white);
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            align-items: center;
            padding: 40px 20px;
        }

        header {
            margin-bottom: 40px;
            text-align: center;
        }

        header h1 {
            font-size: 2.2rem;
            font-weight: 700;
            letter-spacing: 2px;
            text-transform: uppercase;
            margin-bottom: 8px;
        }

        header p {
            color: var(--text-muted);
            font-size: 1rem;
        }

        .container {
            display: grid;
            grid-template-columns: 1.2fr 1fr;
            gap: 30px;
            width: 100%;
            max-width: 1200px;
        }

        @media (max-width: 900px) {
            .container {
                grid-template-columns: 1fr;
            }
        }

        .card {
            background: var(--card-black);
            border: 1px solid var(--border-gray);
            border-radius: 12px;
            padding: 30px;
            display: flex;
            flex-direction: column;
            gap: 20px;
        }

        .card h2 {
            font-size: 1.3rem;
            font-weight: 600;
            letter-spacing: 1px;
            text-transform: uppercase;
            border-bottom: 1px solid var(--border-gray);
            padding-bottom: 15px;
            margin-bottom: 10px;
        }

        .form-group {
            display: flex;
            flex-direction: column;
            gap: 8px;
        }

        .form-group label {
            font-size: 0.8rem;
            font-weight: 600;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .form-control {
            background: var(--input-black);
            border: 1px solid var(--border-gray);
            border-radius: 8px;
            color: var(--text-white);
            padding: 12px 16px;
            font-size: 0.95rem;
            transition: all 0.2s ease;
        }

        .form-control:focus {
            outline: none;
            border-color: var(--border-focus);
        }

        select.form-control {
            appearance: none;
            -webkit-appearance: none;
            -moz-appearance: none;
            background-image: url("data:image/svg+xml;utf8,<svg fill='white' height='24' viewBox='0 0 24 24' width='24' xmlns='http://www.w3.org/2000/svg'><path d='M7 10l5 5 5-5z'/><path d='M0 0h24v24H0z' fill='none'/></svg>");
            background-repeat: no-repeat;
            background-position: right 12px center;
            padding-right: 40px;
            cursor: pointer;
        }
        
        select.form-control option {
            background: var(--card-black);
            color: var(--text-white);
        }

        .color-picker-row {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
        }

        .color-picker-wrapper {
            display: flex;
            align-items: center;
            gap: 12px;
            background: var(--input-black);
            border: 1px solid var(--border-gray);
            border-radius: 8px;
            padding: 8px 12px;
        }

        .color-picker-wrapper input[type="color"] {
            border: none;
            background: none;
            width: 32px;
            height: 32px;
            cursor: pointer;
            border-radius: 50%;
            overflow: hidden;
        }

        .color-picker-wrapper input[type="color"]::-webkit-color-swatch-wrapper {
            padding: 0;
        }

        .color-picker-wrapper input[type="color"]::-webkit-color-swatch {
            border: none;
            border-radius: 50%;
        }

        .color-picker-wrapper span {
            font-size: 0.85rem;
            font-weight: 600;
            color: var(--text-white);
        }

        .checkbox-group {
            display: flex;
            align-items: center;
            gap: 10px;
            cursor: pointer;
            font-size: 0.85rem;
            font-weight: 600;
            color: var(--text-muted);
            text-transform: uppercase;
        }

        .checkbox-group input {
            cursor: pointer;
            width: 16px;
            height: 16px;
            accent-color: var(--text-white);
        }

        .btn {
            background: var(--text-white);
            color: var(--bg-black);
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-size: 0.9rem;
            font-weight: 700;
            padding: 14px 20px;
            text-align: center;
            text-transform: uppercase;
            letter-spacing: 1px;
            transition: all 0.2s ease;
        }

        .btn:hover {
            opacity: 0.9;
        }

        .btn-delete {
            background: var(--error-red);
            color: var(--text-white);
        }

        /* Preview Box */
        .preview-container {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            border: 1px dashed var(--border-gray);
            border-radius: 8px;
            padding: 40px 20px;
            background: rgba(255, 255, 255, 0.02);
            min-height: 180px;
            position: relative;
        }

        .preview-label {
            position: absolute;
            top: 10px;
            left: 15px;
            font-size: 0.7rem;
            color: var(--text-muted);
            text-transform: uppercase;
            font-weight: bold;
        }

        /* Roblox nametag emulator */
        .nametag-emulator {
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 10px 24px;
            border-radius: 12px;
            background-color: #141414;
            min-width: 250px;
            max-width: 380px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.8);
            border: 2px solid transparent;
            transition: all 0.2s ease;
            position: relative;
        }

        .nametag-pfp {
            width: 30px;
            height: 30px;
            border-radius: 6px;
            background-color: #3a3a3a;
            background-size: cover;
            background-position: center;
        }

        .nametag-text-block {
            display: flex;
            flex-direction: column;
            gap: 2px;
        }

        .nametag-rank {
            font-size: 0.88rem;
            font-weight: 700;
            color: #ffffff;
            letter-spacing: 0.2px;
        }

        .nametag-username {
            font-size: 0.65rem;
            font-weight: 700;
            color: #a0a0a0;
        }

        /* Players List */
        .players-list {
            display: flex;
            flex-direction: column;
            gap: 10px;
            max-height: 400px;
            overflow-y: auto;
            padding-right: 5px;
        }

        .player-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            background: var(--input-black);
            border: 1px solid var(--border-gray);
            border-radius: 8px;
            padding: 12px 18px;
            cursor: pointer;
            transition: all 0.2s ease;
        }

        .player-item:hover {
            border-color: var(--border-focus);
        }

        .player-item-info {
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .player-item-name {
            font-weight: 600;
            font-size: 0.95rem;
        }

        .player-item-tag {
            font-size: 0.7rem;
            background: #ffffff;
            color: #000000;
            padding: 3px 8px;
            border-radius: 4px;
            font-weight: bold;
            text-transform: uppercase;
        }

        .hidden {
            display: none !important;
        }

        /* Overlay and Dialog styling */
        .auth-overlay {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.85);
            backdrop-filter: blur(8px);
            z-index: 9999;
            display: flex;
            justify-content: center;
            align-items: center;
        }

        .auth-card {
            background: var(--card-black);
            border: 1px solid var(--border-gray);
            border-radius: 12px;
            padding: 30px;
            width: 90%;
            max-width: 400px;
            display: flex;
            flex-direction: column;
            gap: 20px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.8);
        }

        /* Smooth and Clean Modal Buttons */
        .modal-btn {
            background: transparent;
            border: 1px solid var(--border-gray);
            color: var(--text-white);
            border-radius: 8px;
            padding: 12px 20px;
            font-size: 0.88rem;
            font-weight: 600;
            cursor: pointer;
            text-align: center;
            transition: all 0.2s ease;
            letter-spacing: 0.5px;
            width: 100%;
        }
        
        .modal-btn-edit {
            background: rgba(255, 255, 255, 0.03);
            border-color: rgba(255, 255, 255, 0.15);
        }
        
        .modal-btn-edit:hover {
            background: var(--text-white);
            color: var(--bg-black);
            border-color: var(--text-white);
        }
        
        .modal-btn-delete {
            background: rgba(255, 59, 48, 0.05);
            border-color: rgba(255, 59, 48, 0.3);
            color: #ff453a;
        }
        
        .modal-btn-delete:hover {
            background: var(--error-red);
            color: var(--text-white);
            border-color: var(--error-red);
        }
        
        .modal-btn-cancel {
            background: transparent;
            border-color: rgba(255, 255, 255, 0.05);
            color: var(--text-muted);
        }
        
        .modal-btn-cancel:hover {
            background: rgba(255, 255, 255, 0.05);
            color: var(--text-white);
        }
    </style>
</head>
<body>
    <!-- Action Option Modal -->
    <div id="action-modal" class="auth-overlay hidden">
        <div class="auth-card" style="max-width: 320px; text-align: center;">
            <h2 id="action-title" style="font-size: 1.15rem; border-bottom: none; padding-bottom: 0; margin-bottom: 8px;">Manage Tag</h2>
            <p id="action-subtitle" style="color: var(--text-white); font-size: 0.95rem; margin-bottom: 4px; font-weight: 600;">For player</p>
            <p id="action-created-by" style="color: var(--text-muted); font-size: 0.78rem; margin-bottom: 22px;">Created by: Unknown</p>
            <div style="display: flex; flex-direction: column; gap: 10px; width: 100%;">
                <button class="modal-btn modal-btn-edit" onclick="executeEditFromModal()">Edit Tag</button>
                <button class="modal-btn modal-btn-delete" onclick="executeDeleteFromModal()">Delete Tag</button>
                <button class="modal-btn modal-btn-cancel" onclick="closeActionModal()">Cancel</button>
            </div>
        </div>
    </div>

    <div class="container" style="margin-top: 40px;">
        <!-- Editor Card -->
        <div class="card">
            <h2>Nametag Editor</h2>
            
            <div class="form-group">
                <label for="username">Target Roblox Username</label>
                <input type="text" id="username" class="form-control" placeholder="e.g. edancer67" oninput="updatePreview()">
            </div>

            <div class="form-group">
                <label for="tagText">Tag Text</label>
                <input type="text" id="tagText" class="form-control" placeholder="e.g. OWNER, DEVELOPER" oninput="updatePreview()">
            </div>

            <div class="color-picker-row">
                <div class="form-group">
                    <label>Tag Background</label>
                    <div class="color-picker-wrapper">
                        <input type="color" id="bgColorPicker" value="#141414" oninput="updatePreview()">
                        <span id="bgColorHex">#141414</span>
                    </div>
                </div>
                <div class="form-group">
                    <label>Username Color</label>
                    <div class="color-picker-wrapper">
                        <input type="color" id="userColorPicker" value="#a0a0a0" oninput="updatePreview()">
                        <span id="userColorHex">#A0A0A0</span>
                    </div>
                </div>
            </div>

            <!-- Border Configuration -->
            <div class="form-group" style="gap: 12px;">
                <label class="checkbox-group">
                    <input type="checkbox" id="useBorder" onchange="toggleBorderOption()">
                    Use Outline Border?
                </label>
                <div id="border-picker-wrapper" class="color-picker-wrapper hidden">
                    <input type="color" id="borderColorPicker" value="#ffffff" oninput="updatePreview()">
                    <span id="borderColorHex">#FFFFFF</span>
                </div>
            </div>

            <!-- Text Color configuration (Solid vs Gradient) -->
            <div class="form-group" style="gap: 12px;">
                <label class="checkbox-group">
                    <input type="checkbox" id="useGradient" onchange="toggleGradientOption()">
                    Use Text Color Gradient?
                </label>
                
                <div id="solid-text-picker" class="color-picker-wrapper">
                    <input type="color" id="textColorPicker" value="#ffffff" oninput="updatePreview()">
                    <span id="textColorHex">#FFFFFF</span>
                </div>

                <div id="gradient-pickers" class="color-picker-row hidden">
                    <div class="form-group">
                        <label>Gradient Start</label>
                        <div class="color-picker-wrapper">
                            <input type="color" id="gradStartPicker" value="#8e2de2" oninput="updatePreview()">
                            <span id="gradStartHex">#8E2DE2</span>
                        </div>
                    </div>
                    <div class="form-group">
                        <label>Gradient End</label>
                        <div class="color-picker-wrapper">
                            <input type="color" id="gradEndPicker" value="#4a00e0" oninput="updatePreview()">
                            <span id="gradEndHex">#4A00E0</span>
                        </div>
                    </div>
                </div>
            </div>

            <div class="color-picker-row">
                <div class="form-group">
                    <label for="pfpId">PFP Asset ID (Optional)</label>
                    <input type="text" id="pfpId" class="form-control" placeholder="e.g. 128634152988614" oninput="updatePreview()">
                </div>
                <div class="form-group">
                    <label for="bannerId">Banner Asset ID (Optional)</label>
                    <input type="text" id="bannerId" class="form-control" placeholder="e.g. 137782422455419" oninput="updatePreview()">
                </div>
            </div>

            <!-- Size and Font Dropdowns -->
            <div class="form-group">
                <label for="sizeSelect">Nametag Width Sizing</label>
                <select id="sizeSelect" class="form-control" onchange="updatePreview()">
                    <option value="small">Small (Compact Width)</option>
                    <option value="normal" selected>Normal (Standard Width)</option>
                    <option value="large">Large (Extra Wide)</option>
                </select>
            </div>
            
            <div class="color-picker-row">
                <div class="form-group">
                    <label for="tagFontSelect">Tag Font</label>
                    <select id="tagFontSelect" class="form-control" onchange="updatePreview()">
                        <option value="GothamBold" selected>Default (Gotham Bold)</option>
                        <option value="FredokaOne">Fredoka (Bubbly)</option>
                        <option value="Arcade">Arcade (Pixel)</option>
                        <option value="SciFi">SciFi (Futuristic)</option>
                        <option value="PatrickHand">Patrick Hand (Handwritten)</option>
                        <option value="SpecialElite">Special Elite (Typewriter)</option>
                        <option value="Creepster">Creepster (Spooky)</option>
                        <option value="LuckiestGuy">Luckiest Guy (Cartoon)</option>
                        <option value="Highway">Highway (Clean Sans)</option>
                        <option value="SourceSansLight">Source Sans Light (Sleek)</option>
                        <option value="Garamond">Garamond (Classic Serif)</option>
                    </select>
                </div>
                <div class="form-group">
                    <label for="displayFontSelect">Display Name Font</label>
                    <select id="displayFontSelect" class="form-control" onchange="updatePreview()">
                        <option value="GothamBold" selected>Default (Gotham Bold)</option>
                        <option value="FredokaOne">Fredoka (Bubbly)</option>
                        <option value="Arcade">Arcade (Pixel)</option>
                        <option value="SciFi">SciFi (Futuristic)</option>
                        <option value="PatrickHand">Patrick Hand (Handwritten)</option>
                        <option value="SpecialElite">Special Elite (Typewriter)</option>
                        <option value="Creepster">Creepster (Spooky)</option>
                        <option value="LuckiestGuy">Luckiest Guy (Cartoon)</option>
                        <option value="Highway">Highway (Clean Sans)</option>
                        <option value="SourceSansLight">Source Sans Light (Sleek)</option>
                        <option value="Garamond">Garamond (Classic Serif)</option>
                    </select>
                </div>
            </div>

            <div class="preview-container">
                <div class="preview-label">Live Tag Emulator</div>
                
                <div class="nametag-emulator" id="emulator">
                    <div class="nametag-pfp" id="emulator-pfp"></div>
                    <div class="nametag-text-block">
                        <div class="nametag-rank" id="emulator-rank">TAG TEXT</div>
                        <div class="nametag-username" id="emulator-user">@Username</div>
                    </div>
                </div>
            </div>

            <!-- Password field placed directly in the form -->
            <div class="form-group" style="margin-top: 10px; border-top: 1px solid var(--border-gray); padding-top: 20px;">
                <label for="accessPassword">Security Access Password</label>
                <input type="password" id="accessPassword" class="form-control" placeholder="Enter Access Password to Sync...">
            </div>

            <div style="display: flex; gap: 15px; width: 100%;">
                <button class="btn" style="flex: 2;" onclick="saveTag()">Save / Sync Tag</button>
                <button id="delete-btn" class="btn btn-delete hidden" style="flex: 1;" onclick="deleteTag()">Delete</button>
            </div>
        </div>

        <!-- Database List Card -->
        <div class="card">
            <h2>Current Configurations</h2>
            <div class="form-group" style="margin-bottom: 10px;">
                <input type="text" id="searchBar" class="form-control" placeholder="Search usernames or tags..." oninput="filterPlayersList()">
            </div>
            <div class="players-list" id="players-list">
                <div style="color: var(--text-muted); text-align: center; padding-top: 50px;">Loading database...</div>
            </div>
        </div>
    </div>

    <script>
        let currentDatabase = { players: {} };
        let activeEditUser = null;

        document.addEventListener("DOMContentLoaded", () => {
            // Load saved password from local storage if they entered it before
            const cachedPw = localStorage.getItem("panel_pw");
            if (cachedPw) {
                document.getElementById("accessPassword").value = cachedPw;
            }
            fetchTags();
        });

        function toggleBorderOption() {
            const useBorder = document.getElementById("useBorder").checked;
            const borderWrapper = document.getElementById("border-picker-wrapper");
            if (useBorder) {
                borderWrapper.classList.remove("hidden");
            } else {
                borderWrapper.classList.add("hidden");
            }
            updatePreview();
        }

        function toggleGradientOption() {
            const useGrad = document.getElementById("useGradient").checked;
            const solidPicker = document.getElementById("solid-text-picker");
            const gradPickers = document.getElementById("gradient-pickers");
            if (useGrad) {
                solidPicker.classList.add("hidden");
                gradPickers.classList.remove("hidden");
            } else {
                solidPicker.classList.remove("hidden");
                gradPickers.classList.add("hidden");
            }
            updatePreview();
        }

        function hexToRgb(hex) {
            const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
            return result ? [
                parseInt(result[1], 16),
                parseInt(result[2], 16),
                parseInt(result[3], 16)
            ] : [255, 255, 255];
        }

        function rgbToHex(rgb) {
            if (!rgb || rgb.length < 3) return "#ffffff";
            return "#" + ((1 << 24) + (rgb[0] << 16) + (rgb[1] << 8) + rgb[2]).toString(16).slice(1);
        }

        function extractAssetDigits(assetId) {
            if (!assetId) return "";
            if (assetId.startsWith("http://") || assetId.startsWith("https://")) {
                if (assetId.includes("id=")) {
                    const match = assetId.match(/id=(\d+)/);
                    if (match) return match[1];
                }
                return assetId;
            }
            const digits = assetId.match(/\d+/);
            return digits ? digits[0] : assetId;
        }

        // Live preview synchronization
        function updatePreview() {
            const emulator = document.getElementById("emulator");
            const emRank = document.getElementById("emulator-rank");
            const emUser = document.getElementById("emulator-user");
            const emPfp = document.getElementById("emulator-pfp");

            // Text content
            const username = document.getElementById("username").value.trim() || "Username";
            const tagText = document.getElementById("tagText").value.trim() || "TAG TEXT";
            emRank.innerText = (tagText.toLowerCase() === "xnoctis") ? "XNOCTIS" : tagText;
            emUser.innerText = "@" + username;

            // Hex updates
            document.getElementById("bgColorHex").innerText = document.getElementById("bgColorPicker").value.toUpperCase();
            document.getElementById("userColorHex").innerText = document.getElementById("userColorPicker").value.toUpperCase();
            document.getElementById("borderColorHex").innerText = document.getElementById("borderColorPicker").value.toUpperCase();
            document.getElementById("textColorHex").innerText = document.getElementById("textColorPicker").value.toUpperCase();
            document.getElementById("gradStartHex").innerText = document.getElementById("gradStartPicker").value.toUpperCase();
            document.getElementById("gradEndHex").innerText = document.getElementById("gradEndPicker").value.toUpperCase();

            // Font Preset
            const fontMap = {
                "GothamBold": "'Outfit', sans-serif",
                "FredokaOne": "'Fredoka', sans-serif",
                "Arcade": "'Press Start 2P', monospace",
                "SciFi": "'Orbitron', sans-serif",
                "PatrickHand": "'Patrick Hand', cursive",
                "SpecialElite": "'Special Elite', serif",
                "Creepster": "'Creepster', cursive",
                "LuckiestGuy": "'Luckiest Guy', cursive",
                "Highway": "'Roboto', sans-serif",
                "SourceSansLight": "'Source Sans 3', sans-serif",
                "Garamond": "'EB Garamond', serif"
            };
            const tagFont = document.getElementById("tagFontSelect").value;
            const displayFont = document.getElementById("displayFontSelect").value;
            
            emRank.style.fontFamily = fontMap[tagFont] || fontMap["GothamBold"];
            emUser.style.fontFamily = fontMap[displayFont] || fontMap["GothamBold"];

            // Apply light font weight for SourceSansLight
            if (tagFont === "SourceSansLight") {
                emRank.style.fontWeight = "300";
            } else {
                emRank.style.fontWeight = "600";
            }
            if (displayFont === "SourceSansLight") {
                emUser.style.fontWeight = "300";
            } else {
                emUser.style.fontWeight = "600";
            }

            // Size Preset (Only gets wider, does not get taller or bigger!)
            const size = document.getElementById("sizeSelect").value;
            emulator.style.padding = "10px 24px";
            emulator.style.borderRadius = "12px";
            emPfp.style.width = "30px";
            emPfp.style.height = "30px";
            emRank.style.fontSize = (tagFont === "Arcade") ? "0.65rem" : "0.88rem";
            emUser.style.fontSize = "0.65rem";

            if (size === "small") {
                emulator.style.minWidth = "140px";
            } else if (size === "large") {
                emulator.style.minWidth = "240px";
            } else { // normal
                emulator.style.minWidth = "180px";
            }

            // Adjust custom font size if needed
            if (tagFont === "LuckiestGuy" || tagFont === "Creepster") {
                emRank.style.fontSize = "1.05rem";
            }

            // Background & Banner
            const bannerId = extractAssetDigits(document.getElementById("bannerId").value.trim());
            const bgColor = document.getElementById("bgColorPicker").value;
            if (bannerId) {
                if (bannerId.startsWith("http")) {
                    emulator.style.backgroundImage = `url('${bannerId}')`;
                } else {
                    emulator.style.backgroundImage = `url('/api/thumbnail?id=${bannerId}&size=420x420')`;
                }
                emulator.style.backgroundSize = "cover";
                emulator.style.backgroundPosition = "center";
            } else {
                emulator.style.backgroundImage = "none";
                emulator.style.backgroundColor = bgColor;
            }

            // PFP
            const pfpId = extractAssetDigits(document.getElementById("pfpId").value.trim());
            if (pfpId) {
                emPfp.classList.remove("hidden");
                if (pfpId.startsWith("http")) {
                    emPfp.style.backgroundImage = `url('${pfpId}')`;
                } else {
                    emPfp.style.backgroundImage = `url('/api/thumbnail?id=${pfpId}&size=150x150')`;
                }
            } else if (tagText.toLowerCase() === "xnoctis") {
                emPfp.classList.remove("hidden");
                emPfp.style.backgroundImage = "url('https://tr.rbxcdn.com/128634152988614/150/150/Image/Png')";
            } else {
                emPfp.classList.add("hidden");
            }

            // Border
            const useBorder = document.getElementById("useBorder").checked;
            const borderColor = document.getElementById("borderColorPicker").value;
            if (useBorder && tagText.toLowerCase() !== "xnoctis") {
                emulator.style.borderColor = borderColor;
            } else {
                emulator.style.borderColor = "transparent";
            }

            // Text Colors & Gradients
            const usernameColor = document.getElementById("userColorPicker").value;
            emUser.style.color = (tagText.toLowerCase() === "xnoctis") ? "#a0a0a0" : usernameColor;

            const useGrad = document.getElementById("useGradient").checked;
            if (useGrad) {
                const start = document.getElementById("gradStartPicker").value;
                const end = document.getElementById("gradEndPicker").value;
                emRank.style.background = `linear-gradient(90deg, ${start} 0%, ${end} 100%)`;
                emRank.style.webkitBackgroundClip = "text";
                emRank.style.webkitTextFillColor = "transparent";
            } else {
                emRank.style.background = "none";
                if (tagText.toLowerCase() === "xnoctis") {
                    emRank.style.webkitTextFillColor = "#a0a0a0";
                } else {
                    emRank.style.webkitTextFillColor = document.getElementById("textColorPicker").value;
                }
            }
        }

        // Fetch all configurations from database (No initial block)
        function fetchTags() {
            fetch("/api/tags")
            .then(res => res.json())
            .then(payload => {
                if (!payload || !payload.success) return;
                currentDatabase = payload.data || { players: {} };
                renderPlayersList();
            })
            .catch(err => console.error("Fetch failed", err));
        }

        // Render current player list cards
        function renderPlayersList() {
            const listEl = document.getElementById("players-list");
            listEl.innerHTML = "";
            const players = currentDatabase.players || {};
            const keys = Object.keys(players);
            
            if (keys.length === 0) {
                listEl.innerHTML = `<div style="color: var(--text-muted); text-align: center; padding-top: 50px;">No configurations found in database.</div>`;
                return;
            }

            keys.forEach(username => {
                const config = players[username];
                const item = document.createElement("div");
                item.className = "player-item";
                item.onclick = () => selectUserToEdit(username, config);

                item.innerHTML = `
                    <div class="player-item-info">
                        <div class="player-item-name">${username}</div>
                    </div>
                    <div class="player-item-tag">${config.tag || "XNOCTIS"}</div>
                `;
                listEl.appendChild(item);
            });

            // Re-apply search filter
            filterPlayersList();
        }

        function filterPlayersList() {
            const query = document.getElementById("searchBar").value.toLowerCase().trim();
            const items = document.querySelectorAll(".player-item");
            items.forEach(item => {
                const name = item.querySelector(".player-item-name").innerText.toLowerCase();
                const tag = item.querySelector(".player-item-tag").innerText.toLowerCase();
                if (name.includes(query) || tag.includes(query)) {
                    item.classList.remove("hidden");
                } else {
                    item.classList.add("hidden");
                }
            });
        }

        let modalActiveUser = null;
        let modalActiveConfig = null;

        // Selected user card click -> Show action modal options
        function selectUserToEdit(username, config) {
            modalActiveUser = username;
            modalActiveConfig = config;
            document.getElementById("action-subtitle").innerText = "For player @" + username;
            const creator = config.createdBy || "Unknown";
            document.getElementById("action-created-by").innerText = "Created by: " + creator;
            document.getElementById("action-modal").classList.remove("hidden");
        }

        function closeActionModal() {
            document.getElementById("action-modal").classList.add("hidden");
            modalActiveUser = null;
            modalActiveConfig = null;
        }

        function executeEditFromModal() {
            if (!modalActiveUser || !modalActiveConfig) return;
            const username = modalActiveUser;
            const config = modalActiveConfig;
            closeActionModal();

            loadUserToEdit(username, config);
        }

        function executeDeleteFromModal() {
            if (!modalActiveUser) return;
            const username = modalActiveUser;
            closeActionModal();

            activeEditUser = username;
            deleteTag();
        }

        // Load credentials to the Editor Form
        function loadUserToEdit(username, config) {
            activeEditUser = username;
            document.getElementById("username").value = username;
            document.getElementById("tagText").value = config.tag || "";
            document.getElementById("pfpId").value = extractAssetDigits(config.image || "");
            document.getElementById("bannerId").value = extractAssetDigits(config.bgImage || "");

            // Preset selectors
            document.getElementById("sizeSelect").value = config.size || "normal";
            document.getElementById("tagFontSelect").value = config.font || "GothamBold";
            document.getElementById("displayFontSelect").value = config.displayFont || "GothamBold";

            // Colors setup
            document.getElementById("bgColorPicker").value = rgbToHex(config.primaryColor || [20, 20, 20]);
            document.getElementById("userColorPicker").value = rgbToHex(config.displayNameColor || [160, 160, 160]);

            // Border setup
            if (config.borderColor && config.borderColor !== "none") {
                document.getElementById("useBorder").checked = true;
                document.getElementById("borderColorPicker").value = rgbToHex(config.borderColor);
                document.getElementById("border-picker-wrapper").classList.remove("hidden");
            } else {
                document.getElementById("useBorder").checked = false;
                document.getElementById("border-picker-wrapper").classList.add("hidden");
            }

            // Text styling setup
            if (config.textGradient && config.textGradient.length >= 2) {
                document.getElementById("useGradient").checked = true;
                document.getElementById("gradStartPicker").value = rgbToHex(config.textGradient[0]);
                document.getElementById("gradEndPicker").value = rgbToHex(config.textGradient[1]);
                document.getElementById("solid-text-picker").classList.add("hidden");
                document.getElementById("gradient-pickers").classList.remove("hidden");
            } else {
                document.getElementById("useGradient").checked = false;
                document.getElementById("textColorPicker").value = rgbToHex(config.textColor || [255, 255, 255]);
                document.getElementById("solid-text-picker").classList.remove("hidden");
                document.getElementById("gradient-pickers").classList.add("hidden");
            }

            // Enable delete button
            document.getElementById("delete-btn").classList.remove("hidden");
            updatePreview();
        }

        // Save nametag configurations to DB
        function saveTag() {
            const username = document.getElementById("username").value.trim().toLowerCase();
            const tagText = document.getElementById("tagText").value.trim();
            const pw = document.getElementById("accessPassword").value.trim();

            if (!username || !tagText) {
                alert("Roblox Username and Tag Text are required.");
                return;
            }

            if (!pw) {
                alert("Security Access Password is required to sync changes.");
                return;
            }

            // Save password to local storage so they don't have to retype it in this browser
            localStorage.setItem("panel_pw", pw);

            const payload = {
                username: username,
                config: {
                    tag: tagText,
                    primaryColor: hexToRgb(document.getElementById("bgColorPicker").value),
                    displayNameColor: hexToRgb(document.getElementById("userColorPicker").value),
                    size: document.getElementById("sizeSelect").value,
                    font: document.getElementById("tagFontSelect").value,
                    displayFont: document.getElementById("displayFontSelect").value
                }
            };

            // Banner image
            const bannerId = extractAssetDigits(document.getElementById("bannerId").value.trim());
            if (bannerId) payload.config.bgImage = `rbxassetid://${bannerId}`;

            // PFP image
            const pfpId = extractAssetDigits(document.getElementById("pfpId").value.trim());
            if (pfpId) payload.config.image = `rbxassetid://${pfpId}`;

            // Border
            if (document.getElementById("useBorder").checked) {
                payload.config.borderColor = hexToRgb(document.getElementById("borderColorPicker").value);
            }

            // Text colors
            if (document.getElementById("useGradient").checked) {
                payload.config.textGradient = [
                    hexToRgb(document.getElementById("gradStartPicker").value),
                    hexToRgb(document.getElementById("gradEndPicker").value)
                ];
            } else {
                payload.config.textColor = hexToRgb(document.getElementById("textColorPicker").value);
            }

            fetch("/api/save", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-Password": pw
                },
                body: JSON.stringify(payload)
            })
            .then(res => {
                if (res.status === 401) {
                    alert("Access Denied: Incorrect Security Password.");
                    return null;
                }
                return res.json();
            })
            .then(data => {
                if (data === null) return;
                if (data && data.success) {
                    alert("Configuration saved and synced successfully!");
                    fetchTags();
                    resetForm();
                } else {
                    alert("Failed to save configuration: " + (data ? data.message : "Unknown error"));
                }
            })
            .catch(err => alert("Error saving configurations: " + err));
        }

        // Delete tag from database
        function deleteTag() {
            if (!activeEditUser) return;
            const pw = document.getElementById("accessPassword").value.trim();

            if (!pw) {
                alert("Security Access Password is required to delete tags.");
                return;
            }

            if (!confirm(`Are you sure you want to delete the tag for ${activeEditUser}?`)) return;

            fetch("/api/delete", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-Password": pw
                },
                body: JSON.stringify({ username: activeEditUser })
            })
            .then(res => {
                if (res.status === 401) {
                    alert("Access Denied: Incorrect Security Password.");
                    return null;
                }
                return res.json();
            })
            .then(data => {
                if (data === null) return;
                if (data && data.success) {
                    alert("Tag deleted successfully!");
                    fetchTags();
                    resetForm();
                } else {
                    alert("Failed to delete tag: " + (data ? data.message : "Unknown error"));
                }
            })
            .catch(err => alert("Error deleting tag: " + err));
        }

        function resetForm() {
            activeEditUser = null;
            document.getElementById("username").value = "";
            document.getElementById("tagText").value = "";
            document.getElementById("pfpId").value = "";
            document.getElementById("bannerId").value = "";
            document.getElementById("sizeSelect").value = "normal";
            document.getElementById("tagFontSelect").value = "GothamBold";
            document.getElementById("displayFontSelect").value = "GothamBold";
            document.getElementById("useBorder").checked = false;
            document.getElementById("border-picker-wrapper").classList.add("hidden");
            document.getElementById("useGradient").checked = false;
            document.getElementById("solid-text-picker").classList.remove("hidden");
            document.getElementById("gradient-pickers").classList.add("hidden");
            document.getElementById("delete-btn").classList.add("hidden");
            updatePreview();
        }
    </script>
</body>
</html>
"""

def validate_password_and_get_access_name(provided_pw):
    provided_pw = provided_pw.strip()
    if not provided_pw:
        return None

    # Map passwords to Access names
    key_map = {}
    
    # 1. Map environment variables starting with ACCESS_
    for key, val in os.environ.items():
        if key.startswith("ACCESS_") and val:
            name = key.replace("ACCESS_", "Access ")
            key_map[val.strip()] = name

    # 2. Map standard PASSWORD and PANEL_PASSWORD
    main_pw = os.getenv("PASSWORD") or os.getenv("PANEL_PASSWORD")
    if main_pw:
        key_map[main_pw.strip()] = "Access 1"

    # 3. Map comma-separated PASSWORDS list
    passwords_csv = os.getenv("PASSWORDS")
    if passwords_csv:
        for idx, pw in enumerate(passwords_csv.split(",")):
            pw_strip = pw.strip()
            if pw_strip and pw_strip not in key_map:
                key_map[pw_strip] = f"Access {idx+1}"

    # If no passwords are configured on Render environment, allow access as "Unknown"
    if not key_map:
        return "Unknown"

    return key_map.get(provided_pw)

# Custom Handler for parsing API calls and serving Control Panel Dashboard
class ControlPanelHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # Suppress server request logs to keep Render's consoles clean
        pass

    def send_cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, X-Password")

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_cors_headers()
        self.end_headers()

    def do_GET(self):
        if self.path == "/":
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.send_cors_headers()
            self.end_headers()
            self.wfile.write(HTML_PANEL_CONTENT.encode("utf-8"))
        elif self.path == "/api/tags":
            success, sha, data = fetch_from_github()
            self.send_response(200 if success else 500)
            self.send_header("Content-type", "application/json")
            self.send_cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps({"success": success, "data": data, "error": sha if not success else None}).encode("utf-8"))
        elif self.path.startswith("/api/thumbnail"):
            from urllib.parse import urlparse, parse_qs
            parsed = urlparse(self.path)
            params = parse_qs(parsed.query)
            asset_id = params.get("id", [""])[0].strip()
            size = params.get("size", ["150x150"])[0].strip()
            
            if not asset_id.isdigit():
                self.send_response(400)
                self.send_cors_headers()
                self.end_headers()
                self.wfile.write(b"Invalid asset id")
                return
                
            roblox_url = f"https://thumbnails.roblox.com/v1/assets?assetIds={asset_id}&size={size}&format=Png"
            try:
                res = requests.get(roblox_url, timeout=5)
                if res.status_code == 200:
                    data = res.json()
                    if data and data.get("data") and len(data["data"]) > 0:
                        image_url = data["data"][0].get("imageUrl")
                        if image_url:
                            self.send_response(302)
                            self.send_header("Location", image_url)
                            self.send_cors_headers()
                            self.end_headers()
                            return
            except Exception as e:
                print(f"Error fetching roblox thumbnail: {e}")
                
            fallback_url = f"https://www.roblox.com/thumbs/asset.ashx?assetid={asset_id}&width=150&height=150"
            self.send_response(302)
            self.send_header("Location", fallback_url)
            self.send_cors_headers()
            self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"Not found")

    def do_POST(self):
        if self.path == "/api/save":
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            payload = json.loads(post_data.decode('utf-8'))
            
            # Verify password protection (checks multi-password map)
            provided_pw = self.headers.get("X-Password", "")
            access_name = validate_password_and_get_access_name(provided_pw)
            if not access_name:
                self.send_response(401)
                self.send_header("Content-type", "application/json")
                self.send_cors_headers()
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "message": "Unauthorized"}).encode("utf-8"))
                return
                
            username = payload.get("username", "").strip().lower()
            config = payload.get("config", {})
            config["createdBy"] = access_name
            
            if not username:
                self.send_response(400)
                self.send_header("Content-type", "application/json")
                self.send_cors_headers()
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "message": "Username is required"}).encode("utf-8"))
                return

            success, sha, data = fetch_from_github()
            if not success:
                self.send_response(500)
                self.send_header("Content-type", "application/json")
                self.send_cors_headers()
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "message": f"Failed to fetch tags: {sha}"}).encode("utf-8"))
                return
                
            data["players"][username] = config
            
            # Save local cache
            try:
                with open(JSON_FILE_PATH, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2)
            except Exception:
                pass
                
            ok, err = update_github(data, username, sha)
            self.send_response(200 if ok else 500)
            self.send_header("Content-type", "application/json")
            self.send_cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps({"success": ok, "message": "Success" if ok else err}).encode("utf-8"))
            
        elif self.path == "/api/delete":
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            payload = json.loads(post_data.decode('utf-8'))
            
            provided_pw = self.headers.get("X-Password", "")
            access_name = validate_password_and_get_access_name(provided_pw)
            if not access_name:
                self.send_response(401)
                self.send_header("Content-type", "application/json")
                self.send_cors_headers()
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "message": "Unauthorized"}).encode("utf-8"))
                return
                
            username = payload.get("username", "").strip().lower()
            if not username:
                self.send_response(400)
                self.send_cors_headers()
                self.end_headers()
                return

            success, sha, data = fetch_from_github()
            if not success:
                self.send_response(500)
                self.send_header("Content-type", "application/json")
                self.send_cors_headers()
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "message": f"Failed to fetch tags: {sha}"}).encode("utf-8"))
                return
                
            if username in data.get("players", {}):
                del data["players"][username]
                
                try:
                    with open(JSON_FILE_PATH, 'w', encoding='utf-8') as f:
                        json.dump(data, f, indent=2)
                except Exception:
                    pass
                    
                ok, err = update_github(data, username, sha)
                self.send_response(200 if ok else 500)
                self.send_header("Content-type", "application/json")
                self.send_cors_headers()
                self.end_headers()
                self.wfile.write(json.dumps({"success": ok, "message": "Deleted successfully" if ok else err}).encode("utf-8"))
            else:
                self.send_response(404)
                self.send_header("Content-type", "application/json")
                self.send_cors_headers()
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "message": "Player not found"}).encode("utf-8"))

def run_web():
    port = int(os.getenv("PORT", 8080))
    TCPServer.allow_reuse_address = True
    try:
        with TCPServer(("0.0.0.0", port), ControlPanelHandler) as httpd:
            print(f"Control panel web server running on port {port}")
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

# Helper function to check role permissions
def is_user_authorized(member):
    # Allow server owner/administrators
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

# ================= Discord Bot Commands =================

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name} ({bot.user.id})")

# Command error handling (e.g. missing role restriction)
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.send("You do not have the required role to run this command.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"Missing required arguments. Usage: `{ctx.prefix}{ctx.command.name} <username>`")
    else:
        print(f"Error running command: {error}")

@bot.command()
async def addtag(ctx):
    """
    Directs the user to the visual Web Control Panel to create, edit, and pick colors.
    """
    if not is_user_authorized(ctx.author):
        await ctx.send("You do not have the required role to run this command.")
        return

    url = os.getenv("PANEL_URL", "https://bot-kzu7.onrender.com")
    
    embed = discord.Embed(
        title="Nametags Visual Control Panel",
        description="Configure your nametags visually with color pickers, live previews, and automatic syncing!",
        color=discord.Color.purple()
    )
    embed.add_field(name="Link to Panel", value=f"[Click here to open the Control Panel]({url})")
    await ctx.send(embed=embed)

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
