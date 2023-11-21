from pyrogram import Client, filters
from pyrogram.types import Message
from AnonXMusic import app
from datetime import datetime
import requests
from pytz import timezone
from AnonXMusic.core.call import Anony
from pytgcalls import PyTgCalls, StreamType
from pytgcalls.types.input_stream import AudioPiped, AudioVideoPiped
from AnonXMusic.utils.database import *
from pytgcalls.exceptions import NoActiveGroupCall, TelegramServerError, AlreadyJoinedError
from sqlite3 import connect, OperationalError
from asyncio import create_task, sleep
from AnonXMusic.core.mongo import mongodb


db = mongodb["azan"]

async def add(chat_id, timezone):
    document = {"chat_id": chat_id, "timezone": timezone}
    await db.insert_one(document)

async def delete(chat_id):
    query = {"chat_id": chat_id}
    await db.delete_one(query)

async def exists(chat_id):
    query = {"chat_id": chat_id}
    return await db.count_documents(query) > 0

async def get_timezone(chat_id):
    query = {"chat_id": chat_id}
    document = await db.find_one(query)
    return document["timezone"]


async def get_all():
    query = {}
    documents = await db.find(query)

    chat_ids = []
    for document in documents:
        chat_ids.append(document["chat_id"])

    return chat_ids


# Change it to what you want
#_timezone = timezone('Asia/Baghdad')

@app.on_message(filters.command("تفعيل الاذان", "") & ~filters.private)
async def adhanActivition(_: Client, message: Message):
    chat_id = message.chat.id
    if not exists(chat_id):
        await add(chat_id, "Africa/Cairo")
        create_task(adhan(chat_id, "Africa/Cairo"))
        await message.reply("تم تفعيل الأذان 💙.", reply_to_message_id=message.id)
    else: await message.reply("الأذن مفعل هنا من قبل 💙.")


@app.on_message(filters.command("تعطيل الاذان", "") & ~filters.private)
async def adhanDeactivate(_: Client, message: Message):
    chat_id = message.chat.id
    if not exists(chat_id):
        await message.reply("الأذان غير مفعل بالفعل 💔.", reply_to_message_id=message.id)
    else:
        await delete(chat_id)
        await message.reply("تم إلغاء تفعيل الأذان 💔،")


async def calls_stop(chat_id):
    await Anony.force_stop_stream(chat_id)


async def play(chat_id):
    assistant = await group_assistant(Anony, chat_id)
    audio = "./AnonXMusic/assets/azan.m4a"
    stream = AudioPiped(audio)
    try:await assistant.join_group_call(
            chat_id,
            stream,
            stream_type=StreamType().pulse_stream,
        )
    except NoActiveGroupCall:
        try:
            await Anony.join_assistant(chat_id, chat_id)
        except Exception as e:
            await app.send_message(chat_id, f"خطأ: {e}")
    except TelegramServerError:
        await app.send_message(chat_id, "عذرًا، هناك مشكلات في سيرفر التليجرام")
    except AlreadyJoinedError:
        await stop_azan()
        try:
            await assistant.join_group_call(
                chat_id,
                stream,
                stream_type=StreamType().pulse_stream,
            )
        except Exception as e:
            await app.send_message(chat_id, f"خطأ: {e}")


pnames: dict = {
    'Fajr': "الفجر", 
    'Sunrise': "الشروق", 
    'Dhuhr': "الظهر", 
    'Asr': "العصر",
    'Maghrib': "المغرب", 
    'Isha': "العشاء", 
}

def prayers(city):
    method: int = 1
    params = {
        "address" : city,
        "method" : method, 
        "school" : 0
    }
    res = requests.get("http://api.aladhan.com/timingsByAddress", params=params)
    data = res.json()
    timings = data["data"]["timings"]
    del timings["Sunrise"]; del timings["Sunset"]; del timings["Imsak"]; del timings["Midnight"]; del timings["Firstthird"]; del timings["Lastthird"]
    return timings


async def adhan(chat_id, _timezone):
    while True:
        await exists(chat_id)
        current_time = datetime.now(timezone(_timezone)).strftime("%H:%M")
        prayers_time = prayers(_timezone.split("/")[1].lower())
        current_time = "05:02"
        if current_time in list(prayers_time.values()):
            pname = pnames[
                list(prayers_time.items())[list(prayers_time.values()).index(current_time)][0]
            ]
        else:
            await sleep(5)
            continue
        await calls_stop(chat_id)
        await app.send_message(chat_id, f"حان الآن وقت أذان {pname} ❤️\nجارٍ تشغيل الأذان...")
        await play(chat_id)
        await sleep(175)
        
