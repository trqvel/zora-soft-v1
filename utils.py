from config import *
from settings import *
from abi import *


def send_msg(list_send):
    if type(list_send) == list:
        str_send = '\n'.join(list_send)
    else:
        str_send = text
    bot = telebot.TeleBot(TG_TOKEN, disable_web_page_preview=True, parse_mode='HTML')
    for tg_id in TG_IDS:
        try:
            bot.send_message(tg_id, str_send)
        except Exception as error:
            logger.error(f'tg send error: {error}')

def get_web3(chain, pk=False):

    rpc = DATA[chain]['rpc']

    if USE_PROXY == True:
        while True:
            try:
                web3 = Web3(Web3.HTTPProvider(rpc, request_kwargs={"proxies":{'https' : PROXY_DATA, 'http' : PROXY_DATA}}))
                break
            except Exception as error:
                logger.error(f'{error}. Cant connect to proxy ({PROXY_DATA})')
                send_msg('🚧 не могу подключить прокси к web3 🚧')
                input('\nPress Enter to continue...\n> Enter')


    else:
        web3 = Web3(Web3.HTTPProvider(rpc))

    return web3

def update_name(account_num=0, on_return=False, on_welcome=False):
    version = '1.0'

    if on_welcome:
        if os.name == 'nt':
            windll.kernel32.SetConsoleTitleW(f'Zora v{version} | {len(p_keys)} accounts loaded | {PATH}')
        return

    if on_return:
        return f'account [{account_num}/{len(p_keys)}] | {PATH}'
    if os.name == 'nt':
        windll.kernel32.SetConsoleTitleW(f'Zora v{version} '
                                         f'| account [{account_num}/{len(p_keys)}] '
                                         f'| {PATH}')

def sleeping(*timing):
    if len(timing) == 2: x = random.randint(timing[0], timing[1])
    else: x = timing[0]
    for _ in tqdm(range(x), desc='sleep ', bar_format='{desc}: {n_fmt}/{total_fmt}'):
        time.sleep(1)

