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

import datetime
import functools
import html
import io
import os
import re
import shutil
import tempfile

import youtube_dl
from bs4 import BeautifulSoup as bs
from httpx._exceptions import TimeoutException
from pyrogram import filters
from pyrogram.errors import BadRequest, ImageProcessFailed
from pyrogram.types import CallbackQuery, Message

from korone.handlers import COMMANDS_HELP
from korone.handlers.utils.image import stickcolorsync
from korone.handlers.utils.misc import duck, escape_definition
from korone.handlers.utils.translator import get_tr_lang, tr
from korone.handlers.utils.ytdl import down_progress, extract_info, up_progress
from korone.korone import Korone
from korone.utils import http, pretty_size

GROUP = "utils"

COMMANDS_HELP[GROUP] = {
    "name": "Utilidades",
    "text": "Este é meu módulo de comandos utilitários.",
    "commands": {},
    "help": True,
}


@Korone.on_message(
    filters.cmd(
        command="pypi (?P<search>.+)",
        action="Pesquisa de módulos no PyPI.",
        group=GROUP,
    )
)
async def pypi(c: Korone, m: Message):
    text = m.matches[0]["search"]
    r = await http.get(f"https://pypi.org/pypi/{text}/json")
    if r.status_code == 200:
        json = r.json()
        pypi_info = escape_definition(json["info"])
        message = (
            "<b>%s</b> Por <i>%s %s</i>\n"
            "Plataforma: <b>%s</b>\n"
            "Versão: <b>%s</b>\n"
            "Licença: <b>%s</b>\n"
            "Resumo: <b>%s</b>\n"
            % (
                pypi_info["name"],
                pypi_info["author"],
                f"&lt;{pypi_info['author_email']}&gt;"
                if pypi_info["author_email"]
                else "",
                pypi_info["platform"] or "Não especificado",
                pypi_info["version"],
                pypi_info["license"] or "Nenhuma",
                pypi_info["summary"],
            )
        )
        keyboard = None
        if pypi_info["home_page"] and pypi_info["home_page"] != "UNKNOWN":
            keyboard = [[("Página inicial do pacote", pypi_info["home_page"], "url")]]
        await m.reply_text(
            message,
            disable_web_page_preview=True,
            reply_markup=c.ikb(keyboard),
        )
    else:
        await m.reply_text(
            f"Não consegui encontrar <b>{text}</b> no PyPi (<b>Error:</b> <code>{r.status_code}</code>)",
            disable_web_page_preview=True,
        )
    return


@Korone.on_message(
    filters.cmd(
        command="duckgo (?P<search>.+)",
        action="Faça uma pesquisa no DuckDuckGo através do korone.",
        group=GROUP,
    )
)
async def duckduckgo(c: Korone, m: Message):
    query = m.matches[0]["search"]
    results = await duck.search(query)

    msg = ""
    for i in range(1, 6):
        try:
            title = results[i].title
            link = results[i].url
            desc = results[i].description
            msg += f"{i}. <a href='{link}'>{html.escape(title)}</a>\n<code>{html.escape(desc)}</code>\n\n"
        except IndexError:
            break

    text = (
        f"<b>Consulta:</b>\n<code>{html.escape(query)}</code>"
        f"\n\n<b>Resultados:</b>\n{msg}"
    )

    await m.reply_text(text, disable_web_page_preview=True)


@Korone.on_message(
    filters.cmd(
        command="cleanup",
        action="Banir contas excluídas do grupo.",
        group=GROUP,
    )
)
async def cleanup(c: Korone, m: Message):
    if m.chat.type == "private":
        await m.reply_text("Este comando é para ser usado em grupos!")
        return

    member = await c.get_chat_member(chat_id=m.chat.id, user_id=m.from_user.id)
    if member.status in ["administrator", "creator"]:
        deleted = []
        sent = await m.reply_text("Iniciando limpeza...")
        async for t in c.iter_chat_members(chat_id=m.chat.id, filter="all"):
            if t.user.is_deleted:
                try:
                    await c.kick_chat_member(m.chat.id, t.user.id)
                    deleted.append(t)
                except BadRequest:
                    pass
        if len(deleted) > 0:
            await sent.edit_text(
                f"Removi todas as {len(deleted)} contas excluídas do grupo!"
            )
        else:
            await sent.edit_text("Não há contas excluídas no grupo!")
    else:
        await m.reply_text("Bakayarou! Você não é um administrador...")


