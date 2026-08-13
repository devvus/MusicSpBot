# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# This file is part of AnonXMusic


import os
from pathlib import Path

from pyrogram import filters, types, enums

from anony import anon, app, config, db, lang, logger, queue, tg, yt
from anony.helpers import buttons, utils
from anony.helpers._play import checkUB


def playlist_to_queue(chat_id: int, tracks: list) -> str:
    text = "<blockquote expandable>"
    for track in tracks:
        pos = queue.add(chat_id, track)
        text += f"<b>{pos}.</b> {track.title}\n"
    text = text[:1948] + "</blockquote>"
    return text

@app.on_message(
    filters.command(["play", "playforce", "vplay", "vplayforce"])
    & filters.group
    & ~app.bl_users
)
@lang.language()
@checkUB
async def play_hndlr(
    _,
    m: types.Message,
    force: bool = False,
    m3u8: bool = False,
    video: bool = False,
    url: str = None,
) -> None:
    if not m or not hasattr(m, "chat"): return
    logger.info(f"DEBUG: play_hndlr started for chat {m.chat.id}")
    if await db.is_maintenance() and m.from_user.id not in app.sudoers:
        return await m.reply_text(m.lang["sudo_maint_notify"])
        
    sent = await m.reply_text(m.lang["play_searching"])
    logger.info(f"DEBUG: 'Searching' message sent: {sent.id}")
    file = None
    mention = m.from_user.mention
    media = tg.get_media(m.reply_to_message) if m.reply_to_message else None
    tracks = []

    if media:
        setattr(sent, "lang", m.lang)
        file = await tg.download(m.reply_to_message, sent)

    elif m3u8:
        file = await tg.process_m3u8(url, sent.id, video)

    elif url:
        if "playlist" in url:
            await sent.edit_text(m.lang["playlist_fetch"])
            tracks = await yt.playlist(
                config.PLAYLIST_LIMIT, mention, url, video
            )

            if not tracks:
                return await sent.edit_text(m.lang["playlist_error"])

            file = tracks[0]
            tracks.remove(file)
            file.message_id = sent.id
        else:
            file = await yt.search(url, sent.id, video=video)

        if not file:
            return await sent.edit_text(
                m.lang["play_not_found"].format(config.SUPPORT_CHAT)
            )

    elif len(m.command) >= 2:
        query = " ".join(m.command[1:])
        logger.info(f"DEBUG: Searching for query: {query}")
        file = await yt.search(query, sent.id, video=video)
        if not file:
            logger.warning(f"DEBUG: No file found for query: {query}")
            return await sent.edit_text(
                m.lang["play_not_found"].format(config.SUPPORT_CHAT)
            )
        logger.info(f"DEBUG: Search successful: {file.title}")

    if not file:
        return await sent.edit_text(m.lang["play_usage"])

    # Safely delete user's command message once track is found
    try:
        await m.delete()
    except Exception:
        pass

    if file.duration_sec > config.DURATION_LIMIT and m.from_user.id not in app.sudoers:
        return await sent.edit_text(
            m.lang["play_duration_limit"].format(config.DURATION_LIMIT // 60)
        )

    logger.info("DEBUG: Checking logger settings")
    if await db.is_logger():
        await utils.play_log(m, sent.link, file.title, file.duration)

    file.user = mention
    
    # Auto-force for Sudo users or force commands
    if force or m.from_user.id in app.sudoers:
        force = True
        logger.info(f"DEBUG: Force playing for {m.from_user.id}")
        queue.force_add(m.chat.id, file)
    else:
        position = queue.add(m.chat.id, file)
        logger.info(f"DEBUG: Queued at position {position}")

        # Only show queued message if it's NOT the first song
        if position != 0:
            logger.info("DEBUG: Song queued, editing message")
            await sent.edit_text(
                m.lang["play_queued"].format(
                    position,
                    file.url,
                    file.title,
                    file.duration,
                    m.from_user.mention,
                ),
                reply_markup=buttons.play_queued(
                    m.chat.id, file.id, m.lang["play_now"]
                ),
            )
            if tracks:
                added = playlist_to_queue(m.chat.id, tracks)
                await app.send_message(
                    chat_id=m.chat.id,
                    text=m.lang["playlist_queued"].format(len(tracks)) + added,
                )
            return

    if not file.file_path:
        # Check for any existing file with this ID
        found = False
        if Path("downloads").exists():
            for f in os.listdir("downloads"):
                if f.startswith(file.id):
                    file.file_path = os.path.join("downloads", f)
                    logger.info(f"DEBUG: File exists: {file.file_path}")
                    found = True
                    break
        
        if not found:
            logger.info(f"DEBUG: Downloading file: {file.id}")
            await sent.edit_text(m.lang["play_downloading"])
            file.file_path = await yt.download(file.id, video=video)
            logger.info(f"DEBUG: Download result: {file.file_path}")

    logger.info("DEBUG: Calling play_media")
    await anon.play_media(chat_id=m.chat.id, message=sent, media=file)
    if not tracks:
        return
    added = playlist_to_queue(m.chat.id, tracks)
    await app.send_message(
        chat_id=m.chat.id,
        text=m.lang["playlist_queued"].format(len(tracks)) + added,
    )
