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
import os
import shutil
import tempfile
from datetime import timedelta
from typing import List

import anilist
from httpx import TimeoutException
from jikanpy import AioJikan
from pyrogram import filters
from pyrogram.errors import BadRequest, QueryIdInvalid
from pyrogram.types import (
    Document,
    InlineQuery,
    InlineQueryResultPhoto,
    InputMediaPhoto,
    Message,
    Video,
)

from korone.handlers import COMMANDS_HELP
from korone.handlers.utils.image import pokemon_image_sync
from korone.handlers.utils.misc import cleanhtml
from korone.korone import Korone
from korone.utils import http

GROUP = "animes"

COMMANDS_HELP[GROUP] = {
    "name": "Animes",
    "text": "O módulo dos Otakus!",
    "commands": {},
    "help": True,
}


def t(milliseconds: int) -> str:
    """
    Inputs time in milliseconds, to get beautified time, as string.

    Arguments:
        `milliseconds`: time in milliseconds.
    """
    seconds, milliseconds = divmod(int(milliseconds), 1000)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    tmp = (
        ((str(days) + " Dias, ") if days else "")
        + ((str(hours) + " Horas, ") if hours else "")
        + ((str(minutes) + " Minutos, ") if minutes else "")
        + ((str(seconds) + " Segundos, ") if seconds else "")
        + ((str(milliseconds) + " ms, ") if milliseconds else "")
    )
    return tmp[:-2]


@Korone.on_message(
    filters.cmd(
        command="anime (?P<search>.+)",
        action="Pesquise informações de animes pelo AniList.",
        group=GROUP,
    )
)
async def anilist_anime(c: Korone, m: Message):
    query = m.matches[0]["search"]

    if query.isdecimal():
        anime_id = int(query)
    else:
        try:
            async with anilist.AsyncClient() as client:
                results = await client.search(query, "anime", 1)
                anime_id = results[0].id
        except IndexError:
            return await m.reply_text(
                "Algo deu errado, verifique sua pesquisa e tente novamente!"
            )

    async with anilist.AsyncClient() as client:
        anime = await client.get(anime_id)

    if not anime:
        return await m.reply_text(
            f"Desculpe! Nenhum <b>anime</b> com o ID <code>{anime_id}</code> foi encontrado..."
        )

    if hasattr(anime, "description"):
        if len(anime.description) > 700:
            desc = f"<b>Descrição curta:</b> <i>{anime.description_short}</i>[...]"
        else:
            desc = f"<b>Descrição:</b> <i>{anime.description}</i>"

    text = f"<b>{anime.title.romaji}</b> (<code>{anime.title.native}</code>)\n"
    text += f"<b>ID:</b> <code>{anime.id}</code>\n"
    text += f"<b>Tipo:</b> <code>{anime.format}</code>\n"
    if hasattr(anime, "status"):
        text += f"<b>Estado:</b> <code>{anime.status}</code>\n"
    if hasattr(anime, "episodes"):
        text += f"<b>Episódios:</b> <code>{anime.episodes}</code>\n"
    if hasattr(anime, "duration"):
        text += f"<b>Duração:</b> <code>{anime.duration}</code> Por Ep.\n"
    if hasattr(anime.score, "average"):
        text += f"<b>Pontuação:</b> <code>{anime.score.average}</code>\n"
    if hasattr(anime, "genres"):
        text += (
            f"<b>Gêneros:</b> <code>{', '.join(str(x) for x in anime.genres)}</code>\n"
        )
    if hasattr(anime, "studios"):
        text += f"<b>Estúdios:</b> <code>{', '.join(str(x) for x in anime.studios)}</code>\n"
    if anime.status.lower() != "not_yet_released":
        text += f"<b>Inicio:</b> <code>{anime.start_date.day if hasattr(anime.start_date, 'day') else 0}/{anime.start_date.month if hasattr(anime.start_date, 'month') else 0}/{anime.start_date.year if hasattr(anime.start_date, 'year') else 0}</code>\n"
    if anime.status.lower() not in ["not_yet_released", "releasing"]:
        text += f"<b>Finalização:</b> <code>{anime.end_date.day if hasattr(anime.end_date, 'day') else 0}/{anime.end_date.month if hasattr(anime.end_date, 'month') else 0}/{anime.end_date.year if hasattr(anime.end_date, 'year') else 0}</code>\n"
    if hasattr(anime, "description"):
        text += f"\n{desc}"

    keyboard = [[("Mais informações", anime.url, "url")]]

    if hasattr(anime, "trailer"):
        keyboard[0].append(("Trailer 🎬", anime.trailer.url, "url"))

    await m.reply_photo(
        photo=f"https://img.anili.st/media/{anime.id}",
        caption=text,
        reply_markup=c.ikb(keyboard),
    )