def okx_withdraw(privatekey, CHAIN, eth_balance, retry=0):
    def okx_data(api_key, secret_key, passphras, request_path="/api/v5/account/balance?ccy=USDT", body='', meth="GET"):

        try:
            import datetime
            def signature(
                    timestamp: str, method: str, request_path: str, secret_key: str, body: str = ""
            ) -> str:
                if not body:
                    body = ""

                message = timestamp + method.upper() + request_path + body
                mac = hmac.new(
                    bytes(secret_key, encoding="utf-8"),
                    bytes(message, encoding="utf-8"),
                    digestmod="sha256",
                )
                d = mac.digest()
                return base64.b64encode(d).decode("utf-8")

            dt_now = datetime.datetime.utcnow()
            ms = str(dt_now.microsecond).zfill(6)[:3]
            timestamp = f"{dt_now:%Y-%m-%dT%H:%M:%S}.{ms}Z"

            base_url = "https://www.okex.com"
            headers = {
                "Content-Type": "application/json",
                "OK-ACCESS-KEY": api_key,
                "OK-ACCESS-SIGN": signature(timestamp, meth, request_path, secret_key, body),
                "OK-ACCESS-TIMESTAMP": timestamp,
                "OK-ACCESS-PASSPHRASE": passphras,
                'x-simulated-trading': '0'
            }
        except Exception as ex:
            logger.error(ex)
        return base_url, request_path, headers

    api_key, secret_key, passphras, SYMBOL, amount_from, amount_to, SUB_ACC = value_okx()

    wallet = Web3().eth.account.from_key(privatekey).address

    # take FEE for withdraw
    _, _, headers = okx_data(api_key, secret_key, passphras, request_path=f"/api/v5/asset/currencies?ccy={SYMBOL}", meth="GET")
    response = requests.get(f"https://www.okx.cab/api/v5/asset/currencies?ccy={SYMBOL}", timeout=10, headers=headers)
    if not response.json().get('data'):
        logger.error(f'OKX response error: {response.json()}')
        sleeping(30,80)
        return okx_withdraw(privatekey, CHAIN, eth_balance, retry)

    for lst in response.json()['data']:
        if lst['chain'] == f'{SYMBOL}-{CHAIN}':
            FEE = lst['minFee']


    try:
        while True:
            if SUB_ACC == True:

                _, _, headers = okx_data(api_key, secret_key, passphras, request_path=f"/api/v5/users/subaccount/list", meth="GET")
                list_sub =  requests.get("https://www.okx.cab/api/v5/users/subaccount/list", timeout=10, headers=headers)
                list_sub = list_sub.json()

                for sub_data in list_sub['data']:
                    while True:
                        name_sub = sub_data['subAcct']

                        _, _, headers = okx_data(api_key, secret_key, passphras, request_path=f"/api/v5/asset/subaccount/balances?subAcct={name_sub}&ccy={SYMBOL}", meth="GET")
                        sub_balance = requests.get(f"https://www.okx.cab/api/v5/asset/subaccount/balances?subAcct={name_sub}&ccy={SYMBOL}",timeout=10, headers=headers)
                        sub_balance = sub_balance.json()
                        if sub_balance.get('msg') == f'Sub-account {name_sub} doesn\'t exist':
                            logger.warning(f'ERROR | {sub_balance["msg"]}')
                            continue
                        sub_balance = sub_balance['data'][0]['bal']

                        logger.info(f'{name_sub} | {sub_balance} {SYMBOL}')

                        if float(sub_balance) > 0:
                            body = {"ccy": f"{SYMBOL}", "amt": str(sub_balance), "from": 6, "to": 6, "type": "2", "subAcct": name_sub}
                            _, _, headers = okx_data(api_key, secret_key, passphras, request_path=f"/api/v5/asset/transfer", body=str(body), meth="POST")
                            a = requests.post("https://www.okx.cab/api/v5/asset/transfer",data=str(body), timeout=10, headers=headers)
                        # time.sleep(1)
                        break

            try:
                _, _, headers = okx_data(api_key, secret_key, passphras, request_path=f"/api/v5/account/balance?ccy={SYMBOL}")
                balance = requests.get(f'https://www.okx.cab/api/v5/account/balance?ccy={SYMBOL}', timeout=10, headers=headers)
                balance = balance.json()
                balance = balance["data"][0]["details"][0]["cashBal"]
                # print(balance)

                if balance != 0:
                    body = {"ccy": f"{SYMBOL}", "amt": float(balance), "from": 18, "to": 6, "type": "0", "subAcct": "", "clientId": "", "loanTrans": "", "omitPosRisk": ""}
                    _, _, headers = okx_data(api_key, secret_key, passphras, request_path=f"/api/v5/asset/transfer", body=str(body), meth="POST")
                    a = requests.post("https://www.okx.cab/api/v5/asset/transfer",data=str(body), timeout=10, headers=headers)
            except Exception as ex:
                pass


            # CHECK MAIN BALANCE
            _, _, headers = okx_data(api_key, secret_key, passphras,
                                     request_path=f"/api/v5/asset/balances?ccy={SYMBOL}", meth="GET")
            main_balance = requests.get(f'https://www.okx.cab/api/v5/asset/balances?ccy={SYMBOL}', timeout=10,
                                        headers=headers)
            main_balance = main_balance.json()
            main_balance = float(main_balance["data"][0]['availBal'])
            logger.info(f'total balance | {main_balance} {SYMBOL}')

            if amount_from > main_balance:
                logger.warning(f'not enough balance ({main_balance} < {amount_from}), waiting 10 secs...')
                time.sleep(10)
                continue

            if amount_to > main_balance:
                logger.warning(f'you want to withdraw MAX {amount_to} but have only {round(main_balance, 7)}')
                amount_to = round(main_balance, 7)

            AMOUNT = round(random.uniform(amount_from, amount_to), 7) #  - eth_balance
            break


        body = {"ccy":SYMBOL, "amt":AMOUNT, "fee":FEE, "dest":"4", "chain":f"{SYMBOL}-{CHAIN}", "toAddr":wallet}
        _, _, headers = okx_data(api_key, secret_key, passphras, request_path=f"/api/v5/asset/withdrawal", meth="POST", body=str(body))
        a = requests.post("https://www.okx.cab/api/v5/asset/withdrawal",data=str(body), timeout=10, headers=headers)
        result = a.json()
        # cprint(result, 'blue')

        if result['code'] == '0':
            logger.success(f"withdraw success => {wallet} | {AMOUNT} {SYMBOL}")
            list_send.append(f'{STR_DONE}okx_withdraw | {AMOUNT} {SYMBOL}')
            return AMOUNT
        else:
            error = result['msg']
            logger.error(f"withdraw unsuccess => {wallet} | error : {error}")
            if retry < RETRY:
                return okx_withdraw(privatekey, CHAIN, eth_balance, retry+1)
            else:
                list_send.append(f"{STR_CANCEL}okx_withdraw :  {result['msg']}")

    except Exception as error:
        logger.error(f"withdraw unsuccess => {wallet} | error : {error}")
        if retry < RETRY:
            logger.info(f"try again in 10 sec. => {wallet}")
            sleeping(10, 10)
            if 'Insufficient balance' in str(error): return okx_withdraw(privatekey, CHAIN, eth_balance, retry)
            return okx_withdraw(privatekey, CHAIN, eth_balance, retry+1)
        else:
            list_send.append(f'{STR_CANCEL}okx_withdraw')

