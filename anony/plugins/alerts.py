# DevuxMitsu - The Love Hashira Music Bot
# Premium Telegram Music Streaming Engine
# Inspired by Mitsuri Kanroji 🌸🌺

from pyrogram import filters, types, enums
from anony import app, db, lang, logger

# Note: sudo_gc_join_alert has been moved to start.py to prevent duplicate responses.

@app.on_raw_update()
async def sudo_vc_join_alert(_, update, users, chats):
    """
    Raw update listener to detect when a user joins the Voice Chat.
    """
    # Pyrogram raw update for Voice Chat participants
    # This is a bit complex as it depends on the specific MTProto update type
    # For now, we'll focus on the GC join alert as requested.
    pass