@Korone.on_message(
    filters.cmd(
        command="airing (?P<search>.+)",
        action="Saiba a próxima transmissão de um anime pelo AniList.",
        group=GROUP,
    )
)
async def anilist_airing(c: Korone, m: Message):
    query = m.matches[0]["search"]

    if query.isdecimal():
        anime_id = int(query)
    else:
        try:
            async with anilist.AsyncClient() as client:
                results = await client.search(query, "anime", 1)
                anime_id = results[0].id
        except IndexError:
            return await m.reply_text(
                "Algo deu errado, verifique sua pesquisa e tente novamente!"
            )

    async with anilist.AsyncClient() as client:
        anime = await client.get(anime_id)

    if not anime:
        return await m.reply_text(
            f"Desculpe! Nenhum <b>anime</b> com o ID <code>{anime_id}</code> foi encontrado..."
        )

    text = f"<b>{anime.title.romaji}</b> (<code>{anime.title.native}</code>)\n"
    text += f"<b>ID:</b> <code>{anime.id}</code>\n"
    text += f"<b>Tipo:</b> <code>{anime.format}</code>\n"
    if hasattr(anime, "next_airing"):
        airing_time = anime.next_airing.time_until * 1000
        text += f"<b>Episódio:</b> <code>{anime.next_airing.episode}</code>\n"
        text += f"<b>Exibição em:</b> <code>{t(airing_time)}</code>"
    else:
        text += f"<b>Episódio:</b> <code>{anime.episodes}</code>\n"
        text += "<b>Exibição em:</b> <code>N/A</code>"

    if hasattr(anime, "banner"):
        await m.reply_photo(photo=anime.banner, caption=text)
    else:
        await m.reply_text(text)


@Korone.on_message(
    filters.cmd(
        command="manga (?P<search>.+)",
        action="Pesquise informações de mangás pelo AniList.",
        group=GROUP,
    )
)
async def anilist_manga(c: Korone, m: Message):
    query = m.matches[0]["search"]

    if query.isdecimal():
        manga_id = int(query)
    else:
        try:
            async with anilist.AsyncClient() as client:
                results = await client.search(query, "manga", 1)
                manga_id = results[0].id
        except IndexError:
            return await m.reply_text(
                "Algo deu errado, verifique sua pesquisa e tente novamente!"
            )

    async with anilist.AsyncClient() as client:
        manga = await client.get(manga_id, "manga")

    if not manga:
        return await m.reply_text(
            f"Desculpe! Nenhum <b>mangá</b> com o ID <code>{manga_id}</code> foi encontrado..."
        )

    if hasattr(manga, "description"):
        if len(manga.description) > 700:
            desc = f"<b>Descrição curta:</b> <i>{manga.description_short}</i>[...]"
        else:
            desc = f"<b>Descrição:</b> <i>{manga.description}</i>"

    text = f"<b>{manga.title.romaji}</b> (<code>{manga.title.native}</code>)\n"
    text += f"<b>ID:</b> <code>{manga.id}</code>\n"
    if hasattr(manga, "status"):
        text += f"<b>Estado:</b> <code>{manga.status}</code>\n"
    if hasattr(manga, "chapters"):
        text += f"<b>Capítulos:</b> <code>{manga.chapters}</code>\n"
    if hasattr(manga, "volumes"):
        text += f"<b>Volumes:</b> <code>{manga.volumes}</code>\n"
    if hasattr(manga.score, "average"):
        text += f"<b>Pontuação:</b> <code>{manga.score.average}</code>\n"
    if hasattr(manga, "genres"):
        text += (
            f"<b>Gêneros:</b> <code>{', '.join(str(x) for x in manga.genres)}</code>\n"
        )
    if not manga.status.lower() == "not_yet_released":
        text += f"<b>Início:</b> <code>{manga.start_date.day if hasattr(manga.start_date, 'day') else 0}/{manga.start_date.month if hasattr(manga.start_date, 'month') else 0}/{manga.start_date.year if hasattr(manga.start_date, 'year') else 0}</code>\n"
    if not manga.status.lower() in ["not_yet_released", "releasing"]:
        text += f"<b>Finalização:</b> <code>{manga.end_date.day if hasattr(manga.end_date, 'day') else 0}/{manga.end_date.month if hasattr(manga.end_date, 'month') else 0}/{manga.end_date.year if hasattr(manga.end_date, 'year') else 0}</code>\n"
    if hasattr(manga, "description"):
        text += f"\n{desc}"

    keyboard = [[("Mais informações", manga.url, "url")]]

    await m.reply_photo(
        photo=f"https://img.anili.st/media/{manga.id}",
        caption=text,
        reply_markup=c.ikb(keyboard),
    )


