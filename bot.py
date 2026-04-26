import asyncio
import logging
import os
from typing import Dict

from dotenv import load_dotenv
from telethon import TelegramClient, events
from telethon.errors import SessionPasswordNeededError


load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger("offline-reply-bot")


def get_required_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise ValueError(f"Missing required environment variable: {name}")
    return value


API_ID = int(get_required_env("API_ID"))
API_HASH = get_required_env("API_HASH")
PHONE = get_required_env("PHONE")
AWAY_MESSAGE = os.getenv(
    "AWAY_MESSAGE",
    "⚠ I am offline now\n⏳ please wait...\nThanks for your message. I will reply when I am back online.\n━━━━━━━━━━━━━━━━━━\n🇰🇭 ខ្ញុំមិនអនឡាញទេ\n⏳ សូមរង់ចាំ...\nអរគុណសម្រាប់សារ ខ្ញុំនឹងឆ្លើយតបវិញពេលខ្ញុំអនឡាញ។",
).replace("\\n", "\n").strip()
AUTO_REPLY_ENABLED = os.getenv("AUTO_REPLY_ENABLED", "1").strip() == "1"

client = TelegramClient("personal_offline_reply", API_ID, API_HASH)
last_auto_reply_message_id: Dict[int, int] = {}
auto_reply_enabled = AUTO_REPLY_ENABLED
away_message = AWAY_MESSAGE


def normalize_message_text(text: str) -> str:
    return text.replace("\\n", "\n").strip()


def set_away_message(text: str) -> str:
    global away_message
    away_message = normalize_message_text(text)
    return away_message


async def delete_previous_auto_reply(chat_id: int) -> None:
    message_id = last_auto_reply_message_id.get(chat_id)
    if message_id is None:
        return

    try:
        await client.delete_messages(chat_id, message_id)
    except Exception as exc:  # pragma: no cover
        logger.debug(
            "Could not delete previous auto-reply in chat_id=%s: %s", chat_id, exc
        )
    finally:
        last_auto_reply_message_id.pop(chat_id, None)


@client.on(events.NewMessage(incoming=True))
async def auto_reply_handler(event: events.NewMessage.Event) -> None:
    global auto_reply_enabled

    if not auto_reply_enabled:
        return

    if not event.is_private:
        return

    sender = await event.get_sender()
    if sender is None:
        return

    # Ignore your own messages and bot accounts
    if getattr(sender, "is_self", False) or getattr(sender, "bot", False):
        return

    chat_id = event.chat_id
    if chat_id is None:
        return

    try:
        await delete_previous_auto_reply(chat_id)
        sent = await event.reply(away_message)
        last_auto_reply_message_id[chat_id] = sent.id
        logger.info("Auto-replied in chat_id=%s", chat_id)
    except Exception as exc:  # pragma: no cover
        logger.exception("Failed to send auto-reply: %s", exc)


@client.on(events.NewMessage(outgoing=True, pattern=r"(?i)^/(away|offline)\s+(on|off)$"))
async def toggle_handler(event: events.NewMessage.Event) -> None:
    global auto_reply_enabled

    _, state = event.raw_text.strip().split()
    auto_reply_enabled = state.lower() == "on"
    status = "ON" if auto_reply_enabled else "OFF"
    await event.reply(f"Auto-reply is now {status}.")
    logger.info("Auto-reply toggled to %s", status)


@client.on(events.NewMessage(outgoing=True, pattern=r"(?i)^/away\s+status$"))
async def status_handler(event: events.NewMessage.Event) -> None:
    status = "ON" if auto_reply_enabled else "OFF"
    await event.reply(f"Auto-reply: {status} | Cooldown: OFF")


@client.on(events.NewMessage(outgoing=True, pattern=r"(?i)^/away\s+set\s+(.+)$"))
async def set_message_handler(event: events.NewMessage.Event) -> None:
    raw = event.raw_text.strip()
    new_text = raw.split(maxsplit=2)[2]
    updated = set_away_message(new_text)
    await event.reply(
        "Auto-reply message updated.\n"
        "Tip: use \\n for new lines.\n\n"
        f"Preview:\n{updated}"
    )


@client.on(events.NewMessage(outgoing=True, pattern=r"(?i)^/away\s+show$"))
async def show_message_handler(event: events.NewMessage.Event) -> None:
    await event.reply(f"Current auto-reply message:\n{away_message}")


@client.on(events.NewMessage(outgoing=True))
async def cleanup_on_manual_reply(event: events.NewMessage.Event) -> None:
    if not event.is_private:
        return

    if event.raw_text.strip().lower().startswith("/away"):
        return

    chat_id = event.chat_id
    if chat_id is None:
        return

    await delete_previous_auto_reply(chat_id)


async def main() -> None:
    await client.connect()
    if not await client.is_user_authorized():
        await client.send_code_request(PHONE)
        code = input("Enter the Telegram login code: ").strip()
        try:
            await client.sign_in(PHONE, code)
        except SessionPasswordNeededError:
            password = input("Enter your Telegram 2FA password: ").strip()
            await client.sign_in(password=password)

    me = await client.get_me()
    logger.info("Logged in as %s", me.username or me.first_name or me.id)
    logger.info("Auto-reply starts as %s", "ON" if auto_reply_enabled else "OFF")
    logger.info("Listening for private messages...")

    await client.run_until_disconnected()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Stopped by user")
