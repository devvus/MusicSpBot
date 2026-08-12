# DevuxMitsu - The Love Hashira Music Bot
# Premium Telegram Music Streaming Engine
# Inspired by Mitsuri Kanroji 🌸🌺


import os

from pyrogram import StopPropagation, filters, types

from anony import app, db, lang, queue
from anony.helpers._admins import sudo_only


@app.on_message(filters.command(["ac", "activevc"]))
@lang.language()
@sudo_only
async def _activevc(_, m: types.Message):
    if not db.active_calls:
        return await m.reply_text(m.lang["vc_empty"])

    if m.command[0] == "ac":
        await m.reply_text(m.lang["vc_count"].format(len(db.active_calls)))
        raise StopPropagation

    sent = await m.reply_text(m.lang["vc_fetching"])
    text = ""

    for i, chat in enumerate(db.active_calls):
        playing = queue.get_current(chat)
        text += f"\n{i+1}. <code>{chat}</code>\n    ➜ {playing.title[:25]}"

    if len(text) < 4000:
        await sent.edit_text(m.lang["vc_list"] + text)
        raise StopPropagation

    with open("activevc.txt", "w") as f:
        f.write(text)
    f.close()
    await sent.edit_media(
        media=types.InputMediaDocument(
            media="activevc.txt",
            caption=m.lang["vc_list"],
        )
    )
    os.remove("activevc.txt")
    raise StopPropagation
