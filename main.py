from telethon import TelegramClient, events
from telethon.sessions import StringSession
import pytz
import requests
from aiohttp import web
import base64
import os
import json
import argparse
from https_utils import create_ssl_context
import glob

cfg = None
all_dialog_titles = {}
all_users = {}

tz = None
client = None


###############################################################################
# bot
###############################################################################


def send_message(text, media_fn, media_t):
    url_exts = {
        "photo": "Photo",
        "video": "Video",
        "gif": "Animation",
        "sticker": "Sticker"
    }
    url_ext = url_exts.get(media_t, "Message")
    url = "https://api.telegram.org/bot{}/send{}".format(cfg["bot"]["token"], url_ext)
    data = {
        "chat_id": cfg["bot"]["chat_id"]
    }
    files = None
    if url_ext == "Message":
        data["text"] = text
    elif url_ext == "Photo":
        data["caption"] = text
        files = {
            "photo": open(media_fn, "rb")
        }
    elif url_ext == "Video":
        data["caption"] = text
        files = {
            "video": open(media_fn, "rb")
        }
    elif url_ext == "Animation":
        data["caption"] = text
        files = {
            "animation": open(media_fn, "rb")
        }
    elif url_ext == "Sticker":
        # info message for sticker
        message_url = "https://api.telegram.org/bot{}/sendMessage".format(cfg["bot"]["token"])
        try:
            if not requests.post(message_url, data=dict(data, text=text), timeout=cfg["bot"]["timeout"]).json()["ok"]:
                return False
        except:
            return False
        files = {
            "sticker": open(media_fn, "rb")
        }
    try:
        return requests.post(url, data=data, files=files, timeout=cfg["bot"]["timeout"]).json()["ok"] is True
    except:
        return False


###############################################################################
# src
###############################################################################


def get_name(user):
    if user is None:
        return "?"
    res = ""
    if user.first_name:
        res = user.first_name
    if user.last_name:
        if res:
            res += " "
        res += user.last_name
    if not res:
        res = user.username
    return res


async def get_dialogs():
    dialogs = []
    async for d in client.iter_dialogs():
        dialogs.append((d.title, d.id, d.date, d.message.id))
    return dialogs


async def get_users(dialog_id):
    users = []
    async for p in client.iter_participants(dialog_id):
        users.append((get_name(p), p.id))
    users.sort()
    return users


async def download_media(m):
    media_ts = (
        "photo",
        "video",
        "gif",
        "sticker"
    )
    for media_t in media_ts:
        if getattr(m, media_t) is not None:
            media_fn = "{}/{}".format(cfg["server"]["downloads"], m.id)
            media_fns = glob.glob("{}.*".format(media_fn))
            if not media_fns:
                media_fn = await m.download_media(media_fn)
            else:
                media_fn = media_fns[0]
            _, ext = os.path.splitext(media_fn)
            if media_t == "sticker" and ext not in [".webp", ".webm"]:
                return None, None
            return media_fn, media_t
    return None, None


async def get_messages(dialog_id, max_message_id=None):
    args = dict(max_id=max_message_id) if max_message_id else dict()
    messages = []
    async for m in client.iter_messages(dialog_id, limit=cfg["app"]["limit"], wait_time=cfg["app"]["wait_time"], **args):
        text = m.text
        media_fn, media_t = await download_media(m)
        if media_fn is None and m.file is not None:
            text = "<{}> {}".format(m.file.name, text)
        messages.append((m.date, m.id, get_name(m.sender), m.sender_id, text, media_fn, media_t))
    return messages


async def update_all_users(dialog_id):
    me = await client.get_me()
    all_users[me.id] = me
    async for p in client.iter_participants(dialog_id):
        all_users[p.id] = p


async def update_all_dialog_titles():
    async for d in client.iter_dialogs():
        all_dialog_titles[d.id] = d.title


