import asyncio
import configparser
import multiprocessing
import os

from aiogram import Bot
import openai
from pyrogram import Client
from pyrogram.enums import ChatType
from pyrogram.errors import Forbidden, AuthKeyDuplicated, FloodWait, MsgIdInvalid, ChannelPrivate, UserBannedInChannel


config = configparser.ConfigParser()
config.read('./config/main.ini')
bot = Bot(config['SETTINGS']['token'])
openai.api_key = config['SETTINGS']['chat_gpt']


def get_file(path_):
    for root, dirs, files in os.walk(path_):
        return [file for file in files]


def get_ids_():
    ids = []
    for root, dirs, files in os.walk(f'./config/'):
        for dirses in dirs:
            ids.append(int(dirses))
    return ids


async def chat_gpt(promt, post):
    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=f"Пост: {post}. {promt}",
        max_tokens=1024,
        temperature=0.85
    )

    return response.choices[0].text.split('\n')[-1]


async def start_session(name_session, api_id, api_hash, proxy, time_, sleep, promt):
    proxy_tg = {
        "scheme": "socks5",
        "hostname": proxy.split(':')[0],
        "port": int(proxy.split(':')[1]),
        "username": proxy.split(':')[2],
        "password": proxy.split(':')[3]
    }
    print(f"./session/{name_session[:-2]}/" + name_session)
    async with Client(f"./session/{name_session[:-2]}/" + name_session,
                      api_id=api_id, api_hash=api_hash, proxy=proxy_tg) as app:
        old_posts = []
        messages = 0
        me = await app.get_me()
        await bot.send_message(name_session, f"[+] @{me.username} автокомментит!")
        while True:
            try:
                async for dialog in app.get_dialogs():
                    await asyncio.sleep(10)
                    if dialog.chat.type == ChatType.CHANNEL:
                        message = app.get_chat_history(dialog.chat.id, limit=-1, offset=-1)
                        async for i in message:
                            post = i.text or i.caption
                            if (i.id, i.chat.id) not in old_posts:
                                text = await chat_gpt(promt, post)
                                try:
                                    msg = await app.get_discussion_message(i.chat.id, i.id)
                                    await msg.reply(text=text,
                                                    quote=True)
                                    old_posts.append((i.id, i.chat.id))
                                    print(f'@{me.username}: написал сообщение в канал {i.chat.username} c текстом\n'
                                          + text + '\n\n')
                                    await bot.send_message(name_session,
                                                           f'[+] @{me.username}: написал сообщение в канал '
                                                           f'@{i.chat.username} c текстом:\n ' + text + '\n\n')
                                    break
                                except Forbidden:
                                    chat = await app.get_chat(i.chat.id)
                                    await chat.linked_chat.join()
                                    print(f'@{me.username}: вступил в чат канала {i.chat.username}\n\n')
                                    await bot.send_message(name_session, f'[+] @{me.username}: '
                                                                         f'вступил в чат '
                                                                         f'канала @{i.chat.username}\n\n')
                                    await msg.reply(text=text,
                                                    quote=True)
                                    print(f'[+] @{me.username}: написал '
                                          f'сообщение в канал @{i.chat.username} c текстом:\n'
                                          + text + '\n\n')
                                    await bot.send_message(name_session, f'@{me.username}: написал сообщение в канал '
                                                           f'@{i.chat.username} c текстом:\n' + text + '\n\n')
                                except FloodWait:
                                    await asyncio.sleep(50)
                                    await bot.send_message(name_session, f"[-] Флуд система блокнула @{me.username}, "
                                                                         f"ожидайте 50 секунд")
                                    continue
                                except AuthKeyDuplicated:
                                    return await bot.send_message(name_session, f"У вас умерла сессия @{me.username}")
                                except MsgIdInvalid:
                                    continue
                                except ChannelPrivate:
                                    await app.leave_chat(i.id)
                                    await bot.send_message(name_session, f"[-] @{me.username} пришлось "
                                                                         f"покинуть канал @{i.chat.username}!")
                                    await app.send_message('@spambot', '/start')
                                    await asyncio.sleep(3)
                                    await app.send_message('@spambot', 'OK')
                                    await asyncio.sleep(3)
                                    await app.send_message('@spambot', '/start')

                                except UserBannedInChannel:
                                    app.leave_chat(i.id)
                                    await bot.send_message(name_session, f"[-] @{me.username} был "
                                                                         f"заблокирован в канале "
                                                                         f"@{i.chat.username}!")

                            if messages == int(sleep):
                                await bot.send_message(name_session, f"[+] @{me.username} был "
                                                                     f"отправлен в сон на 1000 секунд :)")
                                await asyncio.sleep(1000)
                                messages = 0
                                continue

                            messages += 1
                        await asyncio.sleep(float(time_))
            except Exception as e:
                print('ОШИБКА: ' + str(e))


def run_async_function(name_session, api_id, api_hash, proxy, time_, sleep, promt):
    asyncio.run(start_session(name_session, api_id, api_hash, proxy, time_, sleep, promt))


def main():
    for id_ in get_ids_():
        for file in get_file(f"./session/{id_}"):
            config.read(f"./config/{id_}/config_{file}"[:-8] + ".ini", encoding="UTF-8")
            process = multiprocessing.Process(target=run_async_function,
                                              args=(config['SETTINGS']['name_session'],
                                                    config['SETTINGS']['api_id'],
                                                    config['SETTINGS']['api_hash'],
                                                    config['SETTINGS']['proxy'],
                                                    config['SETTINGS']['time'],
                                                    config['SETTINGS']['loop_account'],
                                                    config['SETTINGS']['promt']))
            process.start()


if __name__ == "__main__":
    main()
