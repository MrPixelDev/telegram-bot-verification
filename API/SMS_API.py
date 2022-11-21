import logging

from environs import Env
import requests

env = Env()
env.read_env("./.env")

SMS_API_KEY = env.str("SMS_API_KEY")


# ##-----------------------------------------------------------------
# Get balance request
# ##-----------------------------------------------------------------
def get_balance():
    balance_link = f"http://***.com/api/getBalance/?apiKey={SMS_API_KEY}"
    response = requests.get(balance_link).json()
    data_tuple = (response["balance"], env.str("ADMIN_CHAT_ID"))
    logging.warning(data_tuple)
    return data_tuple


# ##-----------------------------------------------------------------
# Get number request
# ##-----------------------------------------------------------------
def get_number(service: str, country: str):
    get_number_link = f"http://***.com/api/getNumber/?apiKey={SMS_API_KEY}&service={service}&country={country}"
    response = requests.get(get_number_link).json()
    logging.warning(response)
    return response



# ##-----------------------------------------------------------------
# Set status to ready/bad/end of given number
# ##-----------------------------------------------------------------
def set_status(status: str, idnum: str):
    set_status_link = f"http://***.com/api/setStatus/?apiKey={SMS_API_KEY}&status={status}&idNum={idnum}"
    response = requests.get(set_status_link).json()
    logging.warning(response)
    return response


# ##-----------------------------------------------------------------
# Get sms code
# ##-----------------------------------------------------------------
async def get_sms_code(idnum: str):
    get_sms_code_link = f"http://***.com/api/getSmsCode/?apiKey={SMS_API_KEY}&idNum={idnum}"
    response = requests.get(get_sms_code_link).json()
    logging.warning(response)
    return response
