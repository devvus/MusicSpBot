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
        self.sudoers = pyrogram.filters.user()
        self.bl_users = pyrogram.filters.user()

    async def boot(self):
        """
        Starts the bot and performs initial setup.

        Raises:
            SystemExit: If the bot fails to access the log group or is not an administrator in the logger group.
        """
        
        @self.on_message(pyrogram.filters.all, group=-100)
        async def log_all_messages(_, m):
            import os
            if m.text or m.caption:
                logger.info(f"INSTANCE_LOG [PID:{os.getpid()}]: MsgID:{m.id} | ChatID:{m.chat.id} | Text:{m.text or m.caption}")
            raise StopPropagation # Testing if stopping here prevents the double response (unlikely but worth a check)
        
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
