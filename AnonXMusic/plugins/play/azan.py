
import asyncio
from pyrogram import filters
from pyrogram.errors import FloodWait
from pyrogram.raw import types
from AnonXMusic import app
from datetime import datetime
import requests
import pytz
from AnonXMusic.core.call import Anony
from pytgcalls import PyTgCalls, StreamType
from pytgcalls.types.input_stream import AudioPiped, AudioVideoPiped
from AnonXMusic.utils.database import *
from pytgcalls.exceptions import NoActiveGroupCall, TelegramServerError, AlreadyJoinedError
from pyrogram.errors import ChatAdminRequired, UserAlreadyParticipant, UserNotParticipant


cairo_timezone = pytz.timezone('Africa/Cairo')


azan_enabled_chats = []

@app.on_message(filters.text & ~filters.private, group=20)
async def handle_azan_command(c, msg):
    chat_id = msg.chat.id
    if msg.text == "تفعيل الاذان":
        if chat_id in azan_enabled_chats:
            await msg.reply_text("الأذان مفعل بالفعل في هذه المجموعة")
        else:
            azan_enabled_chats.append(chat_id)
            await msg.reply_text("تم تفعيل الأذان بنجاح")
    elif msg.text == "تعطيل الاذان":
        if chat_id in azan_enabled_chats:
            azan_enabled_chats.remove(chat_id)
            await msg.reply_text("تم تعطيل الأذان بنجاح")
        else:
            await msg.reply_text("الأذان معطل بالفعل في هذه المجموعة")

async def stop_azan():
    for chat_id in azan_enabled_chats:
        await Anony.force_stop_stream(chat_id)

async def play_azan(chat_id):
    assistant = await group_assistant(Anony, chat_id)
    azan_audio_path = "./assets/azan.mp3"
    stream = AudioPiped(azan_audio_path)
    try:
        await assistant.join_group_call(
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
#واخد موعيد الصلاه من الاستاذ ايرور
def get_prayer_time():
    try:
        prayer_times_response = requests.get("http://api.aladhan.com/timingsByAddress?address=Cairo&method=4&school=0").json()
        fajr_time = datetime.strptime(prayer_times_response['data']['timings']['Fajr'], '%H:%M').strftime('%I:%M %p')
        dhuhr_time = datetime.strptime(prayer_times_response['data']['timings']['Dhuhr'], '%H:%M').strftime('%I:%M %p')
        asr_time = datetime.strptime(prayer_times_response['data']['timings']['Asr'], '%H:%M').strftime('%I:%M %p')
        maghrib_time = datetime.strptime(prayer_times_response['data']['timings']['Maghrib'], '%H:%M').strftime('%I:%M %p')
        isha_time = datetime.strptime(prayer_times_response['data']['timings']['Isha'], '%H:%M').strftime('%I:%M %p')
        
        current_time = datetime.now(cairo_timezone).strftime('%I:%M %p')
        
        if current_time == fajr_time:
            return "اذان الفجر🕊❤"
        elif current_time == dhuhr_time:
            return "اذان الظهر 🕊❤"
        elif current_time == asr_time:
            return "اذان العصر 🕊❤"
        elif current_time == maghrib_time:
            return "اذان المغرب 🕊❤"
        elif current_time == isha_time:
            return "اذان العشاء 🕊❤"
    except Exception as e:
        asyncio.sleep(4)
        print(e)

async def azan_scheduler():
    while True:
        prayer_time = get_prayer_time()
        if prayer_time:
            await stop_azan()
            for chat_id in azan_enabled_chats:
                await app.send_message(chat_id, f"حان الآن وقت {prayer_time}، جاري تشغيل الآذان...")
                await play_azan(chat_id)
            await asyncio.sleep(177)
        await asyncio.sleep(2)
        
  asyncio.create_task(azan_scheduler())
