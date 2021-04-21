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

import os

from tortoise import Tortoise, fields
from tortoise.models import Model


class Chats(Model):
    id = fields.IntField(pk=True)
    title = fields.TextField()


class Banneds(Model):
    id = fields.IntField(pk=True)
    name = fields.TextField()


async def connect_database():
    await Tortoise.init(
        {
            "connections": {
                "korone_db": os.getenv(
                    "DATABASE_URL", "sqlite://korone/database/database.sqlite"
                )
            },
            "apps": {
                "korone": {"models": [__name__], "default_connection": "korone_db"}
            },
        }
    )
    # Generate the schema
    await Tortoise.generate_schemas()
