import json
import os
import re

def parse_hex_color(hex_str):
    if not hex_str:
        return None
    hex_str = hex_str.strip().lstrip('#')
    if len(hex_str) == 3:
        hex_str = ''.join([c*2 for c in hex_str])
    if len(hex_str) != 6:
        print("Invalid hex color format. Skipping color.")
        return None
    try:
        r = int(hex_str[0:2], 16)
        g = int(hex_str[2:4], 16)
        b = int(hex_str[4:6], 16)
        return [r, g, b]
    except ValueError:
        print("Invalid hex color values. Skipping color.")
        return None

def format_asset_id(asset_id):
    if not asset_id:
        return ""
    asset_id = asset_id.strip()
    if not asset_id.isdigit():
        digits = re.findall(r'\d+', asset_id)
        if digits:
            asset_id = digits[0]
        else:
            return asset_id
    return f"rbxassetid://{asset_id}"

def main():
    json_path = "Tags.json"
    data = {"players": {}}
    if os.path.exists(json_path):
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if "players" not in data:
                    data["players"] = {}
        except Exception as e:
            print(f"Error loading Tags.json: {e}. Starting fresh.")
    
    print("=== Roblox Nametags Custom Tag Bot ===")
    username = input("Enter target player's username: ").strip()
    if not username:
        print("Username cannot be empty.")
        return
        
    tag_text = input("Enter tag text (e.g. OWNER, DEVELOPER): ").strip()
    if not tag_text:
        print("Tag text cannot be empty.")
        return

    banner_id = input("Enter Banner/Background Asset ID (or press Enter for none): ").strip()
    pfp_id = input("Enter PFP/Icon Asset ID (or press Enter for none): ").strip()
    border_hex = input("Enter Border Color Hex (e.g. #FF0000 or press Enter for none): ").strip()
    text_hex = input("Enter Text Color Hex (e.g. #FFFFFF or press Enter for none): ").strip()
    bg_hex = input("Enter Primary Tag Background Color Hex (e.g. #141414 or press Enter for default dark): ").strip()

    player_config = {
        "tag": tag_text,
        "bgImage": format_asset_id(banner_id),
        "image": format_asset_id(pfp_id),
        "borderColor": parse_hex_color(border_hex),
        "textColor": parse_hex_color(text_hex),
        "primaryColor": parse_hex_color(bg_hex) or [20, 20, 20]
    }
    
    player_config = {k: v for k, v in player_config.items() if v is not None and v != ""}
    
    data["players"][username.lower()] = player_config
    
    try:
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        print(f"\nSuccessfully added/updated custom tag for {username} in Tags.json!")
    except Exception as e:
        print(f"Failed to save Tags.json: {e}")

if __name__ == "__main__":
    main()