@Korone.on_message(
    filters.cmd(
        command="character (?P<search>.+)",
        action="Pesquise informações de personagens pelo AniList.",
        group=GROUP,
    )
)
async def anilist_character(c: Korone, m: Message):
    query = m.matches[0]["search"]

    if query.isdecimal():
        character_id = int(query)
    else:
        try:
            async with anilist.AsyncClient() as client:
                results = await client.search(query, "char", 1)
                character_id = results[0].id
        except IndexError:
            return await m.reply_text(
                "Algo deu errado, verifique sua pesquisa e tente novamente!"
            )

    async with anilist.AsyncClient() as client:
        character = await client.get(character_id, "char")

    if not character:
        return await m.reply_text(
            f"Desculpe! Nenhum <b>personagem</b> com o ID <code>{character_id}</code> foi encontrado..."
        )

    if hasattr(character, "description"):
        description = character.description
        description = description.replace("__", "**")
        description = description.replace("~", "~~")

        if len(character.description) > 700:
            description = f"{description[0:500]}[...]"

    text = f"<b>{character.name.full}</b> (<code>{character.name.native}</code>)"
    text += f"\n<b>ID:</b> <code>{character.id}</code>"
    if hasattr(character, "favorites"):
        text += f"\n<b>Favoritos:</b> <code>{character.favorites}</code>"
    if hasattr(character, "description"):
        text += f"\n\n<b>Sobre:</b>\n{html.escape(description)}"

    keyboard = [[("Mais informações", character.url, "url")]]

    if hasattr(character, "image"):
        if hasattr(character.image, "large"):
            photo = character.image.large
        elif hasattr(character.image, "medium"):
            photo = character.image.medium

    if hasattr(character, "image"):
        await m.reply_photo(
            photo=photo,
            caption=text,
            reply_markup=c.ikb(keyboard),
            parse_mode="combined",
        )
    else:
        await m.reply_text(
            text,
            reply_markup=c.ikb(keyboard),
            parse_mode="combined",
        )


@Korone.on_message(
    filters.cmd(
        command="upcoming",
        action="Veja os próximos animes a serem lançados.",
        group=GROUP,
    )
)
async def mal_upcoming(c: Korone, m: Message):
    async with AioJikan() as jikan:
        pass

    upcoming = await jikan.top("anime", page=1, subtype="upcoming")
    await jikan.close()

    upcoming_list = [entry["title"] for entry in upcoming["top"]]
    upcoming_message = "<b>Próximos animes:</b>\n"

    for entry_num in range(len(upcoming_list)):
        if entry_num == 10:
            break
        upcoming_message += f"<b>{entry_num + 1}.</b> {upcoming_list[entry_num]}\n"

    await m.reply_text(upcoming_message)


@Korone.on_message(
    filters.cmd(
        command="(?P<type>.*)pokemon (?P<search>.+)",
        action="Retorna o sprite do Pokémon específico, coloque 'back' antes de 'pokemon' para ver na visão traseira.",
        group=GROUP,
    )
)
async def poke_image(c: Korone, m: Message):
    type = m.matches[0]["type"]
    text = m.matches[0]["search"]
    args = text.split()

    types: List[str] = ["back", "front"]

    type = (type if type in types else "front") + "_"
    type += "_".join(args[1:]) if len(args) > 1 else "default"
    r = await http.get("https://pokeapi.co/api/v2/pokemon/" + args[0])
    if r.status_code == 200:
        sprites = (r.json())["sprites"]
        if type in sprites:
            sprite_url = sprites[type]
        else:
            await m.reply_text(
                f"<code>Error! Tipo \"{' '.join(args[1:])}\" não encontrado!</code>"
            )
            return
    else:
        await m.reply_text(f"<b>Error!</b> <code>{r.status_code}</code>")
        return

    if not sprite_url:
        await m.reply_text("Esse Pokémon não tem um sprite disponível!")
        return

    r = await http.get(sprite_url)
    if r.status_code == 200:
        sprite_io = r.read()
    else:
        await m.reply_text(f"<b>Error!</b> <code>{r.status_code}</code>")
        return

    pk_img = await pokemon_image_sync(sprite_io)
    await m.reply_document(pk_img)