@Korone.on_message(
    filters.cmd(
        command="stickers (?P<search>.+)", action="Pesquise stickers.", group=GROUP
    )
)
async def cb_sticker(c: Korone, m: Message):
    args = m.matches[0]["search"]

    r = await http.get("https://combot.org/telegram/stickers?page=1&q=" + args)
    soup = bs(r.text, "lxml")
    main_div = soup.find("div", {"class": "sticker-packs-list"})
    results = main_div.find_all("a", {"class": "sticker-pack__btn"})
    titles = main_div.find_all("div", "sticker-pack__title")
    if not results:
        await m.reply_text("Nenhum resultado encontrado!")
        return

    text = f"Stickers de <b>{args}</b>:"
    for result, title in zip(results, titles):
        link = result["href"]
        text += f"\n - <a href='{link}'>{title.get_text()}</a>"
    await m.reply_text(text, disable_web_page_preview=True)


@Korone.on_message(
    filters.cmd(
        command="color (?P<hex>.+)",
        action="Obtenha uma cor em sticker através do hex ou nome.",
        group=GROUP,
    )
)
async def stickcolor(c: Korone, m: Message):
    args = m.matches[0]["hex"]
    color_sticker = await stickcolorsync(args)

    if color_sticker:
        await m.reply_sticker(color_sticker)
    else:
        await m.reply_text(
            f"<code>{args}</code> é uma cor inválida, use <code>#hex</code> ou o nome da cor."
        )


@Korone.on_message(
    filters.cmd(
        command=r"ytdl(\s(?P<text>.+))?",
        action="Faça o Korone baixar um vídeo do YouTube e enviar no chat atual.",
        group=GROUP,
    )
)
async def on_ytdl(c: Korone, m: Message):
    args = m.matches[0]["text"]
    user = m.from_user.id

    if m.reply_to_message and m.reply_to_message.text:
        url = m.reply_to_message.text
    elif m.text and args:
        url = args
    else:
        await m.reply_text("Por favor, responda a um link do YouTube ou texto.")
        return

    ydl = youtube_dl.YoutubeDL(
        {"outtmpl": "dls/%(title)s-%(id)s.%(ext)s", "format": "mp4", "noplaylist": True}
    )
    rege = re.match(
        r"http(?:s?):\/\/(?:www\.)?youtu(?:be\.com\/watch\?v=|\.be\/)([\w\-\_]*)(&(amp;)?‌​[\w\?‌​=]*)?",
        url,
        re.M,
    )

    temp = "0"
    if "t=" in url:
        temp = url.split("t=")[1].split("&")[0]
    if not rege:
        yt = await extract_info(ydl, "ytsearch:" + url, download=False)
        yt = yt["entries"][0]
    else:
        yt = await extract_info(ydl, rege.group(), download=False)

    if not temp.isnumeric():
        temp = "0"

    for f in yt["formats"]:
        if f["format_id"] == "140":
            afsize = f["filesize"] or 0
        if f["ext"] == "mp4" and f["filesize"] is not None:
            vfsize = f["filesize"] or 0
            vformat = f["format_id"]

    keyboard = [
        [
            (
                "💿 Áudio",
                f'_aud.{yt["id"]}|{afsize}|{vformat}|{temp}|{m.chat.id}|{user}|{m.message_id}',
            ),
            (
                "🎬 Vídeo",
                f'_vid.{yt["id"]}|{vfsize}|{vformat}|{temp}|{m.chat.id}|{user}|{m.message_id}',
            ),
        ]
    ]

    if " - " in yt["title"]:
        performer, title = yt["title"].rsplit(" - ", 1)
    else:
        performer = yt.get("creator") or yt.get("uploader")
        title = yt["title"]

    text = f"🎧 <b>{performer}</b> - <i>{title}</i>\n"
    text += f"💾 <code>{pretty_size(afsize)}</code> (áudio) / <code>{pretty_size(int(vfsize))}</code> (vídeo)\n"
    text += f"⏳ <code>{datetime.timedelta(seconds=yt.get('duration'))}</code>"

    await m.reply_text(text, reply_markup=c.ikb(keyboard))


