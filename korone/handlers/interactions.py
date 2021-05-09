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

import random
from typing import Dict

from pyrogram import filters
from pyrogram.errors import ChatWriteForbidden
from pyrogram.types import Message

from korone.handlers import COMMANDS_HELP
from korone.handlers.utils.random import (
    HEY_REACT,
    INSULTS_REACT,
    RANDOM_REACT,
    SHUTUP_REACT,
    WHATSUP_REACT,
)
from korone.korone import Korone

GROUP = "interactions"

COMMANDS_HELP[GROUP]: Dict = {
    "name": "Interações",
    "text": "Use estes filtros em resposta a mim.",
    "filters": {},
    "help": True,
}


async def int_reply(c: Korone, m: Message, text: str = None):
    if m.chat.type == "private":
        await m.reply_text(text)
    elif (
        m.reply_to_message and m.reply_to_message.from_user.id == (await c.get_me()).id
    ):
        await m.reply_text(text)
        return


@Korone.on_message(
    filters.int(filter=r"(Quem te criou|Quem criou voc(ê|e))", group=GROUP)
)
async def my_creator(c: Korone, m: Message):
    await int_reply(c, m, "Meu criador se chama Hitalo ^^")


@Korone.on_message(filters.int(filter=r"(okay|ok)", group=GROUP))
async def okay(c: Korone, m: Message):
    await int_reply(c, m, "Hmm...")


@Korone.on_message(filters.int(filter=r"voc(e|ê) gosta de caf(é|e)", group=GROUP))
async def ulikecoffe(c: Korone, m: Message):
    await int_reply(c, m, f"Com certeza! {emoji.HOT_BEVERAGE}")


@Korone.on_message(filters.int(filter=r"(Ol(á|a)|Oi|Eae|Hi|Hello|Hey)", group=GROUP))
async def hello(c: Korone, m: Message):
    react = random.choice(HEY_REACT)
    await int_reply(c, m, react.format(m.from_user.first_name))


@Korone.on_message(
    filters.int(
        filter=r"(Est(ú|u)pido|Puta|Vai se f(o|u)der|Idiota|Ot(á|a)rio|Lixo)",
        group=GROUP,
    )
)
async def insult(c: Korone, m: Message):
    react = random.choice(INSULTS_REACT)
    await int_reply(c, m, react.format(m.from_user.first_name))


@Korone.on_message(filters.int(filter=r"(como vai|tudo bem)", group=GROUP))
async def all_right(c: Korone, m: Message):
    react = random.choice(WHATSUP_REACT)
    await int_reply(c, m, react)


@Korone.on_message(filters.int(filter=r"(Cala boca|Cala-boca)", group=GROUP))
async def shutup(c: Korone, m: Message):
    react = random.choice(SHUTUP_REACT)
    await int_reply(c, m, react)


@Korone.on_message(~filters.private)
async def random_react(c: Korone, m: Message):
    if m.message_id % 100 != 0:
        m.continue_propagation()
    react = random.choice(RANDOM_REACT)
    if isinstance(react, tuple):
        react = random.choice(react)

    try:
        await m.reply_text(react, quote=False)
    except ChatWriteForbidden:
        await c.leave_chat(chat_id=m.chat.id)
        pass
    m.continue_propagation()
