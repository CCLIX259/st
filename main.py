import time

from aiogram import Dispatcher, executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

from session import *
from start_session import *

config = configparser.ConfigParser()
config.read('./config/main.ini')
BOT_TOKEN = config['SETTINGS']['token']
bot = Bot(BOT_TOKEN)
dp = Dispatcher(bot=bot, storage=MemoryStorage())


class CalcStates(StatesGroup):
    session = State()
    api_id = State()
    api_hash = State()
    promt = State()
    sleep = State()
    channels = State()
    time_ = State()
    name = State()
    description = State()
    update_channels = State()
    proxy = State()
    photo = State()
    configs = State()
    answer_user = State()
    sessions = State()


async def download_sessions(message, path_):
    if os.path.splitext(message.document.file_name)[1] != '.session':
        return False
    await message.document.download(
        destination_file=path_
    )
    return True


def get_files(path_, check_ras=None):
    ret = []
    for root, dirs, files in os.walk(path_):
        if check_ras is None:
            return files
        for i in files:
            if os.path.splitext(i)[1] == check_ras:
                ret.append(i)
    return ret


@dp.message_handler(commands=['start', 'help'])
async def send_command(message):
    await message.answer(
        """
<b>Комманды:</b>
/show - информация об аккаунте 
/add - добавить аккаунт
                 """, parse_mode="HTML")


@dp.message_handler(commands=['add'])
async def add_account(message):
    await message.answer("Отправь сессию")
    await CalcStates.session.set()


@dp.message_handler(content_types=['document'], state=CalcStates.session)
async def get_session(message, state: FSMContext):
    sessions = get_files(f'./session/{message.from_user.id}', '.session')
    if not await download_sessions(message,
                                   f'./check_session/{message.from_user.id}/{message.from_user.id}_{len(sessions) + 1}'
                                   f'.session'):
        return await message.answer('Пришлите сессию с расширением ".session"!')

    if not await check_session(f"./check_session/{message.from_user.id}/{message.from_user.id}_{len(sessions) + 1}"):
        return await message.answer("[-] Сессия не валидна, возможно аккаунт был удален! Скиньте новую рабочую сессию!")

    await download_sessions(message,
                            f'./session/{message.from_user.id}/{message.from_user.id}_{len(sessions) + 1}'
                            f'.session')
    await get_description(f'./session/{message.from_user.id}/{message.from_user.id}_{len(sessions) + 1}')

    await state.update_data(session=f'{message.from_user.id}')
    await message.answer("Отправь api_id от сессии")
    await CalcStates.api_id.set()


@dp.message_handler(state=CalcStates.api_id)
async def get_api_id(message, state: FSMContext):
    await state.update_data(api_id=message.text)
    if not message.text.isdigit():
        return message.answer('Пришли только цифры!')
    await message.answer("Отправь api_hash от сессии")
    await CalcStates.api_hash.set()


@dp.message_handler(state=CalcStates.api_hash)
async def get_api_hash(message, state: FSMContext):
    await state.update_data(api_hash=message.text)
    await message.answer("Отправь промт")
    await CalcStates.promt.set()


@dp.message_handler(state=CalcStates.promt)
async def get_promt(message, state: FSMContext):
    await state.update_data(promt=message.text)
    await message.answer("После скольки сообщений отправить аккаунт в сон?")
    await CalcStates.sleep.set()


@dp.message_handler(state=CalcStates.sleep)
async def get_sleep(message, state: FSMContext):
    await state.update_data(sleep=message.text)
    if not message.text.isdigit():
        return message.answer('Пришли только цифры!')
    await message.answer("Скинь txt файл со списком каналов")
    await CalcStates.channels.set()


@dp.message_handler(content_types=['document'], state=CalcStates.channels)
async def get_channels(message, state: FSMContext):
    if os.path.splitext(message.document.file_name)[1] != '.txt':
        return await message.answer('Пришлите сессию с расширением ".txt"!')
    await message.document.download(destination_file=f"./channels/{message.from_user.id}_channels.txt")
    async with async_open(f'./channels/{message.from_user.id}_channels.txt', mode='r') as file:
        channels = await file.read()
    await state.update_data(channels=channels.splitlines())
    await message.answer("Отправьте ipv4 SOCK55 прокси в формате:\nip:port:username:password")
    await CalcStates.proxy.set()


@dp.message_handler(state=CalcStates.proxy)
async def get_proxy(message, state: FSMContext):
    await message.answer("Сейчас проверю прокси, подождите минуту!")
    check = await check_proxy(message.text)
    if check in ['Неправильно введён прокси!',
                 'Ошибка подключения к прокси! '
                 'Убедитесь в работоспособности прокси или проверьте правильность написания!']:
        return await message.answer(check)

    await state.update_data(proxy=message.text)
    await message.answer("Сколько задержку между комментированием?")
    await CalcStates.time_.set()


@dp.message_handler(state=CalcStates.time_)
async def get_time_(message, state: FSMContext):
    await state.update_data(time_=message.text)
    if not message.text.isdigit():
        return message.answer('Пришли только цифры!')
    await message.answer("Хотите поменять имя с фамилией аккаунта? Для этого напишите имя фамилия(через пробел), "
                         "или напишите -(если не хотите изменять)")
    await CalcStates.name.set()


@dp.message_handler(state=CalcStates.name)
async def set_name_(message, state: FSMContext):
    if message.text != "-":
        data = await state.get_data()
        session = data.get("session")
        sessions = get_files(f'./session/{message.from_user.id}/', '.session')
        result = await set_name(f"/{session}/{session}_{len(sessions)}", message.text)
        await message.answer(result)
    await message.answer("Хотите поменять фото аккаунта? напишите -, если не хотите изменять")
    await CalcStates.photo.set()


