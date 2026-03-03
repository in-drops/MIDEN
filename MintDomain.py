import datetime
import random
from loguru import logger
from config import config, Chains
from core.bot import Bot
from core.excel import Excel
from core.onchain import Onchain
from models.account import Account
from utils.inputs import input_pause, input_cycle_pause, input_cycle_amount, start_pause, get_value_from_txt, \
    cell_value_to_txt
from utils.logging import init_logger
from utils.utils import (random_sleep, get_accounts, select_profiles, get_list_from_file, generate_random_evm_address)
import time
from playwright.sync_api import expect


TARGET_PAGE = 'https://miden.name/'
FILE = 'mint_domain.txt'
FAUCET_FILE = 'success_public_faucet_count.txt'



def accounts_filter(accounts: list[Account]) -> list[Account]:
    filter_accounts = []
    for account in accounts:
        filter_count = get_value_from_txt(account=account, filename=FAUCET_FILE)
        if filter_count is None:
            continue
        success = get_value_from_txt(account=account, filename=FILE)
        if success is None:
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
    placeholder = bot.ads.page.locator('input[placeholder="e.g. joe"]')
    for _ in range(30):
        if bot.ads.page.get_by_role('button', name='Close').nth(0).is_visible() or placeholder.is_visible():
            random_sleep(2)
            break
        time.sleep(1)
    else:
        logger.error('Ошибка входа на сайт!')
        return

    if bot.ads.page.get_by_role('button', name='Close').nth(0).is_visible():
        bot.ads.page.get_by_role('button', name='Close').nth(0).click()
        random_sleep(1)
        if bot.ads.page.get_by_role('button', name='Close').nth(0).is_visible():
            bot.ads.page.get_by_role('button', name='Close').nth(0).click()
            random_sleep(1)

    try:
        connect_button = None
        connect_button_1 = bot.ads.page.get_by_role('button', name='Select Wallet', exact=True)
        connect_button_2 = bot.ads.page.locator('button').filter(has_text='Connect').locator('i[class="wallet-adapter-button-start-icon"]')
        if connect_button_1.count() and connect_button_1.is_visible():
            connect_button = connect_button_1
        elif connect_button_2.count() and connect_button_2.is_visible():
            connect_button = connect_button_2

        if connect_button:
            connect_button.hover()
            time.sleep(0.5)
            bot.ads.random_click(connect_button)
            random_sleep(1.5)
            miden_btn = bot.ads.page.locator('button[class="wallet-adapter-button "]')
            if miden_btn.is_visible():
                miden_btn.hover()
                time.sleep(0.5)
                bot.ads.random_click(miden_btn)
                bot.miden.universal_confirm()
            for _ in range(30):
                if not connect_button.is_visible() and bot.ads.page.locator('div[class="wallet-adapter-dropdown"]').locator('i[class="wallet-adapter-button-start-icon"]').is_visible():
                    logger.success('Подключение кошелька к сайту выполнено успешно!')
                    random_sleep(1.5)
                    break
                time.sleep(1)

    except Exception:
        logger.error('Подключение кошелька к сайту не удалось!')
        return

    try:
        logger.warning('Начинаем создавать Miden Domain...✈️')
        domain_name = bot.excel.get_cell('Gmail')
        if domain_name is None:
            logger.warning('Почта в таблице не найдена, создаём своё имя...')
            domain_name = random.choice([
                "CryptoKing", "BlockBuster", "ETHWhale", "DeFiDegen", "NFTGuru", "BTCHodler", "AltcoinAce",
                "SmartCoder", "WebThreeWiz", "AirdropGod", "SolanaSage", "PolyPioneer", "ChainChamp",
                "XRPRider", "BinanceBoss", "MegaMiner", "StakeMastr", "EtherElder", "CryptoShark",
                "WhaleWatch", "MoonMisson", "PumpHodl", "SatoshiWay", "BlockNinja", "YieldGod",
                "DappDude", "TokenTitan", "LamboSeekr", "CryptoNerd", "CryptoSnipe", "LiqLion",
                "BTCOldie", "DEXMaster", "SolidityDev", "LedgerLord", "KeyKeeper", "DeflaDon",
                "WebThreeNom", "AltHunter", "FlashLoanX", "MaskMage", "GasFeeGod", "CryptoPirate",
                "ApeBeliver", "NFTMinter", "ShitSamura", "DAODreamer", "TokenTact", "DropSniper",
                "LiqLegion", "EIPFan", "LTwoLegend", "XChainChamp", "FantomX", "AVAXVenture",
                "CyberCrypto", "WebThreeWhis", "BridgeBoss", "ArbitrumAce", "zkRollRider", "FOMOFight",
                "CryptoMind", "PTwoPElite", "DeFiSamur", "YieldYak", "HODLGuru", "CryptoInsid",
                "MEVHunter", "CEXExit", "GasGambler", "NFTTycoon", "DegenMode", "HFTTrader",
                "ETHMaxi", "CryptoVoygr", "BNBBeast", "CakeProfit", "FTXSurvivr", "ZeroHero",
                "RugRadar", "ONFTOG", "SolanaSnipe", "MultiSigX", "ShardSense", "AtomSwap",
                "FiatFighter", "DeFiDare", "StableStrat", "CryptoWar", "DarkForestX", "CryptoRekt",
                "TokenGamb", "GenTrader", "PerpPrince", "StakeShog", "AITradeBot", "DegenKnight",
                "MoonFindr", "CryptoEld", "NFADYOR", "MetaMogul", "FUDFight", "BullRunNow",
                "BearTrapX", "CryptoIllu", "GameFiPlay", "IDOInvest", "ICOInsid", "GenesisOG",
                "RareRuler", "NFTSnipe", "LedgerGod", "LPWizard", "OracleMstr", "HashHero",
                "HodlGains", "DeFiDon", "BlockArch", "ImmutableX", "ApeModeOn", "DustCollector",
                "TokenWhale", "CryptoPhan", "YieldChad", "AlphaHunt", "LiqLord", "GasSaver",
                "StakeKing", "MoonBagX", "CryptoDeity", "DerivDegen", "SecResearch", "BTCMil",
                "CypherWizard", "XChainKing", "CryptoGhost", "GovGiant", "OracleBoss", "WhaleObs",
                "DeFiKing", "RektSurviv", "HODLStrat", "InsidDegen", "DEXGenius", "StableKiller",
                "BlockExp", "SolSensei", "TokenEcon", "FlashLoanX", "RebaseKing", "FrontPhantom",
                "DecentDoge", "WebThreeSeek", "SmartMoves", "DEXDomina", "NFTFlipp", "CryptoAlch",
                "EVMWiz", "BTCVetra", "WalletWar", "XBridgeX", "ZkSnarkZ", "ERCMaster",
                "CoinGeckoX", "CryptoSha", "MEVProfit", "FarmFanat", "CyberHack", "LiqProvide",
                "ShillMast", "HODLover", "FlashSwapX", "TokenBurn", "DropKing", "CryptoOrcl",
                "SmartKiller", "ERC721X", "GameFiWin", "LendLegend", "PerpTrade", "CryptoDru",
                "LPFarm", "LiqTyrant", "AltSeeker", "StableInv", "FOMOWar", "NFTCollX",
                "GenWealth", "ArbKing", "BTCPionr", "ShitExp", "ProtoWhisp", "LiqGod",
                "SmartWhale", "DEXDomina", "CryptoHust", "FiatEscap", "EthereumX", "UniSwapX",
                "DeFiBuild", "CryptoFut", "NFTMag", "PTwoPTycoon", "TokenTita", "CryptoCart",
                "DeflaDoge", "MegaWhale", "TokenTroll", "PrivCoin", "CryptoCur", "VCInsider",
                "DAOMaster", "RektRid", "MetaMogul", "CryptoTita", "NFTDeity", "DEXOrDie",
                "LedgerLoad", "CryptoCyb", "SatoSucc", "BlockNomad", "CryptoSurv", "CryptoProp",
                "WhaleWatch", "LPXMaster", "MultiSigX", "NFTKing", "CryptoInfl", "DAOGod",
                "ZKLayerX", "GameFiWhl", "BitcoinBar", "CryptoSor", "ValVision", "StakeSavvy",
                "DeFiApe", "CryptoMog", "TokenGuru", "RektInv", "HodlHands", "ChainExp",
                "CryptoSch", "MoonMani", "WAGMIWiz", "MetaMaskX", "NFTOrac", "BlockSeer",
                "DegenOver", "FlashKing", "GasSage", "AirdropX", "WebThreeStrat", "StakeWhale",
                "LiqOver", "BitcoinHod", "AltWar", "DEXArch", "GameFiInv", "CryptoGod",
                "BlockVis", "EtherWar", "CryptoYoda", "MultiChain", "NFTBaron", "BlockChad",
                "SmartInv", "ValChief", "CryptoCode", "MEVGenius", "TokenHunt", "DegenEmp",
                "YieldMax", "WenLambo", "CryptoFOMO", "StakeOver", "CryptoZen", "ChainWhale",
                "DropChamp", "MoonMiss", "DegenInv", "CryptoElt", "WenTGE", "BTCApe",
                "WebThreeOver", "LPStrat", "ArbitrumX", "DAOWisp", "RebaseWar", "NFTMill",
                "MEVBotX"])

        else:
            domain_name = bot.excel.get_cell('Gmail').replace("@gmail.com", "")
        placeholder.hover()
        time.sleep(0.5)
        bot.ads.random_click(placeholder)
        time.sleep(0.5)
        placeholder.fill('')
        random_sleep(2, 3)
        bot.ads.page.keyboard.type(f'{domain_name}', delay=300)
        random_sleep(3, 5)

        for _ in range(60):
            if bot.ads.page.locator('div[class="flex items-center justify-between gap-3"]').filter(
                    has_text='Available').filter(
                    has_not_text='Unavailable').is_visible() or bot.ads.page.locator(
                'div[class="flex items-center justify-between gap-3"]').filter(has_text='Unavailable').is_visible():
                random_sleep(2)
                break
            time.sleep(3)
        else:
            logger.error('Ошибка создания Miden Domain при вводе имени!')
            return

        if bot.ads.page.locator('div[class="flex items-center justify-between gap-3"]').filter(
                has_text='Available').filter(
            has_not_text='Unavailable').is_visible():
            bot.ads.page.locator('div[class="flex items-center justify-between gap-3"]').filter(
                has_text='Available').filter(
                has_not_text='Unavailable').hover()
            time.sleep(0.5)
            bot.ads.page.locator('div[class="flex items-center justify-between gap-3"]').filter(
                has_text='Available').filter(
                has_not_text='Unavailable').click()
            random_sleep(2)
            check_balance_btn = bot.ads.page.get_by_role('button', name='Check MIDEN balance')
            if check_balance_btn.is_visible():
                check_balance_btn.hover()
                time.sleep(0.5)
                bot.ads.random_click(check_balance_btn)
                bot.miden.universal_confirm()
                claim_btn = bot.ads.page.get_by_role('button', name='Claim • 20 MIDEN')

                for _ in range(30):
                    if claim_btn.is_visible():
                        break
                    if bot.ads.page.get_by_role('button', name='Retry check MIDEN balance').is_visible():
                        logger.error('Ошибка проверки баланса на сайте! Возможно баланс нулевой...')
                        return
                    time.sleep(1)

                if claim_btn.is_visible():
                    claim_btn.hover()
                    time.sleep(0.5)
                    bot.ads.random_click(claim_btn)
                    bot.miden.universal_confirm()
                    for _ in range(60):
                        if bot.ads.page.get_by_text('Transaction Sent!').count():
                            logger.success('Miden Domain успешно создан! 🔥')
                            cell_value_to_txt(bot, value='SUCCESS', filename=FILE)
                            break
                        time.sleep(1)
                    else:
                        logger.error('Ошибка создания Miden Domain! Перезапустите софт...')

        if bot.ads.page.locator(
                'div[class="flex items-center justify-between gap-3"]').filter(has_text='Unavailable').is_visible():
            logger.warning('Доменное имя, привязанное к почте уже занято! Создайте Miden Domain вручную... 🚨')

    except Exception:
        logger.error('Ошибка создания Miden Domain! Перезапустите софт...')
        return

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logger.warning('Программа завершена вручную!')