def pick_path():
    questions = [
        List('prefered_path', message="What path do you prefer?",
             choices=[
                'Path 1 | Bridge ETH in range -> Zora (withdraw OKX if needed) + Modules',
                'Path 2 | Bridge all ETH -> Zora + Modules',
                'Path 3 | Only modules',
             ]
        )
    ]
    path = prompt(questions)['prefered_path']
    if 'Path 1 |' in path:
        PATH = '1'
    elif 'Path 2 |' in path:
        PATH = '2'
    elif 'Path 3 |' in path:
        PATH = '3'

    return PATH

def get_random_nft(retry=0):
    """
    get data of random nft from saved nft collections
    """

    while True:
        try:
            collection = random.choice(NFT_COLLECTIONS)
            link = f'https://ipfs.io/ipfs/{collection["cid"]}/{random.randint(1, collection["supply"] - 1)}'
            r = requests.get(link)
            link2 = f"https://ipfs.io/ipfs/{r.headers['X-Ipfs-Roots'].split(',')[-1]}"
            r2 = requests.get(link2)

            return r2.json()['image']
        except Exception as err:
            logger.warning(f'cant get random nft ({retry}/{RETRY}): {err}')

            if retry < RETRY:
                time.sleep(10)
                retry += 1
            else:
                logger.error(f'Cant parse NFT in {retry} times, skip minting')
                list_send.append(f'{STR_CANCEL}Cant parse NFT in {retry} times, skip minting')
                return False

# --- web3 helpers ---

def change_proxy():
    r = requests.get(PROXY_CHANGE_LINK)
    if 'mobileproxy.space' in PROXY_CHANGE_LINK and '&format=json' in PROXY_CHANGE_LINK:
        if r.json().get('status') != 'OK' or r.json().get('code') != 200:
            logger.error(f'Failed to get new proxy: {r.json()}')
            time.sleep(10)
            change_proxy()
        else:
            logger.debug(f'proxy changed: {r.json()["new_ip"]}')
    else:
        logger.debug(f'change proxy status: {r.status_code}')

