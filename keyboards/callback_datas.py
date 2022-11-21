from aiogram.utils.callback_data import CallbackData


refill_callback = CallbackData("refill", "part")
back_callback = CallbackData("back", "part")
region_callback = CallbackData("reg", "reg")
service_callback = CallbackData("srv", "srv")
receive_sms_callback = CallbackData("sms", "telstatus")
edit_sms_status_callback = CallbackData("edit", "telstatus")
act_num_callback = CallbackData("act_num", "num")
update_sms_callback = CallbackData("code", "answer")
update_balance_callback = CallbackData("money", "upd")
bad_price_callback = CallbackData("badprice", "clb")