@Korone.on_message(
    filters.cmd(
        command="pokeitem (?P<search>.+)",
        action="Retorna o sprite de um item Pokémon específico.",
        group=GROUP,
    )
)
async def poke_item_image(c: Korone, m: Message):
    text = m.matches[0]["search"]
    args = text.split()

    r = await http.get("https://pokeapi.co/api/v2/item/" + args[0])
    if r.status_code == 200:
        sprites = (r.json())["sprites"]
        sprite_url = sprites["default"]
    else:
        await m.reply_text(f"<b>Error!</b> <code>{r.status_code}</code>")
        return

    if not sprite_url:
        await m.reply_text("Esse item Pokémon não tem um sprite disponível!")
        return

    r = await http.get(sprite_url)
    if r.status_code == 200:
        sprite_io = r.read()
    else:
        await m.reply_text(f"<b>Error!</b> <code>{r.status_code}</code>")
        return

    pk_img = await pokemon_image_sync(sprite_io)
    await m.reply_document(pk_img)


@Korone.on_message(
    filters.cmd(
        command="pokedex (?P<search>.+)",
        action="Obtenha informações sobre Pokémons."))
async def pokedex_cmd(c: Korone, m: Message):
    pokemon = m.matches[0]["search"]
    pokedex = f"https://some-random-api.ml/pokedex?pokemon={pokemon}"
    r = await http.get(pokedex)
    if r.status_code == 404:
        await m.reply_text(f"Não foi possível encontrar o Pokémon <code>{pokemon}</code>.")
        return

    poke = r.json()
    text = f"<b>Pokémon:</b> <code>{poke['name']}</code>\n"
    text += f"<b>Pokedex:</b> <code>{poke['id']}</code>\n"
    text += f"<b>Tipo:</b> <code>{', '.join(str(x) for x in poke['type'])}</code>\n"
    text += f"<b>Abilidades:</b> <code>{', '.join(str(x) for x in poke['abilities'])}</code>\n"
    text += f"<b>Altura:</b> <code>{poke['height']}</code>\n"
    text += f"<b>Peso:</b> <code>{poke['weight']}</code>\n"
    text += f"<b>Gênero:</b> <code>{', '.join(str(x) for x in poke['gender'])}</code>\n"
    text += f"<b>Estatísticas:</b> {', '.join([f'{key}: {value}' for key, value in poke['stats'].items()])}\n"
    text += f"\n<b>Descrição:</b> <i>{poke['description']}</i>"

    poke_img = f"https://img.pokemondb.net/artwork/large/{pokemon}.jpg"
    p = await http.get(poke_img)
    sprite = p.status_code != "404"
    if sprite:
        await m.reply_photo(photo=poke_img, caption=text)
    else:
        await m.reply_text(text)