def get_random_collection(address, retry=0):
    url = f'https://api.goldsky.com/api/public/project_clhk16b61ay9t49vm6ntn4mkz/subgraphs/zora-create-zora-mainnet/stable/gn'
    payload = {
        "query": "query userCollections($admin: Bytes!, $offset: Int!, $limit: Int!, $contractStandards: [String!] = [\"ERC1155\", \"ERC721\"], $orderDirection: OrderDirection! = desc) {\n  zoraCreateContracts(\n    orderBy: createdAtBlock\n    orderDirection: $orderDirection\n    where: {permissions_: {user: $admin, isAdmin: true}, contractStandard_in: $contractStandards}\n    first: $limit\n    skip: $offset\n  ) {\n    ...Collection\n  }\n}\n\nfragment Collection on ZoraCreateContract {\n  id\n  address\n  name\n  symbol\n  owner\n  creator\n  contractURI\n  contractStandard\n  contractVersion\n  mintFeePerQuantity\n  timestamp\n  metadata {\n    ...Metadata\n  }\n  tokens {\n    ...Token\n  }\n  salesStrategies {\n    ...SalesStrategy\n  }\n  royalties {\n    ...Royalties\n  }\n  txn {\n    ...TxnInfo\n  }\n}\n\nfragment Metadata on MetadataInfo {\n  name\n  description\n  image\n  animationUrl\n  rawJson\n}\n\nfragment Token on ZoraCreateToken {\n  id\n  tokenId\n  address\n  uri\n  maxSupply\n  totalMinted\n  rendererContract\n  contract {\n    id\n    owner\n    creator\n    contractVersion\n    metadata {\n      ...Metadata\n    }\n  }\n  metadata {\n    ...Metadata\n  }\n  permissions {\n    user\n  }\n  salesStrategies {\n    ...SalesStrategy\n  }\n  royalties {\n    ...Royalties\n  }\n}\n\nfragment SalesStrategy on SalesStrategyConfig {\n  presale {\n    presaleStart\n    presaleEnd\n    merkleRoot\n    configAddress\n    fundsRecipient\n    txn {\n      timestamp\n    }\n  }\n  fixedPrice {\n    maxTokensPerAddress\n    saleStart\n    saleEnd\n    pricePerToken\n    configAddress\n    fundsRecipient\n    txn {\n      timestamp\n    }\n  }\n  redeemMinter {\n    configAddress\n    redeemsInstructionsHash\n    ethAmount\n    ethRecipient\n    isActive\n    saleEnd\n    saleStart\n    target\n    txn {\n      timestamp\n    }\n    redeemMintToken {\n      tokenId\n      tokenType\n      tokenContract\n      amount\n    }\n    redeemInstructions {\n      amount\n      tokenType\n      tokenIdStart\n      tokenIdEnd\n      burnFunction\n      tokenContract\n      transferRecipient\n    }\n  }\n}\n\nfragment Royalties on RoyaltyConfig {\n  royaltyBPS\n  royaltyRecipient\n  royaltyMintSchedule\n}\n\nfragment TxnInfo on TransactionInfo {\n  id\n  block\n  timestamp\n}\n",
        "variables": {
            "admin": address.lower(),
            "offset": 0,
            "limit": 36
        },
        "operationName": "userCollections"
    }
    r = requests.post(url, json=payload)
    try:
        all_collections = r.json()['data']['zoraCreateContracts']

        if len(all_collections) > 0:
            logger.debug(f'found {len(all_collections)} collections')
            return random.choice(all_collections)['address']
        else:
            logger.error(f'found {len(all_collections)} collections')
            return False
    except Exception as err:
        logger.warning(f'Error when parsing address collection: {err}')
        if retry < RETRY: get_random_collection(address, retry+1)
        else:
            list_send.append(f'{STR_CANCEL}parse address collections')
            return False

def make_contract(web3, address, abi):
    return web3.eth.contract(
        address=web3.to_checksum_address(address),
        abi=abi
    )

def check_status_tx(chain, tx_hash, text='checking tx_status'):
    logger.info(f'{chain} {text} : {tx_hash}')

    while True:
        try:
            web3        = get_web3(chain)
            status      = web3.eth.get_transaction_receipt(tx_hash).status
            if status in [0, 1]:
                return status
            time.sleep(1)
        except Exception as error:
            # logger.info(f'error, try again : {error}')
            time.sleep(1)