@Korone.on_callback_query(filters.regex("^(_(vid|aud))"))
async def cli_ytdl(c, cq: CallbackQuery):
    data, fsize, vformat, temp, cid, userid, mid = cq.data.split("|")
    if not cq.from_user.id == int(userid):
        return await cq.answer("Este botão não é para você!", cache_time=60)
    if int(fsize) > 209715200:
        return await cq.answer(
            (
                "Desculpe! Não posso baixar esta mídia pois ela "
                "ultrapassa o meu limite de 200MB de download."
            ),
            show_alert=True,
            cache_time=60,
        )
    vid = re.sub(r"^\_(vid|aud)\.", "", data)
    url = "https://www.youtube.com/watch?v=" + vid
    await cq.message.edit("Baixando...")
    await cq.answer("Seu pedido é uma ordem... >-<", cache_time=0)
    with tempfile.TemporaryDirectory() as tempdir:
        path = os.path.join(tempdir, "ytdl")
    if "vid" in data:
        ydl = youtube_dl.YoutubeDL(
            {
                "outtmpl": f"{path}/%(title)s-%(id)s.%(ext)s",
                "format": vformat,
                "noplaylist": True,
            }
        )
    else:
        ydl = youtube_dl.YoutubeDL(
            {
                "outtmpl": f"{path}/%(title)s-%(id)s.%(ext)s",
                "format": "140",
                "extractaudio": True,
                "noplaylist": True,
            }
        )
    ydl.add_progress_hook(functools.partial(down_progress, cq.message))
    try:
        yt = await extract_info(ydl, url, download=True)
    except BaseException as e:
        await cq.message.edit(f"<b>Error!</b>\n<code>{e}</code>")
        return
    await cq.message.edit("Enviando...")
    filename = ydl.prepare_filename(yt)
    ttemp = ""
    if int(temp):
        ttemp = f"⏰ {datetime.timedelta(seconds=int(temp))} | "
    thumb = io.BytesIO((await http.get(yt["thumbnail"])).content)
    thumb.name = "thumbnail.png"
    if "vid" in data:
        await c.send_chat_action(int(cid), "upload_video")
        try:
            await c.send_video(
                chat_id=int(cid),
                video=filename,
                width=1920,
                height=1080,
                caption=f"{ttemp} <a href='{yt['webpage_url']}'>{yt['title']}</a></b>",
                duration=yt["duration"],
                thumb=thumb,
                progress=up_progress,
                progress_args=(
                    c,
                    cq.message,
                    "video",
                ),
                reply_to_message_id=int(mid),
            )
        except BadRequest as e:
            await c.send_message(
                chat_id=int(cid),
                text=(
                    "Desculpe! Não consegui enviar o "
                    "vídeo por causa de um erro.\n"
                    f"<b>Erro:</b> <code>{e}</code>"
                ),
                reply_to_message_id=int(mid),
            )
    else:
        if " - " in yt["title"]:
            performer, title = yt["title"].rsplit(" - ", 1)
        else:
            performer = yt.get("creator") or yt.get("uploader")
            title = yt["title"]
        try:
            await c.send_audio(
                chat_id=int(cid),
                audio=filename,
                caption=f"{ttemp} <a href='{yt['webpage_url']}'>{yt['title']}</a></b>",
                title=title,
                performer=performer,
                duration=yt["duration"],
                thumb=thumb,
                progress=up_progress,
                progress_args=(
                    c,
                    cq.message,
                    "audio",
                ),
                reply_to_message_id=int(mid),
            )
        except BadRequest as e:
            await c.send_message(
                chat_id=int(cid),
                text=(
                    "Desculpe! Não consegui enviar o "
                    "vídeo por causa de um erro.\n"
                    f"<b>Erro:</b> <code>{e}</code>"
                ),
                reply_to_message_id=int(mid),
            )
    await cq.message.delete()
    shutil.rmtree(tempdir, ignore_errors=True)


@Korone.on_message(
    filters.cmd(
        command="tr", action="Use o Google Tradutor para traduzir textos.", group=GROUP
    )
)
async def translate(c: Korone, m: Message):
    text = m.text[4:]
    lang = get_tr_lang(text)

    text = text.replace(lang, "", 1).strip() if text.startswith(lang) else text

    if m.reply_to_message and not text:
        text = m.reply_to_message.text or m.reply_to_message.caption

    if not text:
        return await m.reply_text(
            "<b>Uso:</b> <code>/tr &lt;idioma&gt; texto para tradução</code> (Também pode ser usado em resposta a uma mensagem)."
        )

    sent = await m.reply_text("Traduzindo...")
    langs = {}

    if len(lang.split("-")) > 1:
        langs["sourcelang"] = lang.split("-")[0]
        langs["targetlang"] = lang.split("-")[1]
    else:
        langs["targetlang"] = lang

    trres = await tr(text, **langs)
    text = trres.text

    res = html.escape(text)
    await sent.edit_text(
        (
            "<b>Idioma:</b> {from_lang} -> {to_lang}\n<b>Tradução:</b> <code>{translation}</code>"
        ).format(from_lang=trres.lang, to_lang=langs["targetlang"], translation=res)
    )