@Korone.on_message(
    filters.cmd(
        command="whatanime",
        action="Pesquisa reversa de animes através de mídias.",
        group=GROUP,
    )
    & filters.reply
)
async def whatanime(c: Korone, m: Message):
    if not m.reply_to_message.media:
        await m.reply_text("Nenhuma mídia encontrada!")
        return

    media = (
        m.reply_to_message.photo
        or m.reply_to_message.sticker
        or m.reply_to_message.animation
        or m.reply_to_message.video
        or m.reply_to_message.document
    )

    if isinstance(media, (Document, Video)):
        if bool(media.thumbs) and len(media.thumbs) > 0:
            media = media.thumbs[0]

        elif (
            isinstance(media, Video)
            and bool(media.duration)
            and ((media.duration) > (1 * 60 + 30))
        ):
            return

    sent = await m.reply_photo(
        "https://telegra.ph/file/4b479327f02d097a23344.png",
        caption="Procurando informações no AniList...",
    )

    tempdir = tempfile.mkdtemp()
    path = await c.download_media(media, file_name=os.path.join(tempdir, "whatanime"))

    try:
        r = await http.post(
            "https://api.trace.moe/search?anilistInfo&cutBorders",
            files={"image": open(path, "rb")},
        )
    except TimeoutException:
        shutil.rmtree(tempdir)
        await sent.edit("A pesquisa excedeu o tempo limite...")
        return

    shutil.rmtree(tempdir)

    if not r.status_code == 200:
        await sent.edit(
            f"<b>Error:</b> <code>{r.status_code}</code>! Tente novamente mais tarde."
        )
        return

    results = r.json()["result"]
    if len(results) == 0:
        await sent.edit("Nenhum resultado foi encontrado!")
        return

    result = results[0]
    anilist_id = result["anilist"]["id"]
    title_native = result["anilist"]["title"]["native"]
    title_romaji = result["anilist"]["title"]["romaji"]
    is_adult = result["anilist"]["isAdult"]
    synonyms = result["anilist"]["synonyms"]
    episode = result["episode"]

    text = f"<b>{title_romaji}</b>"
    if bool(title_native):
        text += f" (<code>{title_native}</code>)"
    text += "\n"
    text += f"<b>ID:</b> <code>{anilist_id}</code>\n"
    if bool(episode):
        text += f"\n<b>Episódio:</b> <code>{episode}</code>"
    if bool(synonyms):
        text += f"\n<b>Sinônimos:</b> {', '.join(str(x) for x in synonyms)}"
    if bool(is_adult):
        text += "\n<b>Adulto:</b> <code>Sim</code>"
    percent = round(result["similarity"] * 100, 2)
    text += f"\n<b>Similaridade:</b> <code>{percent}%</code>"

    keyboard = [[("Mais informações", f"https://anilist.co/anime/{anilist_id}", "url")]]

    await sent.edit_media(
        InputMediaPhoto(
            f"https://img.anili.st/media/{anilist_id}",
            text,
        ),
        reply_markup=c.ikb(keyboard),
    )

    video = result["video"]
    from_time = str(timedelta(seconds=result["from"])).split(".", 1)[0].rjust(8, "0")
    to_time = str(timedelta(seconds=result["to"])).split(".", 1)[0].rjust(8, "0")
    file_name = result["filename"]

    if video is not None:
        try:
            await c.send_video(
                chat_id=m.chat.id,
                video=video + "&size=l",
                width=1280,
                height=720,
                caption=(
                    f"<code>{file_name}</code>\n\n"
                    f"<code>{from_time}</code> - <code>{to_time}</code>"
                ),
                reply_to_message_id=m.message_id,
            )
        except BadRequest:
            return


@Korone.on_inline_query(filters.regex(r"^anime (?P<query>.+)"), group=-1)
async def inline_anime(c: Korone, q: InlineQuery):
    results: List[InlineQueryResultPhoto] = []
    query = q.query.split()
    if len(query) != 0 and query[0] == "anime":
        search = " ".join(query[1:])
        async with anilist.AsyncClient() as client:
            results_search = await client.search(search, "anime", 10)
            for result in results_search:
                anime = await client.get(result.id, "anime")

                if hasattr(anime, "description"):
                    if len(anime.description) > 700:
                        desc = f"<b>Descrição curta:</b> <i>{anime.description_short}</i>[...]"
                    else:
                        desc = f"<b>Descrição:</b> <i>{anime.description}</i>"

                text = (
                    f"<b>{anime.title.romaji}</b> (<code>{anime.title.native}</code>)\n"
                )
                text += f"<b>ID:</b> <code>{anime.id}</code>\n"
                text += f"<b>Tipo:</b> <code>{anime.format}</code>\n"
                if hasattr(anime, "status"):
                    text += f"<b>Estado:</b> <code>{anime.status}</code>\n"
                if hasattr(anime, "episodes"):
                    text += f"<b>Episódios:</b> <code>{anime.episodes}</code>\n"
                if hasattr(anime, "duration"):
                    text += f"<b>Duração:</b> <code>{anime.duration}</code> Por Ep.\n"
                if hasattr(anime.score, "average"):
                    text += f"<b>Pontuação:</b> <code>{anime.score.average}</code>\n"
                if hasattr(anime, "genres"):
                    text += f"<b>Gêneros:</b> <code>{', '.join(str(x) for x in anime.genres)}</code>\n"
                if hasattr(anime, "studios"):
                    text += f"<b>Estúdios:</b> <code>{', '.join(str(x) for x in anime.studios)}</code>\n"
                if not anime.status.lower() == "not_yet_released":
                    text += f"<b>Inicio:</b> <code>{anime.start_date.day if hasattr(anime.start_date, 'day') else 0}/{anime.start_date.month if hasattr(anime.start_date, 'month') else 0}/{anime.start_date.year if hasattr(anime.start_date, 'year') else 0}</code>\n"
                if not anime.status.lower() in ["not_yet_released", "releasing"]:
                    text += f"<b>Finalização:</b> <code>{anime.end_date.day if hasattr(anime.end_date, 'day') else 0}/{anime.end_date.month if hasattr(anime.end_date, 'month') else 0}/{anime.end_date.year if hasattr(anime.end_date, 'year') else 0}</code>\n"
                if hasattr(anime, "description"):
                    text += f"\n{desc}"

                keyboard = [[("Mais informações", anime.url, "url")]]

                if hasattr(anime, "trailer"):
                    keyboard[0].append(("Trailer 🎬", anime.trailer.url, "url"))

                keyboard.append(
                    [("Pesquisar mais", "anime", "switch_inline_query_current_chat")]
                )

                title = f"{anime.title.romaji} | {anime.format}"
                photo = f"https://img.anili.st/media/{anime.id}"

                results.append(
                    InlineQueryResultPhoto(
                        photo_url=photo,
                        title=title,
                        description=cleanhtml(desc),
                        caption=text,
                        reply_markup=c.ikb(keyboard),
                    )
                )

        try:
            if len(results) > 0:
                await q.answer(
                    results=results,
                    cache_time=0,
                )
        except QueryIdInvalid:
            pass