def check_allowance(chain, token_address, privatekey, spender):
    try:
        web3 = get_web3(chain, privatekey)
        wallet = web3.eth.account.from_key(privatekey).address
        contract  = web3.eth.contract(address=Web3.to_checksum_address(token_address), abi=ERC20_ABI)
        amount_approved = contract.functions.allowance(wallet, spender).call()
        return amount_approved
    except Exception as error:
        logger.error(error)

def check_data_token(web3, token_address):
    try:

        token_contract = web3.eth.contract(address=Web3.to_checksum_address(token_address), abi=ERC20_ABI)
        decimals = token_contract.functions.decimals().call()
        symbol = token_contract.functions.symbol().call()

        return token_contract, decimals, symbol

    except Exception as error:
        logger.error(f'check token data error: {error}')

def check_balance(privatekey, chain, address_contract=False, human=True):
    try:
        web3 = get_web3(chain)

        wallet = web3.eth.account.from_key(privatekey).address

        if address_contract in ['', False]:  # eth
            balance = web3.eth.get_balance(web3.to_checksum_address(wallet))
            token_decimal = 18
        else:
            token_contract, token_decimal, symbol = check_data_token(web3, address_contract)
            balance = token_contract.functions.balanceOf(web3.to_checksum_address(wallet)).call()

        if not human:
            return balance

        human_readable = balance / 10 ** token_decimal

        return human_readable

    except Exception as error:
        logger.error(error)
        time.sleep(1)
        check_balance(privatekey, chain, address_contract, human)

def wait_balance(privatekey, chain, min_balance, token=False):
    logger.debug(f'wait {round(Decimal(min_balance), 8)} in {chain}')

    while True:
        try:
            if not token:
                humanReadable = check_balance(privatekey, chain)
            else:
                humanReadable = check_balance(privatekey, chain, token)

            if humanReadable >= min_balance:
                logger.info(f'balance : {humanReadable}')
                break
            time.sleep(15)
        except Exception as error:
            logger.error(f'wait balance error: {error}, sleeping 60 secs...')
            time.sleep(60)

def sign_tx(web3, contract_txn, privatekey):
    signed_tx = web3.eth.account.sign_transaction(contract_txn, privatekey)
    raw_tx_hash = web3.eth.send_raw_transaction(signed_tx.rawTransaction)
    tx_hash = web3.to_hex(raw_tx_hash)

    return tx_hash

def approve_(amount, privatekey, chain, token_address, spender, retry=0):
    try:
        if amount == 0:
            logger.error(f'want to approve 0 tokens (token: {token_address}; spender: {spender})')
            return

        web3 = get_web3(chain, privatekey)

        spender = Web3.to_checksum_address(spender)

        wallet = web3.eth.account.from_key(privatekey).address
        contract, decimals, symbol = check_data_token(web3, token_address)

        ratio = random.randint(40, 400)

        module_str = f'approve: {int(amount * ratio) / 10 ** decimals} {symbol}'

        allowance_amount = check_allowance(chain, token_address, privatekey, spender)

        if amount > allowance_amount:

            contract_txn = contract.functions.approve(
                spender,
                int(amount * ratio)
            ).build_transaction(
                {
                    "chainId": web3.eth.chain_id,
                    "from": wallet,
                    "nonce": web3.eth.get_transaction_count(wallet),
                    'gasPrice': web3.eth.gas_price,
                }
            )

            tx_hash = sign_tx(web3, contract_txn, privatekey)
            tx_link = f'{DATA[chain]["scan"]}/{tx_hash}'

            status = check_status_tx(chain, tx_hash, 'approve')

            if status == 1:
                logger.success(f"{module_str} | {tx_link}")
                sleeping(15, 30)
            else:
                logger.error(f"{module_str} | tx is failed | {tx_link}")
                list_send.append(f'{STR_CANCEL}{module_str} | tx is failed | <a href="{tx_link}">link 👈</a>')

    except Exception as error:
        logger.error(f'{error}')
        if retry < RETRY:
            logger.info(f'try again in 10 sec.')
            sleeping(10, 10)
            approve_(amount, privatekey, chain, token_address, spender, retry + 1)

