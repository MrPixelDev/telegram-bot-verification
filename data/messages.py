wallet_num = None
wallet_card = None

start_message = "ДОБРО ПОЖАЛОВАТЬ В СЕРВИС ПРИЕМА СМС\n" \
                "Удачного пользования!"

act_nums = "Выберите номер для запроса"

waiting_sms = "Сервис ожидает SMS\n\n" 

bad_api = "Внимание!"


def refill_message(refill_id):
    if wallet_num and wallet_card is not None:
        msg = "Пополнение происходит в автоматическом режиме\n"
    else:
        msg = "Автоматическое пополнение баланса временно недоступно.\n"
    return str(msg)
