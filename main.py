from utils import *
from config import list_send
"""
---
"""

if __name__ == '__main__':

    update_name(on_welcome=True)
    if RANDOM_WALLETS:  random.shuffle(p_keys)

    PATH = pick_path()

    for index in range(len(p_keys)):
        try:

            list_send.clear()
            pk = p_keys[index]
            #change_proxy()

            print('')
            text_ = f'[{index+1}/{len(p_keys)}] {Web3().eth.account.from_key(pk).address}'
            logger.info(text_)
            list_send.append(f'{text_}\n')
            update_name(account_num=index+1)


            ############### withdraw + bridge ###############
            if PATH in '12':
                zora_old_balance = check_balance(pk, 'zora')
                eth_balance = check_balance(pk, 'eth')

                if eth_balance < MIN_ETH_BALANCE:
                    if PATH == '1':
                        okx_withdraw(pk, 'ERC20', eth_balance)
                        wait_balance(pk, 'eth', eth_balance + 0.0001)
                        sleeping(20,40)
                    elif PATH == '2':
                        text_log = f'no funds in ETH to bridge ({eth_balance} ETH)'
                        list_send.append(f'{STR_CANCEL}{text_log}')
                        logger.error(text_log)
                        continue

                if not deposit_to_zora(pk): continue
                wait_balance(pk, 'zora', zora_old_balance+0.0001)
                sleeping(20, 40)


            ##################### modules #####################
            modules = [
                mint_nft,
                create_nft
            ]
            random.shuffle(modules)

            for module in modules:
                try:
                    module(pk)
                except Exception as err:
                    logger.error(f'{module.__name__} error: {err}')
                finally:
                    sleeping(20,40)

            for _ in range(random.randint(NFT_CHANGE_INFO[0], NFT_CHANGE_INFO[1])):
                try:
                    change_random_option(pk)
                except Exception as err:
                    logger.error(f'{module.__name__} error: {err}')
                finally:
                    sleeping(20, 40)


        except Exception as err:
            logger.error(f'GLOBAL ERROR: {err}')

        finally:
            send_msg(list_send)

    logger.success(f'ALL ACCS DONE\nPress Enter to exit...\n')
    input()