@Korone.on_inline_query(filters.regex(r"^manga (?P<query>.+)"), group=-1)
async def inline_manga(c: Korone, q: InlineQuery):
    results: List[InlineQueryResultPhoto] = []
    query = q.query.split()
    if len(query) != 0 and query[0] == "manga":
        search = " ".join(query[1:])
        async with anilist.AsyncClient() as client:
            results_search = await client.search(search, "manga", 10)
            for result in results_search:
                manga = await client.get(result.id, "manga")

                if hasattr(manga, "description"):
                    if len(manga.description) > 700:
                        desc = f"<b>Descrição curta:</b> <i>{manga.description_short}</i>[...]"
                    else:
                        desc = f"<b>Descrição:</b> <i>{manga.description}</i>"

                text = (
                    f"<b>{manga.title.romaji}</b> (<code>{manga.title.native}</code>)\n"
                )
                text += f"<b>ID:</b> <code>{manga.id}</code>\n"
                if hasattr(manga, "status"):
                    text += f"<b>Estado:</b> <code>{manga.status}</code>\n"
                if hasattr(manga, "chapters"):
                    text += f"<b>Capítulos:</b> <code>{manga.chapters}</code>\n"
                if hasattr(manga, "volumes"):
                    text += f"<b>Volumes:</b> <code>{manga.volumes}</code>\n"
                if hasattr(manga.score, "average"):
                    text += f"<b>Pontuação:</b> <code>{manga.score.average}</code>\n"
                if hasattr(manga, "genres"):
                    text += f"<b>Gêneros:</b> <code>{', '.join(str(x) for x in manga.genres)}</code>\n"
                if not manga.status.lower() == "not_yet_released":
                    text += f"<b>Início:</b> <code>{manga.start_date.day if hasattr(manga.start_date, 'day') else 0}/{manga.start_date.month if hasattr(manga.start_date, 'month') else 0}/{manga.start_date.year if hasattr(manga.start_date, 'year') else 0}</code>\n"
                if not manga.status.lower() in ["not_yet_released", "releasing"]:
                    text += f"<b>Finalização:</b> <code>{manga.end_date.day if hasattr(manga.end_date, 'day') else 0}/{manga.end_date.month if hasattr(manga.end_date, 'month') else 0}/{manga.end_date.year if hasattr(manga.end_date, 'year') else 0}</code>\n"
                if hasattr(manga, "description"):
                    text += f"\n{desc}"

                keyboard = [
                    [
                        ("Mais Info", manga.url, "url"),
                        ("Pesquisar mais", "manga", "switch_inline_query_current_chat"),
                    ]
                ]

                photo = f"https://img.anili.st/media/{manga.id}"

                results.append(
                    InlineQueryResultPhoto(
                        photo_url=photo,
                        title=manga.title.romaji,
                        description=cleanhtml(desc),
                        caption=text,
                        reply_markup=c.ikb(keyboard),
                    )
                )

        try:
            if len(results) > 0:
                await q.answer(
                    results=results,
                    cache_time=0,
                )
        except QueryIdInvalid:
            pass
