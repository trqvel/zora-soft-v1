
# --------------- RPC ---------------
DATA = {
    'eth' : {'rpc': 'https://rpc.ankr.com/eth', 'scan': 'https://etherscan.io/tx', 'token': 'ETH', 'chain_id': 1},
    'zora': {'rpc': 'https://rpc.zora.energy', 'scan': 'https://explorer.zora.energy/tx', 'token': 'ETH', 'chain_id': 7777777},
    'oeth': {'rpc': 'https://rpc.ankr.com/optimism', 'scan': 'https://optimistic.etherscan.io/tx', 'token': 'ETH', 'chain_id': 10}, # optimism
}


# --------------- PROXY ---------------
USE_PROXY  = True
PROXY_DATA = 'http://W6HYifnx:GunQCgbt:166.1.238.250:64760'
CHANGE_PROXY_FOR_EACH_ACC = False # менять прокси перед каждым аккантом
PROXY_CHANGE_LINK = 'https://mobileproxy.space/reload.html?proxy_key=a6214a60a69ead59a3358e60df2675ed&format=json'


# --------------- TELEGRAM BOT ---------------
TG_BOT_SEND = True # True / False. нужно ли отправлять результаты в тг бота
TG_TOKEN    = ''
TG_IDS      = [
    ,
    # 12345,
]


# --------------- ADVANCED SETTINGS ---------------
CHECK_GWEI      = True # True / False
MAX_GWEI        = 25 # при каком максимальном гвее софт будет работать

RANDOM_WALLETS  = True # True / False | нужно ли рандомизировать (перемешивать) кошельки

RETRY           = 5 # кол-во попыток при ошибках / фейлах


# --------------- SOFT SETTINGS ---------------

MIN_ETH_BALANCE = 0.01 # если баланс меньше указанного то будет выводится эфир с ОКХ

NFT_MINT_AMOUNT     = [1,3] # сминтить рандомную нфт от 1 до 3 раз
NFT_CREATE_AMOUNT   = [1,2] # создать рандомную нфт от 1 до 3 раз
NFT_CHANGE_INFO     = [1,3] # изменить параметры рандомной созданной коллекции от 1 до 3 раз

AVAILABLE_MODULES = { # допустимые модули для изменения коллекции
    # True / False
    'change_main_info'          : True,
    'airdrop_to_random_wallet'  : True,
    'mint_own_nft'              : True,
    'set_funds_recipient'       : True,
    'change_description'        : True
}
HOW_MANY_ADDRESSES_TO_DROP = [1,2] # аирдропать нфт на от 1 до 3 кошельков | чем больше кошельков - тем больше комса
HOW_MANY_TO_MINT = [1,3] # купить себе бесплатно от 1 до 3 нфт | комса не сильно меняется от количества


# если газ за транзу с этой сети будет выше в $, тогда скрипт будет спать
MAX_GAS = {
    'eth'           : 4,
    'zora'          : 2,
}

def value_okx():
    """
    сколько_вывести = рандомное_число от amount_from до amount_to
    """

    api_key     = ''
    api_secret  = ''
    password    = ''

    symbol      = 'ETH'

    amount_from = 0.02
    amount_to   = 0.03

    SUB_ACC     = True

    return api_key, api_secret, password, symbol, amount_from, amount_to, SUB_ACC


def value_zora_bridge():
    """
    бридж из эфира в зору через офф мост https://bridge.zora.energy/
    эта настройка нужна только для 1 режима
    """

    amount_from = 0.02 # от какого количества бриджить ETH
    amount_to   = 0.03 # до какого количества бриджить ETH

    return amount_from, amount_to





















