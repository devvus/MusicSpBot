# DevuxMitsu - The Love Hashira Music Bot
# Premium Telegram Music Streaming Engine
# Inspired by Mitsuri Kanroji 🌸🌺


import pyrogram

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
        self.logger = config.LOGGER_ID
        
        # Internal sets for storage
        self._sudoers = {config.OWNER_ID}
        self._bl_users = set()
        
        # Pyrogram filters that reference these sets
        self.sudoers = pyrogram.filters.user(self._sudoers)
        self.bl_users = pyrogram.filters.user(self._bl_users)
        
        # Patch filter objects to behave like sets for compatibility
        self.sudoers.add = self._sudoers.add
        self.sudoers.discard = self._sudoers.discard
        self.sudoers.remove = self._sudoers.remove
        self.sudoers.__contains__ = self._sudoers.__contains__
        self.sudoers.__iter__ = lambda: iter(self._sudoers)
        self.sudoers.__len__ = lambda: len(self._sudoers)
        
        self.bl_users.add = self._bl_users.add
        self.bl_users.discard = self._bl_users.discard
        self.bl_users.remove = self._bl_users.remove
        self.bl_users.__contains__ = self._bl_users.__contains__
        self.bl_users.__iter__ = lambda: iter(self._bl_users)
        self.bl_users.__len__ = lambda: len(self._bl_users)

    async def boot(self):
        """
        Starts the bot and performs initial setup.

        Raises:
            SystemExit: If the bot fails to access the log group or is not an administrator in the logger group.
        """
        
        @self.on_message(pyrogram.filters.all, group=-100)
        async def log_all_messages(_, m):
            if m.text or m.caption:
                logger.info(f"DEBUG: Received message: {m.text} from {m.from_user.id if m.from_user else 'None'} in {m.chat.id}")
        
        await super().start()
        self.id = self.me.id
        self.name = self.me.first_name
        self.username = self.me.username
        self.mention = self.me.mention

        try:
            get = await self.get_chat_member(self.logger, self.id)
        except Exception as ex:
            raise SystemExit(f"Bot has failed to access the log group: {self.logger}\nReason: {ex}")

        if get.status != pyrogram.enums.ChatMemberStatus.ADMINISTRATOR:
            raise SystemExit("Please promote the bot as an admin in logger group.")
        logger.info(f"Instance [1786566646] - Bot started as @{self.username}")

    async def exit(self):
        """
        Asynchronously stops the bot.
        """
        await super().stop()
        logger.info("Bot stopped.")