async def event_handler(event):
    m = event.message

    if m is None:
        return

    if m.chat_id == cfg["bot"]["chat_id"]:
        return

    if m.chat:
        chat_title = m.chat.title if m.chat_id < 0 else get_name(m.chat)
    else:
        chat_title = all_dialog_titles.get(m.chat_id)
        if chat_title is None:
            await update_all_dialog_titles()
        chat_title = all_dialog_titles.get(m.chat_id) or "?"

    sender = m.sender
    if sender is None:
        sender = all_users.get(m.sender_id)
        if sender is None:
            await update_all_users(m.chat_id)
        sender = all_users.get(m.sender_id)
    sender_name = get_name(sender)

    prefix = sender_name if m.sender_id == m.chat_id else "{} : {}".format(chat_title, sender_name)

    text = m.text
    media_fn, media_t = await download_media(m)
    if media_fn is None and m.file is not None:
        text = "<{}> {}".format(m.file.name, text)
    data = "{} : {}".format(prefix, text)
    send_message(data, media_fn, media_t)


###############################################################################
# server
###############################################################################


async def index(request):
    return web.FileResponse("static/index.html")


async def me(request):
    me = await client.get_me()

    return web.json_response(dict(my_id=me.id))


async def dialogs(request):
    dialogs = await get_dialogs()

    data = []
    for title, dialog_id, message_t, message_id in dialogs:
        data.append(dict(
            title=title,
            dialog_id=dialog_id,
            message_t=message_t.astimezone(tz).strftime("%d.%m.%y %H:%M:%S")
        ))
    return web.json_response(data)


async def users(request):
    data = await request.json()
    users = await get_users(data["dialog_id"])

    data = []
    for name, user_id in users:
        data.append(dict(
            name=name,
            user_id=user_id
        ))
    return web.json_response(data)


async def messages(request):
    data = await request.json()
    messages = await get_messages(data["dialog_id"], data.get("max_message_id"))

    data = []
    for t, message_id, sender_name, sender_id, text, media_fn, media_t in messages:
        data.append(dict(
            t=t.astimezone(tz).strftime("%d.%m.%y %H:%M:%S"),
            message_id=message_id,
            sender_name=sender_name,
            sender_id=sender_id,
            text=text,
            media_fn=media_fn,
            media_t=media_t
        ))
    return web.json_response({"data": data, "more_data": len(data) == cfg["app"]["limit"]})


@web.middleware
async def basic_auth_middleware(request, handler):
    auth = request.headers.get("Authorization")
    if auth != "Basic " + base64.b64encode("{}:{}".format(cfg["server"]["user"], cfg["server"]["password"]).encode("UTF-8")).decode("UTF-8"):
        return web.Response(status=401, headers={"WWW-Authenticate": 'Basic realm="vxpcsys"'})
    return await handler(request)


async def server_init():
    app = web.Application(
        middlewares=[basic_auth_middleware]
    )
    app.add_routes([
        web.get("/", index),
        web.static("/static", "static"),
        web.static("/downloads", cfg["server"]["downloads"]),
        web.post("/me", me),
        web.post("/dialogs", dialogs),
        web.post("/users", users),
        web.post("/messages", messages)
    ])
    runner = web.AppRunner(app)
    await runner.setup()
    ssl_context = create_ssl_context(cfg["server"]["crt"], cfg["server"]["key"], cfg["server"]["hostname"])
    site = web.TCPSite(runner, cfg["server"]["addr"], cfg["server"]["port"], ssl_context=ssl_context)
    await site.start()


###############################################################################


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--cfg", default="cfg.json")
    args = parser.parse_args()

    if not os.path.exists(args.cfg):
        raise RuntimeError("can not find {}".format(args.cfg))

    with open(args.cfg) as f:
        cfg = json.loads(f.read())

    if not os.path.exists(cfg["server"]["downloads"]):
        os.makedirs(cfg["server"]["downloads"])

    tz = pytz.timezone(cfg["tz"])

    client = TelegramClient(
        StringSession(cfg["app"]["string_session"]),
        cfg["app"]["api_id"], cfg["app"]["api_hash"],
        device_model="Notepad 2", system_version="Android OS"
    )
    client.add_event_handler(event_handler, events.NewMessage)
    with client:
        if not cfg["app"]["string_session"]:
            print(client.session.save())
        else:
            client.loop.run_until_complete(server_init())
            client.run_until_disconnected()
