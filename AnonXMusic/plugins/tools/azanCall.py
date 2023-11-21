from pyrogram import Client, filters
from pyrogram.types import Message
from AnonXMusic import app
from datetime import datetime
import requests
from strings.filters import command
from pytz import timezone
from AnonXMusic.core.call import Anony
from pytgcalls import PyTgCalls, StreamType
from pytgcalls.types.input_stream import AudioPiped, AudioVideoPiped
from AnonXMusic.utils.database import *
from pytgcalls.exceptions import NoActiveGroupCall, TelegramServerError, AlreadyJoinedError
from sqlite3 import connect, OperationalError
from asyncio import create_task, sleep


# Change it to what you want
_timezone = timezone('Asia/Baghdad')

db = connect("adhan.db")
cursor = db.cursor()


def write(table, columns, data):
    try: cursor.execute(f"INSERT INTO {table}{columns} VALUES{data}")
    except OperationalError:
        create(table, "(chat_id INTEGER)")
        cursor.execute(f"INSERT INTO {table}{columns} VALUES{data}")
    db.commit()


def create(table, columns):
    cursor.execute(f"CREATE TABLE {table}{columns}")


def read(table, columns):
    try:data = cursor.execute(f"SELECT {columns} FROM {table}")
    except OperationalError as e:
        create(table, "(chat_id INTEGER)")
        data = cursor.execute(f"SELECT {columns} FROM {table}")
    db.commit()
    return data


def delete(table, column, data):
    try:cursor.execute(f"DELETE FROM {table} WHERE {column} = {data}")
    except OperationalError:pass


@app.on_message(command(["تفعيل اذان"]) & ~filters.private)
async def adhanActivition(_: Client, message: Message):
    chat_id = message.chat.id
    data = list(read("azan", "chat_id"))
    if not len(data) or (chat_id,) not in data:
        write("azan", "(chat_id)", f"({chat_id})")
        await message.reply("تم تفعيل الأذان 💙.", reply_to_message_id=message.id)
    else: await message.reply("الأذن مفعل هنا من قبل 💙.")


@app.on_message(command(["تعطيل اذان"]) & ~filters.private)
async def adhanDeactivate(_: Client, message: Message):
    chat_id = message.chat.id
    data = list(read("azan", "chat_id"))
    if not len(data) or (chat_id,) not in data:
        await message.reply("الأذان غير مفعل بالفعل 💔.", reply_to_message_id=message.id)
    else:
        delete("azan", "chat_id", chat_id)
        await message.reply("تم إلغاء تفعيل الأذان 💔،")


async def calls_stop():
    enabled = list(read("azan", "chat_id"))
    for chat_id in enabled:
        await Anony.force_stop_stream(chat_id[0])


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

def prayers():
    method: int = 7
    params = {
        "address" : "baghdad",
        "method" : method, 
        "school" : 0
    }
    res = requests.get("http://api.aladhan.com/timingsByAddress", params=params)
    data = res.json()
    timings = data["data"]["timings"]
    del timings["Sunrise"]; del timings["Sunset"]; del timings["Imsak"]; del timings["Midnight"]; del timings["Firstthird"]; del timings["Lastthird"]
    return timings

async def adhan():
    while True:
        current_time = datetime.now(_timezone).strftime("%H:%M")
        prayers_time = prayers()
        current_time = "05:14"
        if current_time in list(prayers_time.values()):
            pname = pnames[
                list(prayers_time.items())[list(prayers_time.values()).index(current_time)][0]
            ]
        else:
            await sleep(5)
            continue
        await call_stop()
        enabled = list(read("azan", "chat_id"))
        for chat_id in enabled:
            await app.send_message(chat_id[0], f"حان الآن وقت أذان {pname} ❤️\nجارٍ تشغيل الأذان...")
            await play(chat_id[0])
        await sleep(175)
        
create_task(adhan())
