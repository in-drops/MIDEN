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
    cell_date_to_txt, increase_counter_in_txt, get_value_from_txt, cell_value_to_txt
from utils.logging import init_logger
from utils.utils import (random_sleep, get_accounts, select_profiles, get_user_agent, get_price_token,
                         prepare_proxy_https)
import datetime
from twocaptcha import TwoCaptcha
import os
import json
import re






TARGET_PAGE = 'https://app.zoroswap.com/'
FILE = 'zoroswaps_count.txt'
FAUCET_FILE = 'zoroswap_faucets_count.txt'



def accounts_filter(accounts: list[Account]) -> list[Account]:

    filter_accounts = []
    filter_limit = 100 # <= Минимальный лимит Swaps для аккаунтов
    for account in accounts:
        native_count = get_value_from_txt(account=account, filename=FAUCET_FILE)
        if native_count is None:
            continue
        filter_count = get_value_from_txt(account=account, filename=FILE)
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

    bot.miden.auth_miden()
    random_sleep(1,3)
    bot.ads.open_url(TARGET_PAGE)

    swap_button = bot.ads.page.get_by_role('button', name='Swap', exact=True).nth(0)
    connect_button = bot.ads.page.get_by_role('button', name='Connect Wallet', exact=True).nth(0)


    for _ in range(30):
        if swap_button.is_visible() or connect_button.count():
            random_sleep(2)
            break
        time.sleep(1)
    else:
        logger.error('Ошибка входа на сайт!')
        return


    try:
        if connect_button.is_visible():
            connect_button.hover()
            time.sleep(0.5)
            bot.ads.random_click(connect_button)
            random_sleep(1.5)
            miden_btn = bot.ads.page.locator('button').filter(has_text='Miden Wallet')
            miden_btn_2 = bot.ads.page.locator('button[class="wallet-adapter-button "]')
            if miden_btn.is_visible():
                miden_btn.hover()
                time.sleep(0.5)
                bot.ads.random_click(miden_btn)
                random_sleep(1.5)
                if miden_btn_2.is_visible():
                    miden_btn_2.hover()
                    time.sleep(0.5)
                    bot.ads.random_click(miden_btn_2)
                    bot.miden.universal_confirm()

            for _ in range(30):
                if not connect_button.is_visible() and bot.ads.page.locator('div[class="top-4"]').locator('button').locator('span').filter(has_text='miden').is_visible():
                    logger.success('Подключение кошелька к сайту выполнено успешно!')
                    random_sleep(1.5)
                    break
                time.sleep(1)

    except Exception:
        logger.error('Подключение кошелька к сайту не удалось!')
        return

    swaps = 0
    errors = 0
    random_count = random.randint(3, 10)
    placeholder = bot.ads.page.get_by_placeholder('0').nth(0)
    insuficcient_liquidity = bot.ads.page.get_by_text('Amount too large')

    logger.warning(f'Выбрано случайное количество swaps: {random_count}! Начинаем активность...✈️')

    while swaps < random_count and errors < 5:
        '''SWAP'''
        try:

            if swaps >= random_count:
                logger.success(
                    f'Активность завершена! Всего выполнено swaps: {swaps}. Данные в {FILE}.🔥')
                return

            if errors >= 5:
                logger.error('Исчерпаны 5 попыток исправления ошибок swap-процессов!')
                logger.success(
                    f'Активность завершена! Всего выполнено swaps: {swaps}. Данные в {FILE}.🔥')
                return

            try:
                select = bot.ads.page.locator('select.h-auto.border-1.rounded-xl').nth(0)
                options = select.locator("option:not([disabled])")
                count = options.count()
                random_index = random.randint(0, count - 1)
                option = options.nth(random_index)
                random_value = option.get_attribute("value")
                token_name = option.inner_text().strip()
                select.select_option(value=random_value)
                logger.warning(f'Выбран первый токен ${token_name}...')
                random_sleep(2.5)

            except Exception:
                logger.error('Ошибка при выборе первого токена для swap! Продолжаем активность...')
                errors += 1
                bot.ads.page.reload()
                random_sleep(5, 10)
                continue

            try:
                select = bot.ads.page.locator('select.h-auto.border-1.rounded-xl').nth(1)
                options = select.locator("option:not([disabled])")
                count = options.count()
                random_index = random.randint(0, count - 1)
                option = options.nth(random_index)
                random_value = option.get_attribute("value")
                token_name = option.inner_text().strip()
                select.select_option(value=random_value)
                logger.warning(f'Выбран второй токен ${token_name}...')
                random_sleep(2.5)

            except Exception:
                logger.error('Ошибка при выборе второго токена для swap! Продолжаем активность...')
                errors += 1
                bot.ads.page.reload()
                random_sleep(5, 10)
                continue


            text = bot.ads.page.locator('div[class="p-3 sm:p-4 space-y-3 sm:space-y-4"]').nth(0).locator('div[class="flex items-center gap-1"]').inner_text()
            if not '.' in text:
                logger.warning(f'Баланс токена ${token_name} нулевой! Замена... 🚨')
                errors += 1
                random_sleep(1.5)
                continue
            else:
                value = float(re.findall(r'\d+(?:\.\d+)?', text)[0])



            if 0.5 >= value >= 0.1:
                amount = round(value * random.uniform(0.05, 0.2), 3)
                amount = f"{amount:.3f}".rstrip('0').rstrip('.')
            elif value <= 0.1:
                amount = round(value * random.uniform(0.05, 0.1), 3)
                amount = f"{amount:.3f}".rstrip('0').rstrip('.')
            elif value >= 0.5:
                amount = round(value * random.uniform(0.05, 0.15), 2)
                amount = f"{amount:.2f}".rstrip('0').rstrip('.')

            elif value >= 10:
                amount = int(value * random.uniform(0.05, 0.2))
            else:
                errors += 1
                continue



            placeholder.hover()
            time.sleep(0.5)
            bot.ads.random_click(placeholder)
            time.sleep(0.5)
            placeholder.fill('')
            random_sleep(1, 2)

            bot.ads.page.keyboard.type(str(amount), delay=300)
            random_sleep(2)

            if insuficcient_liquidity.is_visible():
                logger.warning('У выбранного токена недостаточно ликвидности! Продолжаем...')
                errors += 1
                random_sleep(1, 3)
                continue

            swap_button.hover()
            time.sleep(0.5)
            bot.ads.random_click(swap_button)
            bot.miden.universal_confirm()

            for _ in range(120):
                if bot.ads.page.get_by_text('Waiting for order confirmation ').is_visible() or bot.ads.page.get_by_text('Your order is waiting to be processed ...').is_visible():
                    logger.success('Swap выполнен успешно!🎯')
                    random_sleep(1)
                    bot.ads.page.locator('div[class="flex justify-between items-center mb-3"]').get_by_role('button').click()
                    increase_counter_in_txt(bot, filename=FILE)
                    swaps += 1
                    break
                time.sleep(1)

            else:
                logger.error(f'Ошибка swap-транзакции! Перезагрузка...')
                errors += 1
                bot.ads.page.reload()
                for _ in range(30):
                    if swap_button.is_visible():
                        random_sleep(2)
                        break
                    time.sleep(1)
                else:
                    logger.error('Ошибка входа на сайт!')
                    return
                continue

            if swaps >= random_count:
                logger.success(f'Активность на ZoroSwap завершена! Всего выполнено swaps: {swaps}. Данные в {FILE}.🔥')
                break

            random_sleep(5, 10)

        except Exception:
            logger.error(f'Ошибка swap-транзакции! Перезагрузка...')
            errors += 1
            for _ in range(30):
                if swap_button.is_visible():
                    random_sleep(2)
                    break
                time.sleep(1)
            else:
                logger.error('Ошибка входа на сайт!')
                return
            continue


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logger.warning('Программа завершена вручную!')