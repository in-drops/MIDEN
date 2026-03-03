import time
import requests
import random
from loguru import logger
from config import config, Chains, Tokens
from core.bot import Bot
from core.excel import Excel
from core.onchain import Onchain
from models.account import Account
from utils.inputs import input_pause, input_cycle_pause, input_cycle_amount, start_pause, get_date_from_txt, \
    cell_date_to_txt, increase_counter_in_txt, get_value_from_txt
from utils.logging import init_logger
from utils.utils import (random_sleep, get_accounts, select_profiles, get_user_agent, get_price_token,
                         prepare_proxy_https)
import datetime
from twocaptcha import TwoCaptcha

TARGET_PAGE = 'https://faucet.testnet.miden.io/'
FILE = 'private_faucet_date.txt'
FAUCET_FILE = 'success_private_faucet_count.txt'
ADDRESS_FILE = 'miden_addresses.txt'

def time_filter(accounts: list[Account]) -> list[Account]:
    filter_accounts = []
    filter_limit = 3 # <= Минимальный лимит Faucets Private Note для аккаунтов
    limit_date = datetime.datetime.now() - datetime.timedelta(minutes=1450)
    for account in accounts:
        last_date = get_date_from_txt(account=account, filename=FILE)
        if last_date is None:
            continue
        if last_date > limit_date:
            continue
        address = get_value_from_txt(account=account, filename=ADDRESS_FILE)
        if address is None:
            continue
        filter_count = get_value_from_txt(account=account, filename=FAUCET_FILE)
        if filter_count is None:
            filter_count = 0
        if filter_count >= filter_limit:
            continue
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
        filter_accounts = time_filter(accounts_for_work)
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

    bot.ads.open_url(TARGET_PAGE)
    placeholder = bot.ads.page.locator('input[id="recipient-address"]')
    placeholder.wait_for(state='visible')
    random_sleep(1.5)

    address = get_value_from_txt(account=bot.account, filename=ADDRESS_FILE)
    random_count = random.randint(1, 3)
    faucets = 0
    errors = 0

    while faucets < random_count and errors < 5:
        try:
            if errors >= 5:
                logger.error('Исчерпаны 5 попыток исправления ошибок faucet-процессов!')
                logger.success(f'Активность завершена! Всего выполнено faucets: {faucets}. Данные в {FAUCET_FILE}.🔥')
                return
            placeholder.hover()
            time.sleep(0.5)
            bot.ads.random_click(placeholder)
            time.sleep(0.5)
            placeholder.fill(address)
            random_sleep(1, 3)
            values = ["100000000", "500000000", "1000000000"]
            random_value = random.choice(values)
            bot.ads.page.locator("#token-amount").select_option(value=random_value)
            random_sleep(1, 3)
            request_button = bot.ads.page.locator('button[id="send-private-button"]')
            request_button.hover()
            time.sleep(0.5)
            bot.ads.random_click(request_button)
            for _ in range(60):
                if bot.ads.page.locator('div[id="private-success-tick"]').is_visible():
                    random_sleep(1.5)
                    logger.success(f'Токены {int(random_value) / 1000000} $MIDEN успешно получены! 🎯')
                    increase_counter_in_txt(bot, filename=FAUCET_FILE)
                    bot.ads.page.locator('button[id="private-close-button"]').click()
                    faucets += 1
                    break
                time.sleep(1)
            else:
                logger.error('Не удалось получить ответ от сайта за 60 секунд! Продолжаем...')
                bot.ads.page.reload()
                placeholder.wait_for(state='visible')
                errors += 1

            if faucets >= random_count:
                logger.success(f'Активность завершена! Всего выполнено faucets: {faucets}. Данные в {FAUCET_FILE}.🔥')
                break

            random_sleep(10, 15)


        except Exception:
            logger.error('Ошибка взаимодействия с сайтом!')
            bot.ads.page.reload()
            placeholder.wait_for(state='visible')
            errors += 1


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logger.warning('Программа завершена вручную!')