def checker_total_fee(chain, gas):
    gas = (gas / 10 ** 18) * ETH_PRICE

    if gas > MAX_GAS[chain]:
        logger.info(f'gas is too high : {round(gas, 2)} $ > {MAX_GAS[chain]} $. sleep and try check again')
        sleeping(30)
        return False
    else:
        return gas

def send_tx(pk, web3, tx, chain, module_str, value=0, check_text='checking tx_status', check_price=False, multiply_gas=False):
    retry = 0
    address = web3.eth.account.from_key(pk).address
    while True:
        try:

            if chain == 'zora':
                max_priority = int(0.005 * 10 ** 9)
                max_fee = int(0.005 * 10 ** 9)
            else:
                max_priority = web3.eth.max_priority_fee
                last_block = web3.eth.get_block('latest')
                base_fee = last_block['baseFeePerGas']
                block_filled = last_block['gasUsed'] / last_block['gasLimit'] * 100
                if block_filled > 50: base_fee *= 1.125
                max_fee = int(base_fee + max_priority)


            contract_txn = tx.build_transaction({
                'from': address,
                "nonce": web3.eth.get_transaction_count(address),
                'chainId': web3.eth.chain_id,
                'value': value,
                'maxPriorityFeePerGas': max_priority,
                'maxFeePerGas': max_fee
            })
            if multiply_gas: contract_txn['gas'] = int(contract_txn['gas'] * multiply_gas)

            total_fee = int(contract_txn['gas'] * max_fee)
            if check_price == True: return total_fee / 10 ** 18

            gas = checker_total_fee(chain, total_fee)
            if gas == False: continue

            tx_hash = sign_tx(web3, contract_txn, pk)
            tx_link = f'{DATA[chain]["scan"]}/{tx_hash}'

            status = check_status_tx(chain, tx_hash, check_text)

            if status == 1:
                logger.success(f'{module_str} | {tx_link}')
                list_send.append(f'{STR_DONE}{module_str}')
                return True

            else:
                logger.error(f'{module_str} | tx is failed | {tx_link}')
                if retry < RETRY:
                    retry += 1
                    continue
                else:
                    list_send.append(f'{STR_CANCEL}{module_str} | tx is failed | <a href="{tx_link}">link 👈</a>')
                    return False
        except Exception as error:
            logger.error(f'{module_str} | {error}')
            sleeping(10, 20)
            if retry < RETRY:
                retry += 1
            else:
                list_send.append(f'{STR_CANCEL}{module_str}')
                return False

# --- modules ---

def deposit_to_zora(pk, estimate_cost=False):
    if PATH == '1':
        amount_from, amount_to = value_zora_bridge()
        amount_to_bridge = round(random.uniform(amount_from, amount_to), 7)
        estimate_cost = True
    else:
        eth_balance = check_balance(pk, 'eth', human=True)
        if not estimate_cost:
            amount_to_bridge = eth_balance / 2
        else:
            amount_to_bridge = round(eth_balance - estimate_cost * 1.2, 6)

    chain = 'eth'
    value = int(amount_to_bridge * 10 ** 18)
    eth_balance = check_balance(pk, chain)

    module_str = f'bridge {amount_to_bridge} ETH to Zora'
    if estimate_cost:
        logger.info(module_str)

    if amount_to_bridge > eth_balance:
        if amount_from > eth_balance:
            logger.error(f'{module_str} not enough ETH to bridge to Zora')
            return False
        return deposit_to_zora(pk)

    web3 = get_web3(chain, pk)
    address = web3.eth.account.from_key(pk).address

    contract = make_contract(web3, '0x1a0ad011913A150f69f6A19DF447A0CfD9551054', ZORA_BRIDGE_ABI)

    tx = contract.functions.depositTransaction(
        address,
        value,
        100000,
        False,
        '0x'
    )

    if not estimate_cost:
        estimate_cost = send_tx(pk, web3, tx, chain, module_str, value=value, check_text='bridge to zora', check_price=True, multiply_gas=1.3)
        return deposit_to_zora(pk, estimate_cost=estimate_cost)

    status = send_tx(pk, web3, tx, chain, module_str, value=value, check_text='bridge to zora', multiply_gas=1.2)
    return status

