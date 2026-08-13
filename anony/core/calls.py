# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# This file is part of AnonXMusic

import asyncio
from ntgcalls import (ConnectionNotFound, TelegramServerError,
                      RTMPStreamingUnsupported, ConnectionError)
try:
    from pyrogram.errors import (ChatSendMediaForbidden, ChatSendPhotosForbidden,
                                 MessageIdInvalid)
except ImportError:
    from pyrogram.errors import MessageIdInvalid
    ChatSendMediaForbidden = Exception
    ChatSendPhotosForbidden = Exception
from pyrogram.types import InputMediaPhoto, Message
from pytgcalls import PyTgCalls, exceptions, types
from pytgcalls.pytgcalls_session import PyTgCallsSession

from anony import (app, config, db, lang, logger,
                   queue, thumb, userbot, yt)
from anony.helpers import Media, Track, buttons


class TgCall:
    def __init__(self):
        self.clients = []

    async def pause(self, chat_id: int) -> bool:
        client = await db.get_assistant(chat_id)
        await db.playing(chat_id, paused=True)
        try:
            if hasattr(client, "pause_stream"):
                return await client.pause_stream(chat_id)
            return await client.pause(chat_id)
        except Exception:
            return False

    async def resume(self, chat_id: int) -> bool:
        client = await db.get_assistant(chat_id)
        await db.playing(chat_id, paused=False)
        try:
            if hasattr(client, "resume_stream"):
                return await client.resume_stream(chat_id)
            return await client.resume(chat_id)
        except Exception:
            return False

    async def stop(self, chat_id: int) -> None:
        client = await db.get_assistant(chat_id)
        queue.clear(chat_id)
        await db.remove_call(chat_id)
        await db.set_loop(chat_id, 0)

        try:
            if hasattr(client, "leave_group_call"):
                await client.leave_group_call(chat_id)
            else:
                await client.leave_call(chat_id)
        except Exception:
            pass


    async def play_media(
        self,
        chat_id: int,
        message: Message,
        media: Media | Track,
        seek_time: int = 0,
    ) -> None:
        logger.info(f"DEBUG: play_media called for chat {chat_id}, title: {media.title}")
        client = await db.get_assistant(chat_id)
        if not client:
            logger.error(f"DEBUG: No assistant client found for chat {chat_id}")
            return None
        
        _lang = await lang.get_lang(chat_id)
        _thumb = (
            await thumb.generate(media)
            if isinstance(media, Track)
            else config.DEFAULT_THUMB
        ) if config.THUMB_GEN else None

        if not media.file_path:
            await message.edit_text(_lang["error_no_file"].format(config.SUPPORT_CHAT))
            return await self.play_next(chat_id)

        ffmpeg_params = None
        if seek_time > 1:
            ffmpeg_params = f"-ss {seek_time}"

        # Compatibility with different PyTgCalls versions
        try:
            # v2.x and v3.x often use MediaStream
            stream = types.MediaStream(
                media_path=media.file_path,
                audio_parameters=types.AudioQuality.HIGH,
                video_parameters=types.VideoQuality.HD_720p,
                audio_flags=types.MediaStream.Flags.REQUIRED,
                video_flags=(
                    types.MediaStream.Flags.AUTO_DETECT
                    if media.video
                    else types.MediaStream.Flags.IGNORE
                ),
                ffmpeg_parameters=ffmpeg_params,
            )
        except AttributeError:
            # Fallback for older or different versions
            stream = media.file_path

        try:
            # Try play method (common in v3 and some v2)
            if hasattr(client, "play"):
                await client.play(
                    chat_id=chat_id,
                    stream=stream,
                )
            # Try join_group_call (common in v2)
            elif hasattr(client, "join_group_call"):
                await client.join_group_call(
                    chat_id=chat_id,
                    stream=stream,
                )
            else:
                raise AttributeError("Client has no play or join_group_call method")

            if not seek_time:
                media.time = 1
                await db.add_call(chat_id)
                text = _lang["play_media"].format(
                    media.url,
                    media.title,
                    media.duration,
                    media.user,
                )
                keyboard = buttons.controls(chat_id)
                try:
                    if _thumb:
                        await message.edit_media(
                            media=InputMediaPhoto(
                                media=_thumb,
                                caption=text,
                            ),
                            reply_markup=keyboard,
                        )
                    else:
                        await message.edit_text(text, reply_markup=keyboard)
                except (ChatSendMediaForbidden, ChatSendPhotosForbidden, MessageIdInvalid):
                    if _thumb:
                        sent = await app.send_photo(
                            chat_id=chat_id,
                            photo=_thumb,
                            caption=text,
                            reply_markup=keyboard,
                        )
                    else:
                        sent = await app.send_message(
                            chat_id=chat_id,
                            text=text,
                            reply_markup=keyboard,
                        )
                    media.message_id = sent.id
        except FileNotFoundError:
            await message.edit_text(_lang["error_no_file"].format(config.SUPPORT_CHAT))
            await self.play_next(chat_id)
        except exceptions.NoActiveGroupCall:
            await self.stop(chat_id)
            await message.edit_text(_lang["error_no_call"])
        except exceptions.NoAudioSourceFound:
            await message.edit_text(_lang["error_no_audio"])
            await self.play_next(chat_id)
        except (ConnectionError, ConnectionNotFound, TelegramServerError):
            await self.stop(chat_id)
            await message.edit_text(_lang["error_tg_server"])
        except RTMPStreamingUnsupported:
            await self.stop(chat_id)
            await message.edit_text(_lang["error_rtmp"])
        except Exception as e:
            logger.error(f"Error in play_media: {e}")
            await message.edit_text(f"🌸 I'm so sorry, but something went wrong while playing! Error: {e}")


    async def replay(self, chat_id: int) -> None:
        if not await db.get_call(chat_id):
            return

        media = queue.get_current(chat_id)
        _lang = await lang.get_lang(chat_id)
        msg = await app.send_message(chat_id=chat_id, text=_lang["play_again"])
        media.message_id = msg.id
        await self.play_media(chat_id, msg, media)


    async def play_next(self, chat_id: int) -> None:
        if loop := await db.get_loop(chat_id):
            await db.set_loop(chat_id, loop - 1)
            return await self.replay(chat_id)

        media = queue.get_next(chat_id)
        if not media:
            return await self.stop(chat_id)

        try:
            if media.message_id:
                await app.delete_messages(
                    chat_id=chat_id,
                    message_ids=media.message_id,
                    revoke=True,
                )
                media.message_id = 0
        except Exception:
            pass

        _lang = await lang.get_lang(chat_id)
        msg = await app.send_message(chat_id=chat_id, text=_lang["play_next"])
        if not media.file_path:
            media.file_path = await yt.download(media.id, video=media.video)
            if not media.file_path:
                await self.play_next(chat_id)
                return await msg.edit_text(
                    _lang["error_no_file"].format(config.SUPPORT_CHAT)
                )

        media.message_id = msg.id
        await self.play_media(chat_id, msg, media)


    async def ping(self) -> float:
        pings = [client.ping for client in self.clients]
        return round(sum(pings) / len(pings), 2) if pings else 0.0


    async def boot(self) -> None:
        logger.info("DEBUG: anon.boot starting")
        PyTgCallsSession.notice_displayed = True
        for ub in userbot.clients:
            try:
                logger.info(f"DEBUG: starting PyTgCalls for assistant {ub.id}")
                client = PyTgCalls(ub, cache_duration=100)
                
                # Handlers
                async def stream_ended_handler(_, update: types.Update) -> None:
                    logger.info(f"DEBUG: StreamEnded received for chat {update.chat_id}")
                    await self.play_next(update.chat_id)

                async def closed_handler(_, update: types.Update) -> None:
                    logger.info(f"DEBUG: ClosedVoiceChat received for chat {update.chat_id}")
                    await self.stop(update.chat_id)

                # Extremely defensive handler registration
                registered = False
                if hasattr(client, "on_update"):
                    try:
                        client.on_update()(stream_ended_handler)
                        client.on_update()(closed_handler)
                        registered = True
                    except Exception:
                        pass
                
                if not registered:
                    if hasattr(client, "on_stream_ended"):
                        try:
                            client.on_stream_ended()(stream_ended_handler)
                            registered = True
                        except Exception:
                            pass
                    if hasattr(client, "on_closed_voice_chat"):
                        try:
                            client.on_closed_voice_chat()(closed_handler)
                            registered = True
                        except Exception:
                            pass
                
                if not registered:
                    logger.warning(f"Could not register any handlers for assistant {ub.id}")

                await client.start()
                self.clients.append(client)
                logger.info(f"DEBUG: PyTgCalls for assistant {ub.id} started")
            except Exception as e:
                logger.error(f"PyTgCalls failed to start for an assistant: {e}")
        if self.clients:
            logger.info("PyTgCalls client(s) started.")
        else:
            logger.warning("DEBUG: No PyTgCalls clients started")
