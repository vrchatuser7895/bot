@echo off
title Roblox Nametags Discord Bot
echo Installing/Verifying dependencies...
pip install discord.py requests python-dotenv --quiet
echo Starting Discord Bot...
py discord_bot.py
pause
