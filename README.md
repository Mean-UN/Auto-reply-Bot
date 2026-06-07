# Personal Offline Auto-Reply (Telegram)

This project auto-replies to private Telegram messages when you are offline/away.

## What it does
- Uses your Telegram account session (not a separate bot account).
- Replies only in private chats.
- Skips bots and your own messages.
- Uses a per-chat cooldown before sending another auto-reply to the same person.
- Deletes the previous auto-reply in that chat before sending a new one.
- Deletes the auto-reply and pauses future auto-replies in that chat when you manually send a message.
- Lets you toggle at runtime with chat commands.

## Requirements
- Python 3.10+
- Telegram account
- Telegram API credentials from https://my.telegram.org

## Setup
1. Install dependencies:
   ```powershell
   pip install -r requirements.txt
   ```
2. Copy env file:
   ```powershell
   Copy-Item .env.example .env
   ```
3. Edit `.env` and set:
   - `API_ID`
   - `API_HASH`
   - `PHONE`
   - Optional: `AWAY_MESSAGE`, `AUTO_REPLY_ENABLED`, `AUTO_REPLY_COOLDOWN_SECONDS`
   - For multi-line message in `.env`, use `\n` for new lines.

## Run
```powershell
python bot.py
```
First run asks for Telegram login code and 2FA password (if enabled).

## Chat commands (send from your own account)
- `/away on` -> enable auto-reply
- `/away off` -> disable auto-reply
- `/away status` -> show current status
- `/away set your text here` -> change auto-reply text while bot is running
- `/away show` -> show current auto-reply text

## Notes
- Keep this script running on your PC/VPS.
- If you stop it, auto-replies stop.
- Sending `/away on` also clears chats paused by manual replies, so auto-replies start fresh.
- Set `AUTO_REPLY_COOLDOWN_SECONDS=0` to disable cooldown and reply to every incoming message.
- Use responsibly and follow Telegram terms.

## Host on AWS (EC2 Ubuntu)
1. Launch an Ubuntu EC2 instance (t3.micro is enough) and allow SSH (port 22) in Security Group.
2. SSH into server:
   ```bash
   ssh -i /path/to/key.pem ubuntu@YOUR_EC2_PUBLIC_IP
   ```
3. Install system packages:
   ```bash
   sudo apt update
   sudo apt install -y python3 python3-venv python3-pip git
   ```
4. Clone project and install Python deps:
   ```bash
   git clone https://github.com/YOUR_USERNAME/YOUR_REPO.git
   cd YOUR_REPO
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   cp .env.example .env
   nano .env
   ```
5. First login run (required once to create Telegram session):
   ```bash
   source .venv/bin/activate
   python bot.py
   ```
   Enter Telegram OTP/2FA, wait until bot is running, then stop with `Ctrl + C`.
6. Create systemd service:
   ```bash
   sudo nano /etc/systemd/system/telegram-away-bot.service
   ```
   Paste:
   ```ini
   [Unit]
   Description=Telegram Away Bot
   After=network.target

   [Service]
   User=ubuntu
   WorkingDirectory=/home/ubuntu/YOUR_REPO
   Environment=PYTHONUNBUFFERED=1
   ExecStart=/home/ubuntu/YOUR_REPO/.venv/bin/python /home/ubuntu/YOUR_REPO/bot.py
   Restart=always
   RestartSec=5

   [Install]
   WantedBy=multi-user.target
   ```
7. Enable and start service:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable telegram-away-bot
   sudo systemctl start telegram-away-bot
   ```
8. Check logs/status:
   ```bash
   sudo systemctl status telegram-away-bot
   journalctl -u telegram-away-bot -f
   ```
