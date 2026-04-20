import random
import time
from loguru import logger
from config import config
from core.bot import Bot
from models.account import Account
from utils.inputs import input_pause, input_cycle_amount, input_cycle_pause, start_pause, get_value_from_txt, \
    cell_value_to_txt
from utils.logging import init_logger
from utils.utils import random_sleep, get_accounts, select_profiles

FILE = 'clear_cache.txt'


def accounts_filter(accounts: list[Account]) -> list[Account]:
    filter_accounts = []
    for account in accounts:
        if get_value_from_txt(account=account, filename=FILE) is None:
            filter_accounts.append(account)
    logger.info(f"Отфильтровано {len(filter_accounts)} аккаунтов для очистки кэша!")
    return filter_accounts


def worker(account: Account) -> None:
    try:
        with Bot(account) as bot:
            activity(bot)
    except Exception as e:
        logger.critical(f"{account.profile_number} Ошибка при инициализации Bot: {e}")


def activity(bot: Bot) -> None:
    try:
        cdp = bot.ads.context.new_cdp_session(bot.ads.page)
        cdp.send("Network.enable")
        cdp.send("Network.clearBrowserCache")
        cell_value_to_txt(bot, value='SUCCESS', filename=FILE)
        logger.success(f"{bot.account.profile_number} Кэш браузера очищен! 🎯")
    except Exception as e:
        logger.error(f"{bot.account.profile_number} Ошибка очистки кэша: {e}")


def main():
    init_logger()
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

        logger.success(f'Цикл {i + 1} завершен, обработано {len(filter_accounts)} аккаунтов! ✅')
        logger.info(f'Ожидание перед следующим циклом {cycle_pause / 60} минут!')
        random_sleep(cycle_pause)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logger.warning('Программа завершена вручную!')