def mint_nft(pk):
    def mint_721_nft(pk, chain, contract_address):

        module_str = f'mint 721 nft'
        logger.info(module_str)

        web3 = get_web3(chain, pk)

        contract = make_contract(web3, contract_address, NFT_721_ABI)

        value = ZORA_FEE + contract.functions.salesConfig().call()[0]
        tx = contract.functions.purchase(1)

        status = send_tx(pk, web3, tx, chain, module_str, value=value, check_text='mint 721 nft')
        return status

    def mint_1155_nft(pk, chain, contract_address, nft_id):

        module_str = 'mint 1155 nft'
        logger.info(module_str)

        web3 = get_web3(chain, pk)
        address = web3.eth.account.from_key(pk).address

        price_contract = make_contract(web3, '0x169d9147dFc9409AfA4E558dF2C9ABeebc020182', NFT_PRICE_ABI)
        contract = make_contract(web3, contract_address, NFT_1122_ABI)

        value = ZORA_FEE + price_contract.functions.sale(contract.address, nft_id).call()[3]

        tx = contract.functions.mint(
            web3.to_checksum_address('0x169d9147dFc9409AfA4E558dF2C9ABeebc020182'), # const address
            nft_id,
            1, # amount
            '0x'+address[2:].zfill(64)
        )

        status = send_tx(pk, web3, tx, chain, module_str, value=value, check_text='mint 1155 nft')
        return status


    with open('nfts.txt') as f:
        nfts_list = f.read().splitlines()
        random.shuffle(nfts_list)

    for _ in range(random.randint(NFT_MINT_AMOUNT[0], NFT_MINT_AMOUNT[1])):

        picked_nft = nfts_list.pop(random.randint(0,len(nfts_list)-1)).split(':')
        try:
            if len(picked_nft) == 2:
                mint_721_nft(pk, picked_nft[0], picked_nft[1])
            else:
                mint_1155_nft(pk, picked_nft[0], picked_nft[1], int(picked_nft[2]))
            sleeping(20, 40)
        except Exception as err:
            if 'Could not transact with/call contract function, is contract deployed correctly' in str(err):
                err = 'wrong nft chain'
            logger.error(f'mint nft error: {err}')
            list_send.append(f'{STR_CANCEL}mint nft error: {err}')

def create_nft(pk):
    chain = 'zora'
    module_str = 'create nft'

    web3 = get_web3(chain, pk)
    address = web3.eth.account.from_key(pk).address
    contract = make_contract(web3, '0xA2c2A96A232113Dd4993E8b048EEbc3371AE8d85', CREATE_NFT_ABI)
    times_to_do = random.randint(NFT_CREATE_AMOUNT[0], NFT_CREATE_AMOUNT[1])

    for i in range(times_to_do):

        logger.info(module_str)

        name = ' '.join([random.choice(WORDS) for _ in range(random.randint(1,3))]).title() # get random from `words.txt`
        symbol = ''.join([letter if letter not in 'aeiouy ' else '' for letter in name])[:3].upper() # get first consonants

        nft_price = int(random.randrange(100, 10000, 100) / 10 ** 8 * 10 ** 18) # from 0.000001 to 0.0001 ETH
        imageURI = get_random_nft()

        tx = contract.functions.createEdition(
            name,                           # name
            symbol,                         # symbol
            18446744073709551615,           # editionSize (const)
            random.randrange(100, 500, 50), # royaltyBPS
            address,                        # fundsRecipient
            address,                        # defaultAdmin
            (
                nft_price,                  # publicSalePrice
                random.randint(1,10000),    # maxSalePurchasePerAddress
                int(time.time()),           # publicSaleStart
                18446744073709551615,       # publicSaleEnd
                0,                          # presaleStart
                0,                          # presaleEnd
                '0x0000000000000000000000000000000000000000000000000000000000000000',# presaleMerkleRoot
            ),
            '',                             # description
            '',                             # animationURI
            imageURI,                       # imageURI
        )

        status = send_tx(pk, web3, tx, chain, module_str, check_text='create nft')

        if i != times_to_do - 1:
            sleeping(30, 60)

