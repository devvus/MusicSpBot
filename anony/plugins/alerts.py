# DevuxMitsu - The Love Hashira Music Bot
# Premium Telegram Music Streaming Engine
# Inspired by Mitsuri Kanroji 🌸🌺

from pyrogram import filters, types, enums
from anony import app, db, lang, logger

@app.on_message(filters.new_chat_members)
async def sudo_gc_join_alert(_, m: types.Message):
    """
    Triggered when a new member joins the group.
    Alerts if the member is a SUDO_USER.
    """
    for user in m.new_chat_members:
        if user.id in app.sudoers:
            try:
                # Fetch language for the chat
                _lang = await lang.get_lang(m.chat.id)
                
                # Format and send the alert
                alert_text = _lang["sudo_gc_join"].format(user.id, user.first_name)
                await m.reply_text(alert_text, disable_web_page_preview=False)
            except Exception as e:
                logger.error(f"GC Join Alert Error: {e}")

@app.on_raw_update()
async def sudo_vc_join_alert(_, update, users, chats):
    """
    Raw update listener to detect when a user joins the Voice Chat.
    """
    # Pyrogram raw update for Voice Chat participants
    # This is a bit complex as it depends on the specific MTProto update type
    # For now, we'll focus on the GC join alert as requested.
    pass
