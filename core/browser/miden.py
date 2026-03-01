import random
import time

import pyperclip
from loguru import logger
from core.browser.ads import Ads
from core.excel import Excel
from config import config
from models.account import Account
from models.chain import Chain
from utils.utils import random_sleep, generate_password, write_text_to_file

class Miden:
    """
    Класс для работы с Miden Wallet 1.13.1
    """

    def __init__(self, ads: Ads, account: Account, excel: Excel) -> None:
        self._url = config.miden_url
        self.ads = ads
        self.password = account.password
        self.seed = account.seed  # это сид-фраза в виде строки
        self.excel = excel


    def open_miden(self):
        '''Открытие страницы кошелька'''
        self.ads.open_url(self._url)
        random_sleep(5, 10)

    def import_wallet(self):

        '''Импорт кошелька по сид-фразе MetaMask'''

        self.ads.open_url('chrome-extension://ablmompanofnodfdkgchkpmphailefpb/fullpage.html')
        seed_list = self.seed.split(" ")
        if not self.password:
            self.password = generate_password()

        random_sleep(3, 5)

        try:
            self.ads.page.locator('button[id="import-link"]').wait_for(state='visible')
            random_sleep(2,3)
            self.ads.page.locator('button[id="import-link"]').click()
            random_sleep(2, 3)
            self.ads.page.locator('h2[class="font-medium text-base"]').nth(0).click()
            random_sleep(2, 3)
            for i, word in enumerate(seed_list):
                self.ads.page.locator('input').nth(i).fill(word)
                time.sleep(0.1)
            random_sleep(2, 3)
            self.ads.page.locator('button[id="submit-button"]').click()
            while not self.ads.page.locator('input[type="password"]').count():
                time.sleep(0.5)
            random_sleep(2, 3)

            self.ads.page.locator('input[placeholder="Enter password"]').nth(0).click()
            time.sleep(0.5)
            self.ads.page.locator('input[placeholder="Enter password"]').nth(0).fill(self.password)
            random_sleep(1, 2)
            self.ads.page.locator('input[placeholder="Enter password again"]').nth(0).click()
            time.sleep(0.5)
            self.ads.page.locator('input[placeholder="Enter password again"]').nth(0).fill(self.password)
            random_sleep(1, 2)

            self.ads.page.get_by_role('button', name='Continue').click()
            random_sleep(2, 3)

            self.ads.page.get_by_role('button', name='Get started').click()
            random_sleep(2, 3)
            while not self.ads.page.locator('a[href="/fullpage.html#/"]').is_visible():
                time.sleep(1)

            time.sleep(1)

        except Exception:
            logger.error('Ошибка импорта аккаунта MetaMask в Miden Wallet! Возможно кошелёк уже существует в профиле ADS...')

    def auth_miden(self) -> None:
        '''Авторизация в кошельке'''

        self.open_miden()

        if not self.password:
            raise Exception(f"{self.ads.profile_number}: Не указан пароль для авторизации в Rabby Wallet!")

        try:
            if self.ads.page.locator('input[id="password"]').is_visible():
                self.ads.page.locator('input[id="password"]').fill(self.password)
                random_sleep(1, 2)
                self.ads.page.locator('button[type="submit"]').click()
                time.sleep(3)

                if self.ads.page.locator('div[class="bg-r-neutral-bg-2"]').nth(0).is_visible():
                    logger.info(f"{self.ads.profile_number}: Успешная авторизация в Rabby Wallet!")
                    random_sleep(1, 3)

            else:
                logger.info(f"{self.ads.profile_number}: Уже авторизованы в Rabby Wallet!")
                random_sleep(1, 3)

        except Exception:
            logger.error(f"{self.ads.profile_number}: Ошибка авторизации в Rabby Wallet!")

    def wait_for_miden_page(self, timeout=10):
        for _ in range(int(timeout * 2)):
            for page in self.ads.context.pages:
                try:
                    url = page.url
                except:
                    continue

                if (
                        "chrome-extension://" in url
                        and ("notification" in url.lower() or "popup" in url.lower())
                ):
                    return page

            time.sleep(0.5)

        return None


    def universal_confirm(self, windows: int = 1, buttons: int = 1) -> None:
        '''Подтверждение транзакций в кошельке'''

        for _ in range(windows):
            random_sleep(5, 7)

            wallet_page = self.wait_for_miden_page()
            if wallet_page:
                # logger.success("Окно Rabby Wallet найдено! ✅")
                pass
            else:
                # logger.error("Не удалось найти окно Rabby Wallet! ")
                return

            time.sleep(1)

            if wallet_page.get_by_text("Ignore all", exact=True).is_visible():
                wallet_page.get_by_text("Ignore all", exact=True).click()
                time.sleep(1)

            if wallet_page and not wallet_page.is_closed() and wallet_page.locator('input[id="password"]').is_visible():
                wallet_page.locator('input[id="password"]').fill(self.password)
                random_sleep(1, 2)
                wallet_page.locator('button[type="submit"]').click()
                random_sleep(1)

            buttons_name = ['Connect',
                            'Sign',
                            'Confirm',
                            'Add'
                            ]

            for __ in range(buttons):
                for button in buttons_name:
                    if wallet_page.get_by_role('button', name=button).count():
                        for _ in range(60):
                            if wallet_page.get_by_role('button', name=button).is_enabled():
                                wallet_page.get_by_role('button', name=button).click()
                                time.sleep(2)
                                break
                            time.sleep(1)
                        if button == 'Sign':
                            for _ in range(30):
                                if wallet_page.get_by_role('button', name='Confirm').is_enabled():
                                    wallet_page.get_by_role('button', name='Confirm').click()
                                    time.sleep(1)
                                    break
                                time.sleep(1)

                        logger.info('Успешно подтверждено в Rabby Wallet!')
                        break

                else:
                    logger.error(f'{self.ads.profile_number} Ошибка подтверждения в Rabby Wallet!')
                    return

                time.sleep(3)

            wallet_page.close()