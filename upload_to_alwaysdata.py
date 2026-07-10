import ftplib
import os
import getpass

print("=== Alwaysdata Bot File Uploader ===")
password = getpass.getpass("Enter your Alwaysdata account password: ")

try:
    print("Connecting to ftp-cispn.alwaysdata.net...")
    ftp = ftplib.FTP("ftp-cispn.alwaysdata.net")
    ftp.login(user="cispn", passwd=password)
    
    print("Creating 'bot' directory...")
    try:
        ftp.mkd("bot")
    except Exception:
        pass  # Already exists
        
    ftp.cwd("bot")
    
    files_to_upload = ["discord_bot.py", "requirements.txt", ".env"]
    for filename in files_to_upload:
        if os.path.exists(filename):
            print(f"Uploading {filename}...")
            with open(filename, "rb") as f:
                ftp.storbinary(f"STOR {filename}", f)
            print(f"Uploaded {filename} successfully.")
        else:
            print(f"Warning: {filename} not found locally, skipping.")
            
    ftp.quit()
    print("\n🎉 Success! All files uploaded to Alwaysdata!")
except Exception as e:
    print(f"\n❌ Error during upload: {e}")

input("\nPress Enter to exit...")
