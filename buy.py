import os
from web3 import Web3
from dotenv import load_dotenv

load_dotenv()

BASE_RPC = os.getenv("BASE_RPC")
WALLET_ADDRESS = os.getenv("WALLET_ADDRESS")
PRIVATE_KEY = os.getenv("PRIVATE_KEY")
UNISWAP_ROUTER = os.getenv("UNISWAP_ROUTER")
BUY_AMOUNT = float(os.getenv("BUY_AMOUNT"))

w3 = Web3(Web3.HTTPProvider(BASE_RPC))

router_abi = '[{"inputs":[{"internalType":"address","name":"token","type":"address"},{"internalType":"uint256","name":"amountOutMin","type":"uint256"},{"internalType":"uint256","name":"amountInMax","type":"uint256"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"exactInputSingle","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"payable","type":"function"}]'
router = w3.eth.contract(address=UNISWAP_ROUTER, abi=router_abi)

def buy_token(token_address):
    amount = w3.to_wei(BUY_AMOUNT, 'ether')
    tx = router.functions.exactInputSingle(token_address, 0, amount, WALLET_ADDRESS, (w3.eth.get_block('latest').timestamp + 60)).build_transaction({
        'from': WALLET_ADDRESS,
        'value': amount,
        'gas': 300000,
        'gasPrice': w3.eth.gas_price,
        'nonce': w3.eth.get_transaction_count(WALLET_ADDRESS)
    })
    signed_tx = w3.eth.account.sign_transaction(tx, PRIVATE_KEY)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
    print(f"Bought token: {token_address}, tx: {tx_hash.hex()}")