def change_random_option(pk, retry=0):
    def check_available():
        options = [
            change_main_info,
            airdrop_to_random_wallet,
            mint_own_nft,
            set_funds_recipient,
            change_description
        ]
        for module_name in list(AVAILABLE_MODULES.keys()):
            if AVAILABLE_MODULES[module_name] == False:
                for module in options:
                    if module.__name__ == module_name: options.remove(module)
        return options

    def change_main_info(collection_contract):
        """
        this func can change: Price and Max Sale Per Address
        """
        module_str = 'change main info'

        nft_price = int(random.randrange(100, 10000, 100) / 10 ** 8 * 10 ** 18)  # from 0.000001 to 0.0001 ETH
        created_time = collection_contract.functions.saleDetails().call()[3]

        tx = collection_contract.functions.setSaleConfiguration(
            nft_price,                  # publicSalePrice
            random.randint(1, 10000),   # maxSalePurchasePerAddress
            created_time,               # publicSaleStart
            18446744073709551615,       # publicSaleEnd
            0,                          # presaleStart
            0,                          # presaleEnd
            '0x0000000000000000000000000000000000000000000000000000000000000000', # presaleMerkleRoot
        )

        status = send_tx(pk, web3, tx, chain, module_str, check_text=module_str)

    def airdrop_to_random_wallet(collection_contract):
        module_str = 'airdrop nft'
        lucky_addresses = [Web3().eth.account.create().address for _ in range(random.randint(HOW_MANY_ADDRESSES_TO_DROP[0],HOW_MANY_ADDRESSES_TO_DROP[1]))]
        tx = collection_contract.functions.adminMintAirdrop(lucky_addresses)
        status = send_tx(pk, web3, tx, chain, module_str, check_text=module_str)

    def mint_own_nft(collection_contract):
        module_str = 'mint own nft'
        tx = collection_contract.functions.adminMint(address, random.randint(HOW_MANY_TO_MINT[0],HOW_MANY_TO_MINT[1]))
        status = send_tx(pk, web3, tx, chain, module_str, check_text=module_str)

    def set_funds_recipient(collection_contract):
        module_str = 'set funds recipient'
        tx = collection_contract.functions.setFundsRecipient(address)
        status = send_tx(pk, web3, tx, chain, module_str, check_text=module_str)

    def change_description(collection_contract):
        module_str = 'change description'
        text_to_description = ''.join([random.choice(ascii_letters + digits + ' ') for _ in range(random.randint(1,31))])

        description_contract = make_contract(web3, '0xCA7bF48453B72e4E175267127B4Ed7EB12F83b93', CHANGE_DESC_ABI)
        tx = description_contract.functions.updateDescription(collection_contract.address, text_to_description)
        status = send_tx(pk, web3, tx, chain, module_str, check_text=module_str)

    chain = 'zora'
    module_str = 'change random option'

    web3 = get_web3(chain, pk)
    address = web3.eth.account.from_key(pk).address

    collection_address = get_random_collection(address)
    if collection_address == False: return False
    collection_contract = make_contract(web3, collection_address, OWN_COLLECT_ABI)

    available_modules = check_available()

    '1-31 символа - дешево для описания'
    try:
        random.choice(available_modules)(collection_contract)
    except Exception as err:
        logger.warning(f'{module_str}{err}')
        list_send.append(f'{STR_CANCEL}{module_str}')
