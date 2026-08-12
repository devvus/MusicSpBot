# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# This file is part of AnonXMusic


import asyncio

from pyrogram import enums, errors, types

from anony import app, config, db, logger, queue, yt
from anony.helpers import utils


def checkUB(play):
    async def wrapper(_, m: types.Message):
        logger.info(f"DEBUG: checkUB wrapper called for chat {m.chat.id}")
        if not m.from_user:
            return await m.reply_text(m.lang["play_user_invalid"])

        chat_id = m.chat.id
        if m.chat.type not in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
            return await m.reply_text("🌸 I'm so sorry, but you can only play music in a **Group Chat**! Please add me to a group to start the party! ✨")

        if not m.reply_to_message and (
            len(m.command) < 2 or (len(m.command) == 2 and m.command[1] == "-f")
        ):
            return await m.reply_text(m.lang["play_usage"])

        if len(queue.get_queue(chat_id)) >= config.QUEUE_LIMIT and m.from_user.id not in app.sudoers:
            return await m.reply_text(m.lang["play_queue_full"].format(config.QUEUE_LIMIT))

        force = m.command[0].endswith("force") or (
            len(m.command) > 1 and "-f" in m.command[1]
        )
        video = m.command[0][0] == "v" and config.VIDEO_PLAY
        url = utils.get_url(m)
        if url and yt.invalid(url):
            return await m.reply_text(m.lang["play_not_found"].format(config.SUPPORT_CHAT))
        m3u8 = url and not yt.valid(url)

        play_mode = await db.get_play_mode(chat_id)
        if play_mode or force:
            adminlist = await db.get_admins(chat_id)
            if (
                m.from_user.id not in adminlist
                and not await db.is_auth(chat_id, m.from_user.id)
                and not m.from_user.id in app.sudoers
            ):
                return await m.reply_text(m.lang["play_admin"])

        logger.info(f"DEBUG: active_calls keys: {list(db.active_calls.keys())}")
        if chat_id not in db.active_calls:
            logger.info(f"DEBUG: chat {chat_id} not in active_calls, fetching client")
            client = await db.get_client(chat_id)
            if not client:
                logger.warning(f"DEBUG: no client found for chat {chat_id}")
                return await m.reply_text("🌸 I'm so sorry, but my assistant is currently offline. Please check back in a few minutes! ✨")
            logger.info(f"DEBUG: client {client.id} found, checking chat membership")
            try:
                member = await app.get_chat_member(chat_id, client.id)
                if member.status in [
                    enums.ChatMemberStatus.BANNED,
                    enums.ChatMemberStatus.RESTRICTED,
                ]:
                    try:
                        await app.unban_chat_member(
                            chat_id=chat_id, user_id=client.id
                        )
                    except Exception:
                        return await m.reply_text(
                            m.lang["play_banned"].format(
                                app.name,
                                client.id,
                                client.mention,
                                f"@{client.username}" if client.username else None,
                            )
                        )
            except errors.ChatAdminRequired:
                return await m.reply_text(m.lang["admin_required"])
            except (errors.UserNotParticipant, errors.exceptions.bad_request_400.UserNotParticipant):
                if m.chat.username:
                    invite_link = m.chat.username
                    try:
                        await client.resolve_peer(invite_link)
                    except Exception:
                        pass
                else:
                    try:
                        invite_link = (await app.get_chat(chat_id)).invite_link
                        if not invite_link:
                            invite_link = await app.export_chat_invite_link(chat_id)
                    except errors.ChatAdminRequired:
                        return await m.reply_text(m.lang["admin_required"])
                    except Exception as ex:
                        return await m.reply_text(
                            m.lang["play_invite_error"].format(type(ex).__name__)
                        )

                umm = await m.reply_text(m.lang["play_invite"].format(app.name))
                await asyncio.sleep(2)
                try:
                    await client.join_chat(invite_link)
                except errors.UserAlreadyParticipant:
                    pass
                except errors.InviteRequestSent:
                    await asyncio.sleep(2)
                    try:
                        await app.approve_chat_join_request(chat_id, client.id)
                    except errors.HideRequesterMissing:
                        pass
                    except Exception as ex:
                        return await umm.edit_text(
                            m.lang["play_invite_error"].format(type(ex).__name__)
                        )
                except Exception as ex:
                    logger.error(f"Error joining chat - {chat_id}: {ex}")
                    return await umm.edit_text(
                        m.lang["play_invite_error"].format(type(ex).__name__)
                    )

                await umm.delete()
                await client.resolve_peer(chat_id)

        if await db.get_cmd_delete(chat_id):
            try:
                await m.delete()
            except Exception:
                pass

        return await play(_, m, force, m3u8, video, url)

    return wrapper