@dp.message_handler(content_types=['photo', 'text'], state=CalcStates.photo)
async def set_photo_(message, state: FSMContext):
    if message.text != "-":
        sessions = get_files(f'./session/{message.from_user.id}/', '.session')
        file_info = await bot.get_file(message.photo[-1].file_id)
        await message.photo[-1].download(f"./photo/{message.from_user.id}.{file_info.file_path.split('.')[-1]}")
        data = await state.get_data()
        session = data.get("session")
        result = await set_photo(session, f"/{session}/{session}_{len(sessions)}")
        await message.answer(result)
    await message.answer("Хотите поменять описание аккаунта? напишите -, если не хотите изменять")
    await CalcStates.description.set()


@dp.message_handler(state=CalcStates.description)
async def set_description_(message, state: FSMContext):
    data = await state.get_data()
    session = data.get("session")
    channels = data.get("channels")
    sleep = data.get("sleep")
    time_ = data.get("time_")
    api_id = data.get("api_id")
    api_hash = data.get("api_hash")
    promt = data.get("promt")
    proxy = data.get('proxy')
    sessions = get_files(f'./session/{message.from_user.id}/', '.session')
    if message.text != "-":
        result = await set_description(f"/{session}/{session}_{len(sessions)}", message.text)
        await message.answer(result)

    await message.answer("Подождите, добавляю в группы...")
    try:
        configs = get_files(f'./config/{message.from_user.id}/', '.ini')
        info_account = await get_id(f'./session/{message.from_user.id}/{message.from_user.id}_{len(configs) + 1}')
        await state.update_data(sessions=len(sessions))
        await state.update_data(configs=len(configs))
        async with async_open(f'./config/{message.from_user.id}/config_{message.from_user.id}_{len(configs) + 1}.ini',
                              mode='w+') as configfile:
            await configfile.write(
                f"[SETTINGS]\nname_session = {f'{session}_{len(sessions)}'}\napi_id = {api_id}\napi_hash = {api_hash}\n"
                f"promt = {promt}\nloop_account = {sleep}\ntime = {time_}\nproxy = {proxy}\nid = {info_account[0]}\n"
                f"username = {info_account[1]}")
        path_ = f"./config/{message.from_user.id}/config_{message.from_user.id}_{len(configs) + 1}.ini"
    except (FileNotFoundError, FileExistsError):
        os.makedirs(f'./config/{message.from_user.id}/')
        info_account = await get_id(f'./session/{message.from_user.id}/{message.from_user.id}_1')
        await state.update_data(configs=0)
        async with async_open(f'./config/{message.from_user.id}/config_{message.from_user.id}_1.ini',
                              mode='w+') as configfile:
            await configfile.write(f"[SETTINGS]\nname_session = {session}_1\napi_id = {api_id}\napi_hash = {api_hash}\n"
                                   f"promt = {promt}\nloop_account = {sleep}\ntime = {time_}\nproxy = {proxy}\n"
                                   f"id = {info_account[0]}\nusername = {info_account[1]}")
        path_ = f"./config/{message.from_user.id}/config_{message.from_user.id}_1.ini"

    try:
        process = multiprocessing.Process(target=run_async_channels,
                                          args=(f"./session/{session}/{session}"
                                                f"_{len(get_files(f'./session/{message.from_user.id}/', '.session'))}",
                                                channels, path_))
        process.start()

    except Exception as e:
        print(f"Добавление в группы: {e}")
        await message.answer("Что-то пошло не так при добавлении в группы!")

    await state.finish()
    await message.answer('Хотите ли вы добавить ещё сессии? '
                         'Напишите "-" если нет, любой другой ответ будет воспринят за согласие')
    await CalcStates.answer_user.set()


@dp.message_handler(state=CalcStates.answer_user)
async def get_answer_user(message, state: FSMContext):
    await state.update_data(answer_user=message.text)
    if message.text != '-':
        await message.answer('Пришлите сессию')
        await CalcStates.session.set()
    else:
        await message.answer('Готово')
        await state.finish()


def run_async_channels(path_, channels, path=None):
    if path is None:
        asyncio.run(joined_channels(path_, channels, 1, 1, 1))
    else:
        time.sleep(100)
        config.read(path, encoding="UTF-8")
        asyncio.run(joined_channels(path_, channels, config['SETTINGS']['proxy'],
                                    config['SETTINGS']['api_id'], config['SETTINGS']['api_hash']))
        time.sleep(100)
        process = multiprocessing.Process(target=run_async_function,
                                          args=(config['SETTINGS']['name_session'],
                                                config['SETTINGS']['api_id'],
                                                config['SETTINGS']['api_hash'],
                                                config['SETTINGS']['proxy'],
                                                config['SETTINGS']['time'],
                                                config['SETTINGS']['loop_account'],
                                                config['SETTINGS']['promt']))

        process.start()


@dp.message_handler(commands=['show'])
async def show_account(message):
    try:
        info = "----------------Запущенные аккаунты----------------\n\n"
        for i in get_file(f"./config/{message.from_user.id}/"):
            config.read(f"./config/{message.from_user.id}/{i}")
            info += f'Account: @{config["SETTINGS"]["username"]}\n'
            info += f'ID: {config["SETTINGS"]["id"]}\n'
            info += f'Proxy: {config["SETTINGS"]["proxy"]}\n\n'
        await message.answer(info)
    except TypeError:
        await message.answer("У тебя ничего не запущено :(")


if __name__ == "__main__":
    executor.start_polling(dispatcher=dp,
                           skip_updates=True)
