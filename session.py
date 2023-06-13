import asyncio
import configparser
import sqlite3

from aiogram import Bot
from pyrogram import Client
from pyrogram.errors.exceptions import FloodWait, AuthKeyDuplicated
from requests import get
from requests.exceptions import ConnectionError
from aiofile import async_open

API_ID = 19309010
API_HASH = "dfdf154157cca400bd53b00100468fa5"


async def set_name(path_, name):
    app = Client(f"./session/{path_}", api_id=API_ID, api_hash=API_HASH)
    async with app:
        try:
            name = name.split()
            await app.update_profile(first_name=name[0], last_name=name[1])
            return "[+] Успешно изменен!"
        except Exception as e:
            return "[-] Не удалось изменить!"


async def set_description(path_, description):
    app = Client(f"./session/{path_}", api_id=API_ID, api_hash=API_HASH)
    async with app:
        try:
            await app.update_profile(bio=description)
            return "[+] Успешно изменен!"
        except Exception as e:
            return "[-] Не удалось изменить!"


async def joined_channels(path_, channels, proxy, api_id, api_hash):
    proxy_tg = {
        "scheme": "socks5",
        "hostname": proxy.split(':')[0],
        "port": int(proxy.split(':')[1]),
        "username": proxy.split(':')[2],
        "password": proxy.split(':')[3]
    }
    app = Client(path_, api_id=api_id, api_hash=api_hash, proxy=proxy_tg)
    config = configparser.ConfigParser()
    config.read('./config/main.ini')
    bot = Bot(config['SETTINGS']['token'])
    async with app:
        me = await app.get_me()
        try:
            for channel in channels:
                chat = await app.get_chat(channel)
                await app.join_chat(chat.id)
                await bot.send_message(int(path_.split('/')[2]), f"@{me.username}: присоединился к @{channel}\n")
                await asyncio.sleep(120)
        except FloodWait:
            await bot.send_message(int(path_.split('/')[2]), f"@{me.username}: "
                                                             f"не присоединился к @{channel} из-за antiflud системы\n")
            print('antiflood')
            await asyncio.sleep(300)
        except sqlite3.OperationalError:
            await bot.send_message(int(path_.split('/')[2]),
                                   f"@{me.username}: не присоединился к @{channel} из-за того, что сессия"
                                   f" открыта в другом файле\n")
            print('сессия занята')
        except AuthKeyDuplicated:
            print('сессия умерла')
            return await bot.send_message(int(path_.split('/')[2]), f"У вас умерла сессия @{me.username}")
        except Exception as e:
            print(e)
            await bot.send_message(int(path_.split('/')[2]),
                                   f"@{me.username}: не присоединился из-за {e}!")


async def set_photo(name_session, path_):
    app = Client(f"./session/{path_}", api_id=API_ID, api_hash=API_HASH)
    async with app:
        try:
            await app.set_profile_photo(photo=f'./photo/{name_session}.jpg')
            return "[+] Успешно изменен!"
        except Exception as e:
            return "[-] Не удалось изменить!"


async def check_session(path_):
    app = Client(path_, api_id=API_ID, api_hash=API_HASH)
    try:
        async with app:
            return True
    except Exception as e:
        return False


async def check_proxy(proxy):
    try:
        proxy = {
            "scheme": "socks5",
            "hostname": proxy.split(':')[0],
            "port": int(proxy.split(':')[1]),
            "username": proxy.split(':')[2],
            "password": proxy.split(':')[3]
        }
        get('https://httpbin.org/ip', proxies={
            'http': f'socks5://{proxy["username"]}:{proxy["password"]}@{proxy["hostname"]}:{proxy["port"]}',
            'https': f'socks5://{proxy["username"]}:{proxy["password"]}@{proxy["hostname"]}:{proxy["port"]}'
        })
        return True
    except IndexError:
        return 'Неправильно введён прокси!'
    except ConnectionError:
        return 'Ошибка подключения к прокси! Убедитесь в работоспособности прокси или проверьте правильность написания!'


async def get_description(path_):
    app = Client(path_, api_id=API_ID, api_hash=API_HASH)
    id_, username = await get_id(path_)
    async with app:
        me = await app.get_chat(id_)
    async with async_open(f'./info_account.txt', mode='a+') as info:
        await info.write(f"@{username} (ID: {id_}) : {me.bio}\n")


async def get_id(path_):
    app = Client(path_, api_id=API_ID, api_hash=API_HASH)
    async with app:
        me = await app.get_me()
    return [me.id, me.username]
