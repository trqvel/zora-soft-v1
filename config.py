from inspect import getsourcefile
from decimal import Decimal
from loguru import logger
from tqdm import tqdm
from web3 import Web3
import requests
import telebot
import random
import ctypes
import base64
import time
import hmac
import sys
import os
from settings import NFT_MINT_AMOUNT
from string import ascii_letters, digits

windll = ctypes.windll if os.name == 'nt' else None
sys.__stdout__ = sys.stdout # error with `import inquirer` without this string in some system
from inquirer import prompt, List

PATH = '*' + os.path.abspath(getsourcefile(lambda:0)).split("\\")[-2]+'*'
list_send = []
STR_DONE    = '✅ '
STR_CANCEL  = '❌ '

NFT_COLLECTIONS = [
        {'cid': "QmdYeDpkVZedk1mkGodjNmF35UNxwafhFLVvsHrWgJoz6A/beanz_metadata", 'supply': 19000},    # azuki beanz
        {'cid': "QmZcH4YvBVVRJtdn4RdbaqgspFU8gH6P9vomDpBVpAL3u4", 'supply': 10000},                   # azuki
        {'cid': "QmeSjSinHpPnmXmspMjwiXyN6zS4E9zccariGR3jxcaWtq", 'supply': 10000},                   # BAYC
        {'cid': "QmaN1jRPtmzeqhp6s3mR1SRK4q1xWPvFvwqW1jyN6trir9", 'supply': 20000},                   # Nakamigos
        {'cid': "QmSARWPw2tAoVwZMqBLjxSh2qKCZ8qBimxZccTkWnNBggh", 'supply': 17000},                   # PixelBubbies
        {'cid': "QmPMc4tcBsMqLRuCQtPmPe84bpSjrC3Ky7t3JWuHXYB4aS", 'supply': 10000},                   # Doodles
        {'cid': "QmU7pgaLsVkrP1ao7pn51wDE37PYNime6pV6mx8sUx1Nr4", 'supply': 10000},                   # ForgottenRunesWizardsCult
        {'cid': "QmWiQE65tmpYzcokCheQmng2DCM33DEhjXcPB6PanwpAZo", 'supply': 10000},                   # mfer
        {'cid': "QmUEiYGcZJWZWp9LNCTL5PGhGcjGvokKfcaCoj23dbp79J", 'supply': 10000},                   # SHIBOSHIS
        {'cid': "QmXUUXRSAJeb4u8p4yKHmXN1iAKtAV7jwLHjw35TNm5jN7", 'supply': 10000},                   # BoredApeKennelClub
        {'cid': "QmTDcCdt3yb6mZitzWBmQr65AW6Wska295Dg9nbEYpSUDR", 'supply': 9500},                    # Sappy Seals
    ]

ZORA_FEE = 777000000000000

with open('private_keys.txt') as f:
    p_keys = f.read().splitlines()

with open('words.txt') as f:
    WORDS = f.read().splitlines()

with open('nfts.txt') as f:
    nfts = f.read().splitlines()
    if len(nfts) < NFT_MINT_AMOUNT[1]:
        raise ValueError(f'Have {len(nfts)} nfts in `nfts.txt` but MAX NFT_MINT_AMOUNT = {NFT_MINT_AMOUNT[1]}')
    for nft in nfts:
        if len(nft.split(':')) < 2 or len(nft.split(':')) > 3:
            raise ValueError(f'{nft}\nNFTs in `nfts.txt` must contain `chain:address` or `chain:address:id`')


def get_native_prices():
    try:
        url = f'https://api.binance.com/api/v3/ticker/price?symbol=ETHUSDT'
        response = requests.get(url)

        if response.status_code == 200:
            result = [response.json()]
            return float(result[0]['price'])
        else:
            logger.error(f'response.status_code : {response.status_code}. try again')
            time.sleep(5)
            return get_native_prices()

    except Exception as error:
        logger.error(f'error : {error}. try again')
        time.sleep(5)
        return get_native_prices()

ETH_PRICE       = get_native_prices()


text = r"""
   ▒███████▒ ▒█████   ██▀███   ▄▄▄         ▓█████  ▄▄▄▄    ▄▄▄     ▄███████▓▓█████  ██▓  ██▒    
  ░▒ ▒ ▒ ▄▀░▒██▒  ██▒▓██ ▒ ██▒▒████▄       ▓█   ▀ ▓█████▄ ▒████▄   ▓  ██▒ ▓▒▓█   ▀ ▓██▒   ░█▒░   
   ░ ▒ ▄▀▒░ ▒██░  ██▒▓██ ░▄█ ▒▒██  ▀█▄     ▒███   ▒██▒ ▄██▒██  ▀█▄ ▒ ▓██░ ▒░▒███   ▒██ ░   ▒▒ 
     ▄▀▒   ░▒██   ██░▒██▀▀█▄  ░██▄▄▄▄██    ▒▓█  ▄ ▒██░█▀  ░██▄▄▄▄██░ ▓██▓ ░ ▒▓█  ▄ ▒██▄ ░  ░
   ▒███████▒░ ████▓▒░░██▓ ▒██▒ ▓█   ▓██▒   ░▒████▒░▓█  ▀█▓ ▓█   ▓██▒ ▒██▒ ░ ░▒████▒░██████▒
   ░▒▒ ▓░▒░▒░ ▒░▒░▒░ ░ ▒▓ ░▒▓░ ▒▒   ▓▒█░   ░░ ▒░ ░░▒▓███▀▒ ▒▒   ▓▒█░ ▒ ░░   ░░ ▒░ ░░ ▒░▓  ░
  ░░░▒ ▒ ░ ▒  ░ ▒ ▒░   ░▒ ░ ▒░  ▒   ▒▒ ░    ░ ░  ░▒░▒   ░   ▒   ▒▒ ░   ░     ░ ░  ░░ ░ ▒  ░
   ░ ░ ░ ░ ░░ ░ ░ ▒    ░░   ░   ░   ▒         ░    ░    ░   ░   ▒    ░         ░     ░ ░   
  ░  ░ ░        ░ ░     ░           ░  ░      ░  ░ ░            ░  ░           ░  ░    ░  ░
   ░                                                    ░                                                                                                                                                                                                                                                                                                             
"""
logger.remove()
logger.add(sys.stderr, format="<level>{message}</level>")
logger.error(text)
logger.remove()
logger.add(sys.stderr, format="<white>{time:HH:mm:ss:SSS}</white> | <level>{level: <6}</level> | <level>{message}</level>")
