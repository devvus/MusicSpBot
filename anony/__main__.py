# DevuxMitsu - The Love Hashira Music Bot
# Premium Telegram Music Streaming Engine
# Inspired by Mitsuri Kanroji 🌸🌺


import asyncio
import signal
import importlib
from contextlib import suppress

from anony import (anon, app, config, db, logger,
                   stop, thumb, userbot, yt)
from anony.plugins import all_modules


async def idle():
    loop = asyncio.get_running_loop()
    stop_event = asyncio.Event()

    for sig in (signal.SIGINT, signal.SIGTERM, signal.SIGABRT):
        with suppress(NotImplementedError):
            loop.add_signal_handler(sig, stop_event.set)
    await stop_event.wait()

async def main():
    await db.connect()
    await app.boot()
    await userbot.boot()
    await anon.boot()
    await thumb.start()

    for module in all_modules:
        importlib.import_module(f"anony.plugins.{module}")
    logger.info(f"Loaded {len(all_modules)} modules.")

    # if config.COOKIES_URL:
    #     await yt.save_cookies(config.COOKIES_URL)

    sudoers = await db.get_sudoers()
    for user_id in sudoers:
        app.sudoers.add(user_id)
    app.sudoers.add(config.OWNER_ID)
    
    blacklisted = await db.get_blacklisted()
    for chat_id in blacklisted:
        app.bl_users.add(chat_id)
        
    logger.info(f"Loaded {len(app._sudoers)} sudo users.")

    await idle()
    asyncio.create_task(stop())


if __name__ == "__main__":
    try:
        asyncio.get_event_loop().run_until_complete(main())
    except KeyboardInterrupt:
        pass
