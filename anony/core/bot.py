# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# This file is part of AnonXMusic

import pyrogram
from pyrogram import filters
from anony import config, logger


class Bot(pyrogram.Client):
    def __init__(self):
        super().__init__(
            name="anony",
            api_id=config.API_ID,
            api_hash=config.API_HASH,
            bot_token=config.BOT_TOKEN,
            parse_mode=pyrogram.enums.ParseMode.HTML,
            max_concurrent_transmissions=7,
            link_preview_options=pyrogram.types.LinkPreviewOptions(is_disabled=True),
        )
        self.owner = config.OWNER_ID
        self.logger_id = config.LOGGER_ID
        
        # Internal sets for storage
        self._sudoers = {config.OWNER_ID}
        self._bl_users = set()
        
        # Dynamic filters
        self.sudoers = filters.create(lambda _, __, m: bool(m.from_user and m.from_user.id in self._sudoers))
        self.bl_users = filters.create(lambda _, __, m: bool(m.from_user and m.from_user.id in self._bl_users))
        
        # Expose methods and attributes for compatibility
        for attr in ['add', 'discard', 'remove', '__contains__', '__iter__', '__len__']:
            setattr(self.sudoers, attr, getattr(self._sudoers, attr))
            setattr(self.bl_users, attr, getattr(self._bl_users, attr))

    async def boot(self):
        """
        Starts the bot and performs initial setup.
        """
        
        # Log all messages for debugging
        @self.on_message(filters.all, group=-100)
        async def log_all_messages(_, m):
            if m.text or m.caption:
                logger.info(f"DEBUG: Received message: {m.text[:50] if m.text else m.caption[:50]} from {m.from_user.id if m.from_user else 'None'} in {m.chat.id}")
        
        await super().start()
        self.id = self.me.id
        self.name = self.me.first_name
        self.username = self.me.username
        self.mention = self.me.mention

        # Verify logger access
        try:
            get = await self.get_chat_member(self.logger_id, self.id)
            if get.status != pyrogram.enums.ChatMemberStatus.ADMINISTRATOR:
                logger.warning("Bot is not an admin in the logger group. Please promote it.")
        except Exception as ex:
            logger.error(f"Bot failed to access the log group: {self.logger_id}. Reason: {ex}")

        logger.info(f"Instance [1786566646] - Bot started as @{self.username}")

    async def exit(self):
        """
        Asynchronously stops the bot.
        """
        await super().stop()
        logger.info("Bot stopped.")
