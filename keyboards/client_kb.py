from parsers.cost import set_cost, set_price
from keyboards.callback_datas import *
from data.sqlite_db import fetch_active_nums
from data.read_json import read_json
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton


# ##-----------------------------------------------------------------
# Main Keyboard
# ##-----------------------------------------------------------------
balancebtn = KeyboardButton("Баланс")
numsbtn = KeyboardButton("Номера")
receivebtn = KeyboardButton("Принять смс")
exitbtn = KeyboardButton("Выход")
kb_client = ReplyKeyboardMarkup(resize_keyboard=True)
kb_client.add(balancebtn, numsbtn, receivebtn, exitbtn)


# ##-----------------------------------------------------------------
# Nav and standalone buttons
# ##-----------------------------------------------------------------
refill_btn = InlineKeyboardButton(text="Обновить баланс", callback_data=refill_callback.new(part="refill"))
back_btn = InlineKeyboardButton(text="Назад", callback_data=back_callback.new(part="back"))
kb_inline_balance = InlineKeyboardMarkup(one_time_keyboard=True)
kb_inline_balance.add(refill_btn, back_btn)


# ##-----------------------------------------------------------------
# Active number choosing inline keyboard
# ##-----------------------------------------------------------------
async def active_numbers(message):
    nums = await fetch_active_nums(message)
    act_nums_inline_kb = InlineKeyboardMarkup()
    srvccds_json = read_json("servicecodes")
    svc = ""
    for num in nums:
        for key, value in srvccds_json['servicecodes'].items():
            if value == num[2]:
                svc = key

        act_num_btn = InlineKeyboardButton(
            text=(str(num[0]) + " - " + str(svc)),
            callback_data=act_num_callback.new(num=str(num[1]))
        )

        act_nums_inline_kb.add(act_num_btn)
    act_nums_inline_kb.add(back_btn)
    return act_nums_inline_kb


# ##-----------------------------------------------------------------
# Region choosing inline keyboard
# ##-----------------------------------------------------------------
kb_inline_region = InlineKeyboardMarkup()
regions = read_json("regions")
for region in regions["regions"]:
    region_btn = InlineKeyboardButton(
        text=f"{regions['regions'][region]}",
        callback_data=region_callback.new(reg=region)
    )
    kb_inline_region.add(region_btn)


# ##-----------------------------------------------------------------
# Service choosing inline keyboard
# ##-----------------------------------------------------------------
def kb_inline_svc_create(region_code):
    kb_inline_service = InlineKeyboardMarkup()
    cost = set_cost(region_code)
    services = read_json("servicecodes")
    for service in services["servicecodes"]:
        for data in cost:
            if service in data:
                if data[3] == "0шт.":
                    break
                else:
                    svc_price = int(data[4][6:-1])
                    price = set_price(svc_price)
                    callback = services["servicecodes"][service] + str(price)

                    service_btn = InlineKeyboardButton(
                        text=f"{service}: {data[3]}, {price}₽",
                        callback_data=service_callback.new(srv=callback)
                    )

                    kb_inline_service.add(service_btn)
                    break
    if kb_inline_service.values['inline_keyboard']:
        inline_back = InlineKeyboardButton(text="Назад", callback_data=bad_price_callback.new(clb="callback"))
        kb_inline_service.add(inline_back)
    return kb_inline_service


# ##-----------------------------------------------------------------
# Actions with number inline keyboard
# ##-----------------------------------------------------------------
def kb_inline_numactions_create(tel, region_code):
    kb_inline_numactions = InlineKeyboardMarkup()
    callback = str(tel['tel'])
    receive_sms_btn = InlineKeyboardButton(
        text="Принять СМС",
        callback_data=receive_sms_callback.new(telstatus=region_code + callback + "send")
    )

    break_btn = InlineKeyboardButton(
        text="Отмена",
        callback_data=edit_sms_status_callback.new(telstatus=region_code + callback + "end")
    )

    blocked_btn = InlineKeyboardButton(
        text="Номер заблокирован",
        callback_data=edit_sms_status_callback.new(telstatus=region_code + callback + "bad")
    )

    kb_inline_numactions.add(receive_sms_btn, break_btn, blocked_btn)
    return kb_inline_numactions


# ##-----------------------------------------------------------------
# Update SMS Code inline keyboard
# ##-----------------------------------------------------------------
def kb_inline_update_create(idnum):
    kb_inline_update = InlineKeyboardMarkup()
    update_btn = InlineKeyboardButton(
        text="Обновить",
        callback_data=update_sms_callback.new(answer=str(idnum) + "update")
    )
    kb_inline_update.add(update_btn)
    return kb_inline_update
