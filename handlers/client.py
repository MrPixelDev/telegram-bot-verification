import logging
import aiogram.types.message
from executor import bot
from API.SMS_API import get_number, set_status, get_balance
from API.QIWI_API import find_tx, refill_smsvf
from keyboards.client_kb import *
from data.sqlite_db import *
from data.messages import *
from aiogram import types, Dispatcher
from aiogram.types import ReplyKeyboardRemove, CallbackQuery
import time


def read_json(name):
    with open(f"./data/{name}.json") as file:
        data = json.load(file)
        return data


regs = read_json('regions')
svcs = read_json("servicecodes")


def get_service_name(val):
    for key, value in svcs['servicecodes'].items():
        if val == value:
            return key
    return logging.error("No key in servicecodes")


# ##-----------------------------------------------------------------
# Decorator checking master balance
# ##-----------------------------------------------------------------
def check_service_balance(func):
    async def wrapper(query):
        data = get_balance()
        if data[0] < 300:
            await bot.send_message(data[1], f"Необходимо пополнить баланс {data[0]}")
            logging.warning(f"{data[1]}, fНеобходимо пополнить баланс {data[0]}")
            await bot.send_message(query.from_user.id, "Сервис временно недоступен")
            return await command_exit(query)
        else:
            await func(query)
            return func
    return wrapper


# ##-----------------------------------------------------------------
# Decorator removing inactive nums from BD
# ##-----------------------------------------------------------------
def remove_inactive_nums_from_bd(func):
    async def wrapper(query):
        await fetch_active_nums(query)
        await func(query)
    return wrapper


# ##-----------------------------------------------------------------
# Decorator removing inline kb
# ##-----------------------------------------------------------------
def remove_inline_kb(func):
    async def wrapper(query):
        if type(query) == aiogram.types.CallbackQuery:
            chat_id = query.message.chat.id
            message_id = query.message.message_id
            await bot.edit_message_reply_markup(chat_id, message_id, reply_markup=None)
        await func(query)
    return wrapper


# ____________________________________________________________
# _______________________FUNCTIONALITY________________________
# ##-----------------------------------------------------------------
# Press "Exit" button
# ##-----------------------------------------------------------------
async def command_exit(message: types.Message):
    rmv_kb = ReplyKeyboardRemove()
    await bot.send_message(message.from_user.id, "Ждем вас снова!", reply_markup=rmv_kb)


@check_service_balance
@remove_inactive_nums_from_bd
async def command_start(*args):
    for arg in args:
        await bot.send_message(arg.from_user.id, start_message, reply_markup=kb_client)
        if type(arg) == types.Message:
            await new_user(query=arg)
        else:
            pass


# ##-----------------------------------------------------------------
# Press "Balance" Button
# ##-----------------------------------------------------------------
async def command_bal(query):
    refill_id = int(query.from_user.id) + 7
    msg = refill_message(refill_id)
    await find_tx(refill_id)
    await bot.send_message(
        query.from_user.id,
        f"БАЛАНС: {await show_balance(query.from_user.id)} руб.\n\n" + msg,
        reply_markup=kb_inline_balance
    )


# ##-----------------------------------------------------------------
# Press "Active Numbers" Button
# ##-----------------------------------------------------------------
async def command_nums(message: types.Message):
    nums = await active_numbers(message)
    if len(nums.values['inline_keyboard']) > 1:
        await bot.send_message(message.from_user.id, act_nums, reply_markup=nums)
    else:
        await bot.send_message(message.from_user.id, "У вас нет активных номеров", reply_markup=nums)


# ##-----------------------------------------------------------------
# From "Active Numbers" Press on number button
# ##-----------------------------------------------------------------
async def command_show_number(call: CallbackQuery):
    idnum = call.data[8:]
    set_status("send", idnum)
    sms_code = await get_sms_code(idnum)
    if list(sms_code.values())[0] is None:
        kb_inline_update = kb_inline_update_create(idnum)
        await bot.send_message(call.from_user.id, "Сервис ожидает SMS", reply_markup=kb_inline_update)
    elif list(sms_code.values())[0] == 'idNumNotFound':
        await bot.send_message(call.from_user.id, "Номер не найден")
    else:
        await bot.send_message(call.from_user.id, f"Ваш код: {list(sms_code.values())[0]}")


# ##-----------------------------------------------------------------
# Press "Back" button
# ##-----------------------------------------------------------------
@remove_inline_kb
async def command_back(call: CallbackQuery):
    await command_start(call)


