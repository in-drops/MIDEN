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






TARGET_PAGE = 'https://app.zoroswap.com/faucet'
FILE = 'zoroswap_faucets_count.txt'
FAUCET_FILE = 'success_public_faucet_count.txt'



def accounts_filter(accounts: list[Account]) -> list[Account]:

    filter_accounts = []
    filter_limit = 50 # <= Минимальный лимит Faucets для аккаунтов
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

    btc_btn = bot.ads.page.get_by_role('button', name='Request BTC')
    eth_btn = bot.ads.page.get_by_role('button', name='Request ETH')
    usdc_btn = bot.ads.page.get_by_role('button', name='Request USDC')
    connect_button = bot.ads.page.get_by_role('button', name='Connect Wallet', exact=True).nth(0)


    for _ in range(30):
        if usdc_btn.is_visible() or connect_button.count():
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

    '''BTC MINT'''
    btc_random_mint = random.randint(1, 3)
    btc_mints = 0
    btc_errors = 0
    logger.warning(f'Получаем токены $BTC {btc_random_mint} раз(а)...✈️')


    while btc_mints <= btc_random_mint and btc_errors < 3:
        try:

            for _ in range(30):
                if btc_btn.is_enabled():
                    break
                time.sleep(1)

            if btc_btn.is_enabled():
                btc_btn.hover()
                time.sleep(0.5)
                bot.ads.random_click(btc_btn)
                for _ in range(30):
                    if bot.ads.page.get_by_text('Requested. Claim the tokens in your wallet!').count():
                        logger.success('Токены $BTC успешно получены! 🎯')
                        random_sleep(3)
                        btc_mints += 1
                        increase_counter_in_txt(bot, filename=FILE)
                        break
                    time.sleep(1)

                else:
                    logger.error('Ошибка mint-процесса! Продолжаем...')
                    btc_errors += 1
                    continue

                if btc_mints >= btc_random_mint:
                    break

        except Exception:
            logger.error('Ошибка mint-процесса! Перезагрузка...')
            btc_errors += 1
            bot.ads.page.reload()
            for _ in range(30):
                if usdc_btn.is_visible():
                    random_sleep(2)
                    break
                time.sleep(1)
            else:
                logger.error('Ошибка входа на сайт!')
                return
            random_sleep(1.5)
            continue

    if btc_errors >= 3:
        logger.error('Исчерпаны 3 попытки исправления Mint ошибок на сайте!')
        logger.success(
            f'Активность на ZoroSwap завершена! Данные в {FILE}. 🔥')
        return

    random_sleep(3)


    '''ETH MINT'''
    eth_random_mint = random.randint(1, 2)
    eth_mints = 0
    eth_errors = 0
    logger.warning(f'Получаем токены $ETH {eth_random_mint} раз(а)...✈️')


    while eth_mints <= eth_random_mint and eth_errors < 3:
        try:

            for _ in range(30):
                if eth_btn.is_enabled():
                    break
                time.sleep(1)

            if eth_btn.is_enabled():
                eth_btn.hover()
                time.sleep(0.5)
                bot.ads.random_click(eth_btn)
                for _ in range(30):
                    if bot.ads.page.get_by_text('Requested. Claim the tokens in your wallet!').count():
                        logger.success('Токены $ETH успешно получены! 🎯')
                        random_sleep(3)
                        eth_mints += 1
                        increase_counter_in_txt(bot, filename=FILE)
                        break
                    time.sleep(1)

                else:
                    logger.error('Ошибка mint-процесса! Продолжаем...')
                    eth_errors += 1
                    continue

                if eth_mints >= eth_random_mint:
                    break

        except Exception:
            logger.error('Ошибка mint-процесса! Перезагрузка...')
            btc_errors += 1
            bot.ads.page.reload()
            for _ in range(30):
                if usdc_btn.is_visible():
                    random_sleep(2)
                    break
                time.sleep(1)
            else:
                logger.error('Ошибка входа на сайт!')
                return
            random_sleep(1.5)
            continue

    if eth_errors >= 3:
        logger.error('Исчерпаны 3 попытки исправления Mint ошибок на сайте!')
        logger.success(
            f'Активность на ZoroSwap завершена! Данные в {FILE}. 🔥')
        return

    random_sleep(3)




    '''USDT MINT'''
    usdt_random_mint = random.randint(1, 2)
    usdt_mints = 0
    usdt_errors = 0
    logger.warning(f'Получаем токены $USDС {usdt_random_mint} раз(а)...✈️')


    while usdt_mints <= usdt_random_mint and usdt_errors < 3:
        try:

            for _ in range(30):
                if usdc_btn.is_enabled():
                    break
                time.sleep(1)

            if usdc_btn.is_enabled():
                usdc_btn.hover()
                time.sleep(0.5)
                bot.ads.random_click(usdc_btn)
                for _ in range(30):
                    if bot.ads.page.get_by_text('Requested. Claim the tokens in your wallet!').count():
                        logger.success('Токены $USDC успешно получены! 🎯')
                        random_sleep(3)
                        usdt_mints += 1
                        increase_counter_in_txt(bot, filename=FILE)
                        break
                    time.sleep(1)

                else:
                    logger.error('Ошибка mint-процесса! Продолжаем...')
                    usdt_errors += 1
                    continue

                if usdt_mints >= usdt_random_mint:
                    break

        except Exception:
            logger.error('Ошибка mint-процесса! Перезагрузка...')
            btc_errors += 1
            bot.ads.page.reload()
            for _ in range(30):
                if usdc_btn.is_visible():
                    random_sleep(2)
                    break
                time.sleep(1)
            else:
                logger.error('Ошибка входа на сайт!')
                return
            random_sleep(1.5)
            continue

    if usdt_errors >= 3:
        logger.error('Исчерпаны 3 попытки исправления Mint ошибок на сайте!')
        logger.success(
            f'Активность на ZoroSwap завершена! Данные в {FILE}. 🔥')
        return

    logger.warning('Делаем Claim токенов в кошельке... 💰')

    bot.miden.auth_miden()

    logger.success(
        f'Активность на ZoroSwap завершена! Данные в {FILE}. 🔥')

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logger.warning('Программа завершена вручную!')