import time

import pyperclip
import requests
import random
from loguru import logger
from config import config, Chains, Tokens
from core.bot import Bot
from core.excel import Excel
from core.onchain import Onchain
from models.account import Account
from utils.inputs import input_pause, input_cycle_pause, input_cycle_amount, start_pause, get_date_from_txt, \
    cell_date_to_txt, increase_counter_in_txt, get_value_from_txt, cell_value_to_txt
from utils.logging import init_logger
from utils.utils import (random_sleep, get_accounts, select_profiles, get_user_agent, get_price_token,
                         prepare_proxy_https)
import datetime
from twocaptcha import TwoCaptcha


FILE = 'miden_addresses.txt'



def accounts_filter(accounts: list[Account]) -> list[Account]:
    filter_accounts = []
    for account in accounts:
        wallet = get_value_from_txt(account=account, filename=FILE)
        if wallet is None:
            filter_accounts.append(account)
    logger.info(f"Отфильтровано {len(filter_accounts)} аккаунтов для активности!")
    return filter_accounts

def main():

    init_logger()
    if not config.is_browser_run:
        config.is_browser_run = True

    accounts = get_accounts()
    accounts_for_work = select_profiles(accounts)
    pause = input_pause()
    cycle_amount = input_cycle_amount()
    cycle_pause = input_cycle_pause()
    time.sleep(start_pause())

    for i in range(cycle_amount):
        filter_accounts = accounts_filter(accounts_for_work)
        random.shuffle(filter_accounts)

        for account in filter_accounts:
            worker(account)
            random_sleep(pause)

        logger.success(f'Цикл {i + 1} завершен, обработано {len(filter_accounts)} аккаунтов!✅')
        logger.info(f'Ожидание перед следующим циклом {cycle_pause / 60} минут!')
        random_sleep(cycle_pause)

def worker(account: Account) -> None:

    try:
        with Bot(account) as bot:
            activity(bot)
    except Exception as e:
        logger.critical(f"{account.profile_number} Ошибка при инициализации Bot: {e}")

def activity(bot: Bot):
    ''''''


    bot.miden.import_wallet()
    for _ in range(30):
        if bot.ads.page.locator('a[href="/fullpage.html#/"]').is_visible():
            break
        time.sleep(0.5)
    else:
        logger.error('Ошибка создания Miden Wallet! Удалите расширение в профиле и перезапустите софт...')
        return
    random_sleep(1)
    button = bot.ads.page.locator("button span.mr-1").first
    button.click()
    time.sleep(0.5)
    address = pyperclip.paste()
    cell_value_to_txt(bot, value=address, filename=FILE)
    logger.success(
        f'Аккаунт MetaMask в Miden Wallet импортирован успешно! 🔥')


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logger.warning('Программа завершена вручную!')
