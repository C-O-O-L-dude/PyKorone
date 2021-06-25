# This file is part of Korone (Telegram Bot)
# Copyright (C) 2021 AmanoTeam

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import html
import json
from typing import Dict

from pyrogram import filters
from pyrogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from korone.database import Levels, Rank_not, Users, XPs
from korone.handlers import COMMANDS_HELP
from korone.korone import Korone

GROUP = "ranking"

COMMANDS_HELP[GROUP]: Dict = {
    "name": "Ranking",
    "text": "Comando relacionado ao meu sistema de ranks, níveis e XPs.",
    "commands": {},
    "help": True,
}


LEVELS_GROUP: Dict = {}
with open("korone/levels_group.json", "r") as file:
    LEVELS_GROUP = json.loads(file.read())
    file.close()


LEVELS_GLOBAL: Dict = {}
with open("korone/levels_global.json", "r") as file:
    LEVELS_GLOBAL = json.loads(file.read())
    file.close()


@Korone.on_message(
    filters.cmd(
        command=r"ranking$", action="Ranking de usuários do grupo.", group=GROUP
    )
    & filters.group
)
async def ranking(c: Korone, m: Message):
    user_levels = sorted(
        await Levels.filter(chat_id=m.chat.id),
        key=lambda level: level.value,
        reverse=True,
    )

    text = f"Ranking de níveis de <b>{html.escape(m.chat.title)}</b>:"

    for index, level in enumerate(user_levels):
        if (index + 1) >= 21:
            break

        first_name = (await Users.get(id=level.user_id)).first_name

        current_xp = (await XPs.get(chat_id=m.chat.id, user_id=level.user_id)).value
        current_level = level.value
        next_level = current_level + 1
        next_level_xp = (
            LEVELS_GROUP[str(next_level)]
            if str(next_level) in LEVELS_GROUP.keys()
            else 0
        )

        text += f"\n    <i>#{index + 1}</i> {html.escape(first_name)} <b>{current_level}</b> (<code>{current_xp}</code>/<code>{next_level_xp}</code>)"

    await m.reply_text(text)


@Korone.on_message(
    filters.cmd(
        command=r"ranking global$", action="Ranking de usuários global.", group=GROUP
    )
)
async def ranking_global(c: Korone, m: Message):
    users = sorted(await Users.all(), key=lambda user: user.level, reverse=True)

    text = f"Ranking de níveis <b>global</b>:"

    for index, user in enumerate(users):
        if (index + 1) >= 21:
            break

        first_name = user.first_name

        current_xp = user.xp
        current_level = user.level
        next_level = current_level + 1
        next_level_xp = (
            LEVELS_GLOBAL[str(next_level)]
            if str(next_level) in LEVELS_GLOBAL.keys()
            else 0
        )

        text += f"\n    <i>#{index + 1}</i> {html.escape(first_name)} <b>{current_level}</b> (<code>{current_xp}</code>/<code>{next_level_xp}</code>)"

    await m.reply_text(text)


@Korone.on_message(
    filters.cmd(
        command=r"ranking notify$",
        action="Desativar/Ativar aviso de level up.",
        group=GROUP,
    )
    & filters.group
)
async def ranking_notify(c: Korone, m: Message):
    config = await Rank_not.get_or_none(chat_id=m.chat.id)
    keyboard = [
        [("✅ Ativado" if config.value == "True" else "☑️ Desativado", "rank_togle")]
    ]
    await m.reply_text("Notificações de level up.", reply_markup=c.ikb(keyboard))


@Korone.on_callback_query(filters.regex("^rank_togle"))
async def rank_togle(c: Korone, cq: CallbackQuery):
    member = await c.get_chat_member(
        chat_id=cq.message.chat.id, user_id=cq.from_user.id
    )
    if member.status not in ["administrator", "creator"]:
        return await cq.answer("Este botão não é para você!", cache_time=60)
    config = await Rank_not.get_or_none(chat_id=cq.message.chat.id)
    if config.value == "True":
        config.update_from_dict({"value": False})
        await config.save()
    elif config.value == "False":
        config.update_from_dict({"value": True})
        await config.save()

    keyboard = [
        [("✅ Ativado" if config.value == "True" else "☑️ Desativado", "rank_togle")]
    ]
    await cq.message.edit_text(
        "Notificações de level up.", reply_markup=c.ikb(keyboard)
    )