# ##-----------------------------------------------------------------
# In Balance press "Update" button
# ##-----------------------------------------------------------------
@remove_inline_kb
async def command_refill(call: CallbackQuery):
    await bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
    await command_bal(call)


# ##-----------------------------------------------------------------
# On press "Receive SMS" choosing region
# ##-----------------------------------------------------------------
@check_service_balance
@remove_inactive_nums_from_bd
@remove_inline_kb
async def command_receive(query):
    if type(query) == aiogram.types.Message:
        chat_id = query.chat.id
    else:
        chat_id = query.message.chat.id
    await bot.send_message(chat_id, f"Выберите страну\n{bad_api}", reply_markup=kb_inline_region)


# ##-----------------------------------------------------------------
# On press "Choose region" choosing service
# ##-----------------------------------------------------------------
@remove_inline_kb
async def command_region(call: CallbackQuery):
    region_code = call.data[4:]
    await set_region(call, region_code)
    country = regs['regions'][region_code]

    if region_code == "fr" or region_code == "ca" or region_code == "es":
        await bot.edit_message_text(
            f"Страна временно недоступна\n\nВыберите другую\n\n{bad_api}",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=kb_inline_region
        )
    else:
        kb_inline_svc = kb_inline_svc_create(region_code)
        if not kb_inline_svc.values['inline_keyboard']:
            await bot.edit_message_text(
                f"Страна временно недоступна\nВыберите другую",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=kb_inline_region
            )
        else:
            await bot.edit_message_text(
                f"Страна: {country}", call.message.chat.id, call.message.message_id
            )
            await bot.send_message(
                call.from_user.id,
                f"Выберите сервис\nБаланс: {await show_balance(call.from_user.id)} руб.",
                reply_markup=kb_inline_svc
            )


# ##-----------------------------------------------------------------
# On press "Service" Taking Number and choosing what to do with, adding number to DB
# ##-----------------------------------------------------------------
@remove_inline_kb
async def command_service(call: CallbackQuery):
    service_code = call.data[4:8]
    price = float(call.data[8:])

    if float(price) > await show_balance(call.from_user.id):
        await bot.send_message(call.from_user.id, "На балансе недостаточно средств\n")
    else:
        await set_service(call, service_code)
        region_code = await return_region(call, service_code)
        svc = [k for k, v in svcs['servicecodes'].items() if v == f'{service_code}']

        await bot.edit_message_text(
            f"Сервис: {svc[0]}",
            call.message.chat.id,
            call.message.message_id
        )
        tel = get_number(service_code, region_code)
        if 'error' in tel.keys():
            if tel['error'] == 'noNumber':
                msg = await bot.send_message(
                    call.from_user.id,
                    "Сервис для данного региона временно недоступен\n"
                    "Попробуйте выбрать другой регион"
                )
                time.sleep(2)
                await command_receive(msg)
            elif tel['error'] == 'noMoney':
                await bot.send_message(call.from_user.id, "На балансе недостаточно средств\n")
        else:
            if str(tel['tel'])[:2] == "44":
                region_code = "en"
            if str(tel['tel'])[:2] == "49":
                region_code = "de"
            if str(tel['tel'])[:2] == "31":
                region_code = "nl"
            if str(tel['tel'])[:1] == "1":
                region_code = "us"
            cost = set_cost(region_code)
            service = get_service_name(service_code)
            for data in cost:
                if service in data:
                    try:
                        price = set_price(float(data[4].split("/")[1].rstrip("₽")))
                    except Exception as e:
                        logging.error(e)
                        pass
            await new_number(call, tel, price)
            kb_inline_numactions = kb_inline_numactions_create(tel, region_code)
            await update_balance(call.from_user.id, delta=-price)
            await bot.send_message(
                call.from_user.id,
                f"Номер телефона: +{tel['tel']}\n"
                f"Стоимость: {price} руб.\n"
                f"Выберите действие",
                reply_markup=kb_inline_numactions
            )


# ##-----------------------------------------------------------------
# On press "Update" to receive sms, adding code to DB
# ##-----------------------------------------------------------------
async def get_sms(call: CallbackQuery):
    idnum = call.data[5:-6]
    sms = await get_sms_code(idnum)
    try:
        if sms['error']:
            await bot.edit_message_text(
                "Номер недействителен",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=None
            )
    except KeyError as e:
        logging.error(e)
        try:
            if sms['smsCode'] is None:
                kb_inline_update = kb_inline_update_create(idnum)
                await bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id)
                await bot.edit_message_text(
                    waiting_sms,
                    call.message.chat.id,
                    call.message.message_id,
                    reply_markup=kb_inline_update
                )
            else:
                await bot.send_message(call.from_user.id, f"Ваш код: {sms['smsCode']}")
                await new_sms(idnum, sms['smsCode'])
        except json.decoder.JSONDecodeError as e1:
            logging.error(e1)
            await bot.send_message(call.from_user.id, "Номер недействителен")