@Korone.on_message(
    filters.cmd(
        command="mcserver (?P<ip>.+)",
        action="Veja algumas informações de servidores de Minecraft Java Edition.",
        group=GROUP,
    )
)
async def mcserver(c: Korone, m: Message):
    args = m.matches[0]["ip"]
    reply = await m.reply_text("Obtendo informações...")
    try:
        r = await http.get(f"https://api.mcsrvstat.us/2/{args}")
    except TimeoutException:
        await reply.edit("Desculpe, não consegui me conectar a API!")
        return

    if r.status_code in [500, 504, 505]:
        await reply.edit("A API está indisponível ou com instabilidade!")
        return

    a = r.json()
    if a["online"]:
        text = "<b>Minecraft Server:</b>"
        text += f"\n<b>IP:</b> {a['hostname'] if 'hostname' in a else a['ip']} (<code>{a['ip']}</code>)"
        text += f"\n<b>Port:</b> <code>{a['port']}</code>"
        text += f"\n<b>Online:</b> <code>{a['online']}</code>"
        text += f"\n<b>Mods:</b> <code>{len(a['mods']['names']) if 'mods' in a else 'N/A'}</code>"
        text += f"\n<b>Players:</b> <code>{a['players']['online']}/{a['players']['max']}</code>"
        if "list" in a["players"]:
            text += "\n<b>Players list:</b> {}".format(
                (
                    ", ".join(
                        [
                            f"<a href='https://namemc.com/profile/{name}'>{name}</a>"
                            for name in a["players"]["list"]
                        ]
                    )
                ),
            )
        text += f"\n<b>Version:</b> <code>{a['version']}</code>"
        try:
            text += f"\n<b>Software:</b> <code>{a['software']}</code>"
        except KeyError:
            pass
        text += f"\n<b>MOTD:</b> <i>{a['motd']['clean'][0]}</i>"

    elif not a["ip"] or a["ip"] == "127.0.0.1":
        text = "Isso não é um IP/domínio válido!"

    elif not a["online"]:
        text = (
            "<b>Minecraft Server</b>:"
            f"\n<b>IP:</b> {a['hostname'] if 'hostname' in a else a['ip']} (<code>{a['ip']}</code>)"
            f"\n<b>Port:</b> <code>{a['port']}</code>"
            f"\n<b>Online:</b> <code>{a['online']}</code>"
        )
    await reply.edit(text, disable_web_page_preview=True)


@Korone.on_message(
    filters.cmd(
        command="print (?P<url>.+)",
        action="Faça uma captura de tela da url dada.",
        group=GROUP,
    )
)
async def amn_print(c: Korone, m: Message):
    args = m.matches[0]["url"]
    reply = await m.reply_text("Printando...")
    try:
        r = await http.get("https://webshot.amanoteam.com/print", params=dict(q=args))
    except TimeoutException:
        await reply.edit("Desculpe, não consegui concluir seu pedido!")
        return

    if r.status_code in [500, 504, 505]:
        await reply.edit("API indisponível ou instável!")
        return

    bio = io.BytesIO(r.read())
    bio.name = "screenshot.png"
    try:
        await m.reply_photo(bio)
    except ImageProcessFailed:
        await reply.edit("Um erro ocorreu ao tentar processar a imagem!")
        return

    await reply.delete()


@Korone.on_message(
    filters.cmd(
        command="del$",
        action="Faça o Korone apagar uma mensagem.",
        group=GROUP,
    )
)
async def del_message(c: Korone, m: Message):
    if not m.chat.type == "private":
        member = await c.get_chat_member(chat_id=m.chat.id, user_id=m.from_user.id)

    if m.chat.type == "private" or member.status in ["administrator", "creator"]:
        if m.reply_to_message:
            await c.delete_messages(
                chat_id=m.chat.id,
                message_ids=[m.reply_to_message.message_id, m.message_id],
                revoke=True,
            )
    else:
        await m.reply_text("Bakayarou! Você não é um administrador...")
