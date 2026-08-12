# DevuxMitsu - The Love Hashira Music Bot
# Premium Telegram Music Streaming Engine
# Inspired by Mitsuri Kanroji 🌸🌺


from pyrogram import filters, types

from anony import app, db, lang
from anony.helpers import utils
from anony.helpers._admins import owner_only, sudo_only


@app.on_message(filters.command(["addsudo", "delsudo", "rmsudo"]))
@lang.language()
@owner_only
async def _sudo(_, m: types.Message):
    user = await utils.extract_user(m)
    if not user:
        return await m.reply_text(m.lang["user_not_found"])

    if m.command[0] == "addsudo":
        if user.id in app.sudoers:
            return await m.reply_text(m.lang["sudo_already"].format(user.mention))

        app.sudoers.add(user.id)
        await db.add_sudo(user.id)
        await m.reply_text(m.lang["sudo_added"].format(user.mention))
    else:
        if user.id not in app.sudoers:
            return await m.reply_text(m.lang["sudo_not"].format(user.mention))

        app.sudoers.discard(user.id)
        await db.del_sudo(user.id)
        await m.reply_text(m.lang["sudo_removed"].format(user.mention))


o_mention = None

@app.on_message(filters.command(["listsudo", "sudolist"]))
@lang.language()
@sudo_only
async def _listsudo(_, m: types.Message):
    global o_mention
    sent = await m.reply_text(m.lang["sudo_fetching"])

    if not o_mention:
        o_mention = (await app.get_users(app.owner)).mention
    txt = m.lang["sudo_owner"].format(o_mention)
    sudoers = await db.get_sudoers()
    if sudoers:
        txt += m.lang["sudo_users"]

    for user_id in sudoers:
        try:
            user = (await app.get_users(user_id)).mention
            txt += f"\n- {user}"
        except Exception:
            continue

    await sent.edit_text(txt)


@app.on_message(filters.command("sudo") & filters.private & ~app.bl_users)
@lang.language()
async def sudo_panel_hndlr(_, m: types.Message):
    if m.from_user.id not in app.sudoers:
        return await m.reply_text(m.lang["user_no_perms"])
    
    # We'll reuse the help_markup with sudo category to mimic a panel
    from anony.helpers._inline import Inline
    btn = Inline().help_markup(m.lang, m.from_user.id)
    
    await m.reply_text(
        m.lang["sudo_panel"].format(m.from_user.mention),
        reply_markup=buttons.sudo_panel(m.lang)
    )


@app.on_callback_query(filters.regex(r"^sudo_") & ~app.bl_users)
@lang.language()
async def sudo_cb_hndlr(_, query: types.CallbackQuery):
    if query.from_user.id not in app.sudoers:
        return await query.answer(query.lang["user_no_perms"], show_alert=True)

    data = query.data.split("_")[1]
    
    if data == "close":
        return await query.message.delete()
    
    if data == "back":
        return await query.edit_message_text(
            query.lang["sudo_panel"].format(query.from_user.mention),
            reply_markup=buttons.sudo_panel(query.lang)
        )

    if data == "maint":
        current = await db.is_maintenance()
        await db.set_maintenance(not current)
        status = query.lang["sudo_maint_off"] if current else query.lang["sudo_maint_on"]
        return await query.answer(status, show_alert=True)

    if data == "stats":
        from anony.plugins.stats import _stats
        # We need to adapt the stats call or just trigger the stats logic
        # For simplicity, let's redirect to the stats command logic
        await query.answer()
        return await _stats(_, query.message)

    if data == "clean":
        # Bulk delete bot messages in current chat
        async for message in app.get_chat_history(query.message.chat.id, limit=50):
            if message.from_user and message.from_user.id == app.id:
                try: await message.delete()
                except: pass
        return await query.answer(query.lang["sudo_clean_success"], show_alert=True)

    if data == "vc":
        return await query.edit_message_text(
            query.lang["sudo_vc_control"],
            reply_markup=buttons.sudo_vc_panel(query.lang)
        )

    if data == "leave":
        chats = await db.get_chats()
        count = 0
        for chat_id in chats:
            if chat_id not in db.active_calls:
                try:
                    await app.leave_chat(chat_id)
                    count += 1
                except: pass
        return await query.answer(query.lang["sudo_leave_confirm"].format(count), show_alert=True)

    # For complex actions like Broadcast, GBan, Force Play, Manage Sudos
    # We'll send a prompt and wait for input (simplified here)
    if data in ["broadcast", "gban", "fplay", "manage"]:
        await query.answer("Feature coming in next update! 🌸", show_alert=True)
        return