# ##-----------------------------------------------------------------
# On press "Receive SMS" after taking number
# ##-----------------------------------------------------------------
@remove_inline_kb
async def command_receive_sms(call: CallbackQuery):
    await bot.edit_message_text(
        call.message.text.strip('\nВыберите действие'),
        call.message.chat.id,
        call.message.message_id
    )
    logging.warning(call.data)
    try:
        if call.data[4:6] == "de":
            num = int(call.data[6:19])
            status = call.data[19:]
        else:
            num = int(call.data[6:18])
            status = call.data[18:]
    except ValueError as e:
        logging.error(e)
        num = int(call.data[6:17])
        status = call.data[17:]
    idnum = await return_idnum(call, num)
    set_status(status, idnum)
    kb_inline_update = kb_inline_update_create(idnum)
    await bot.send_message(
        call.from_user.id,
        f"Сервис ожидает SMS\n"
        f"Баланс: {await show_balance(call.from_user.id)} руб.\n"
        f"Нажмите обновить для получения кода",
        reply_markup=kb_inline_update
    )


# ##-----------------------------------------------------------------
# On press "Cancel" or "Number is banned"
# ##-----------------------------------------------------------------
@remove_inline_kb
async def command_edit_status(call: CallbackQuery):
    try:
        if call.data[5:7] == "de":
            num = int(call.data[7:20])
            status = call.data[20:]
        else:
            num = int(call.data[7:19])
            status = call.data[19:]
    except ValueError as e:
        logging.error(e)
        num = int(call.data[7:18])
        status = call.data[18:]
    idnum = await return_idnum(call, num)
    response = set_status(status, idnum)
    if response['status'] != 'update':
        if response['status'] == 'waitSMS':
            await bot.send_message(call.from_user.id, "Отмена невозможна\nСервис ожидает SMS")
        else:
            await bot.send_message(call.from_user.id, f"Отмена невозможна\n{response}")
    else:
        price = await return_price(idnum, num)
        await deactivate_num(idnum)
        await update_balance(call.from_user.id, delta=price)
        await bot.send_message(call.from_user.id, f"Номер успешно отменен\n"
                                                  f"Баланс: {await show_balance(call.from_user.id)} руб.")


# ##-----------------------------------------------------------------
# Refill via /refill {number} {comment} {amount}
# ##-----------------------------------------------------------------
async def command_ref(message: types.Message):
    recipient = message.text.lstrip("/refill ")[:11]
    uid = message.text.lstrip("/refill ")[12:16]
    amount = message.text.lstrip("/refill ")[17:]
    tx = await refill_smsvf(recipient, amount, uid)
    if tx is None:
        await bot.send_message(message.chat.id, "Проверьте номер и айди")
    else:
        await bot.send_message(message.chat.id, f"{tx}")


# ##-----------------------------------------------------------------
# Registering Handlers (decorators revealed)
# ##-----------------------------------------------------------------
def register_handlers_client(dp: Dispatcher):
    dp.register_message_handler(command_start, commands=["start", "help"])
    dp.register_message_handler(command_exit, commands=["exit"], text=["Выход"])
    dp.register_message_handler(command_bal, text=["Баланс"])
    dp.register_message_handler(command_ref, commands=["refill"])
    dp.register_message_handler(command_nums, text=["Номера"])
    dp.register_message_handler(command_receive, text=["Принять смс"])
    dp.register_message_handler(command_exit, text=["Выход"])
    dp.register_callback_query_handler(command_refill, text_contains="refill")
    dp.register_callback_query_handler(command_receive, text_contains="badprice")
    dp.register_callback_query_handler(command_back, text_contains="back")
    dp.register_callback_query_handler(command_region, text_contains="reg")
    dp.register_callback_query_handler(command_service, text_contains="srv")
    dp.register_callback_query_handler(command_receive_sms, text_contains="sms")
    dp.register_callback_query_handler(command_edit_status, text_contains="edit")
    dp.register_callback_query_handler(command_show_number, text_contains="act_num")
    dp.register_callback_query_handler(get_sms, text_contains="code")
