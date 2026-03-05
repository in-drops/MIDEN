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
                         prepare_proxy_https, get_list_from_file)
import datetime
from twocaptcha import TwoCaptcha
import os
import json
import re



FILE = 'transfers_count.txt'
FAUCET_FILE = 'success_public_faucet_count.txt'



def accounts_filter(accounts: list[Account]) -> list[Account]:

    filter_accounts = []
    filter_limit = 100 # <= Минимальный лимит Transfers для аккаунтов
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

    try:
        bot.ads.open_url('chrome-extension://ablmompanofnodfdkgchkpmphailefpb/fullpage.html')
        random_sleep(1)
        bot.ads.page.reload()
        random_sleep(5, 7)

        if bot.ads.page.locator('input[id="unlock-password"]').is_visible():
            bot.ads.page.locator('input[id="unlock-password"]').fill(bot.account.password)
            random_sleep(1, 2)
            bot.ads.page.get_by_role('button', name='Unlock').click()
            time.sleep(3)

        if bot.ads.page.get_by_role('button', name='Hide').is_visible():
            bot.ads.page.get_by_role('button', name='Hide').click()
            random_sleep(1)

        random_sleep(2)

        transfers = 0
        errors = 0
        random_count = random.randint(1, 5)
        address_ph = bot.ads.page.get_by_placeholder('Recipient account ID')
        amount_ph = bot.ads.page.get_by_placeholder('0')
        addresses = get_list_from_file("addresses_parsing.txt")

    except Exception:
        logger.error(f'Ошибка при входе в кошелёк!')
        return



    logger.warning(f'Выбрано случайное количество transfers на рандомные Miden адреса: {random_count}! Начинаем активность...✈️')

    while transfers < random_count and errors < 5:

        try:

            if transfers >= random_count:
                logger.success(
                    f'Активность завершена! Всего выполнено swaps: {transfers}. Данные в {FILE}.🔥')
                return

            if errors >= 5:
                logger.error('Исчерпаны 5 попыток исправления ошибок swap-процессов!')
                logger.success(
                    f'Активность завершена! Всего выполнено swaps: {transfers}. Данные в {FILE}.🔥')
                return

            if bot.ads.page.get_by_role('button', name='Hide').is_visible():
                bot.ads.page.get_by_role('button', name='Hide').click()
                random_sleep(1)

            if bot.ads.page.locator('a[href="/fullpage.html#/send"]').filter(has_text='Send').is_visible():
                bot.ads.page.locator('a[href="/fullpage.html#/send"]').filter(has_text='Send').click()
                random_sleep(3)

            tokens = bot.ads.page.locator('div[class="flex flex-1 overflow-hidden"]')
            count = tokens.count()
            idx = random.randrange(count)
            token = tokens.nth(idx)
            token_balance = token.locator('div[class="text-sm font-medium text-black"]').inner_text()
            token_balance = token_balance.replace(',', '')
            token_name = token.locator('p[class="text-sm font-medium text-black truncate text-ellipsis text-left"]').inner_text()
            value = float(token_balance)


            if value <= 0.01:
                logger.warning('Баланс выбранного токена слишком маленький! Замена... ')
                errors += 1
                random_sleep(1.5)
                continue

            token.click()



            if 0.5 >= value >= 0.1:
                amount = round(value * random.uniform(0.05, 0.2), 3)
                amount = f"{amount:.3f}".rstrip('0').rstrip('.')
            elif value <= 0.1:
                amount = round(value * random.uniform(0.05, 0.1), 3)
                amount = f"{amount:.3f}".rstrip('0').rstrip('.')
            elif 10 >= value >= 0.5:
                amount = round(value * random.uniform(0.05, 0.15), 2)
                amount = f"{amount:.2f}".rstrip('0').rstrip('.')

            elif 50 >= value >= 11:
                amount = int(value * random.uniform(0.1, 0.2))

            elif 200 >= value >= 51:
                amount = int(value * random.uniform(0.05, 0.1))

            elif 1000 >= value >= 201:
                amount = int(value * random.uniform(0.01, 0.05))

            elif value >= 1001:
                amount = int(value * random.uniform(0.01, 0.015))

            else:
                errors += 1
                continue


            logger.warning(f'Делаем transfer {amount} ${token_name}... ✈️')
            address_ph.hover()
            time.sleep(0.5)
            bot.ads.random_click(address_ph)
            time.sleep(0.5)
            address = random.choice(addresses)
            address_ph.fill(address)
            random_sleep(1)
            bot.ads.page.get_by_role('button', name='Next').click()
            random_sleep(1)

            amount_ph.hover()
            time.sleep(0.5)
            bot.ads.random_click(amount_ph)
            time.sleep(0.5)
            amount_ph.fill(str(amount))
            random_sleep(1)
            bot.ads.page.get_by_role('button', name='Next').click()
            random_sleep(1)
            bot.ads.page.get_by_role('button', name='Send').click()

            for _ in range(120):
                if bot.ads.page.get_by_text('Transaction Completed').count():
                    random_sleep(1.5)
                    bot.ads.page.get_by_role('button', name='Done').nth(0).click()
                    time.sleep(1)
                    if bot.ads.page.get_by_role('button', name='Done').nth(0).is_visible():
                        bot.ads.page.get_by_role('button', name='Done').nth(0).click()
                    logger.success('Transfer выполнен успешно!🎯')
                    increase_counter_in_txt(bot, filename=FILE)
                    transfers += 1
                    break
                time.sleep(1)

            else:
                logger.error(f'Ошибка transfer-транзакции! Перезагрузка...')
                errors += 1
                bot.ads.page.reload()
                bot.ads.open_url('chrome-extension://ablmompanofnodfdkgchkpmphailefpb/fullpage.html')
                random_sleep(1)
                bot.ads.page.reload()
                random_sleep(5, 7)
                try:
                    if bot.ads.page.locator('input[id="unlock-password"]').is_visible():
                        bot.ads.page.locator('input[id="unlock-password"]').fill(bot.account.password)
                        random_sleep(1, 2)
                        bot.ads.page.get_by_role('button', name='Unlock').click()
                        time.sleep(3)

                    if bot.ads.page.get_by_role('button', name='Hide').is_visible():
                        bot.ads.page.get_by_role('button', name='Hide').click()
                        random_sleep(1)

                    if bot.ads.page.locator('a[href="/fullpage.html#/send"]').filter(has_text='Send').is_visible():
                        bot.ads.page.locator('a[href="/fullpage.html#/send"]').filter(has_text='Send').click()
                        random_sleep(1)

                    random_sleep(1)
                except Exception:
                    logger.error(f'Ошибка на странице кошелька!')
                    return

            if transfers >= random_count:
                logger.success(f'Активность завершена! Всего выполнено transfers: {transfers}. Данные в {FILE}.🔥')
                break

            random_sleep(5, 10)

        except Exception:
            logger.error(f'Ошибка transfer-транзакции! Перезагрузка...')
            errors += 1
            bot.ads.open_url('chrome-extension://ablmompanofnodfdkgchkpmphailefpb/fullpage.html')
            random_sleep(1)
            bot.ads.page.reload()
            random_sleep(5, 7)

            try:
                if bot.ads.page.locator('input[id="unlock-password"]').is_visible():
                    bot.ads.page.locator('input[id="unlock-password"]').fill(bot.account.password)
                    random_sleep(1, 2)
                    bot.ads.page.get_by_role('button', name='Unlock').click()
                    time.sleep(3)

                if bot.ads.page.get_by_role('button', name='Hide').is_visible():
                    bot.ads.page.get_by_role('button', name='Hide').click()
                    random_sleep(1)

                if bot.ads.page.locator('a[href="/fullpage.html#/send"]').filter(has_text='Send').is_visible():
                    bot.ads.page.locator('a[href="/fullpage.html#/send"]').filter(has_text='Send').click()
                    random_sleep(1)

                random_sleep(1)
            except Exception:
                logger.error(f'Ошибка на странице кошелька!')
                return



    if errors >= 5:
        logger.error('Исчерпаны 5 попыток исправления ошибок swap-процессов!')
        logger.success(
            f'Активность завершена! Всего выполнено swaps: {transfers}. Данные в {FILE}.🔥')


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logger.warning('Программа завершена вручную!')