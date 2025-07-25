import os, time, requests
from web3 import Web3
from dotenv import load_dotenv

# ========== CONFIG ==========
# .env values directly yaha paste karo ya .env file rakho aur load_dotenv() use karo
BASE_RPC = "https://mainnet.base.org"
WALLET_ADDRESS = "0xYourWalletAddress"
PRIVATE_KEY = "your_private_key"
TELEGRAM_TOKEN = "your_telegram_bot_token"
TELEGRAM_CHAT_ID = "your_chat_id"
UNISWAP_ROUTER = "0x2626664c2603336E57B271c5C0dCE69c6E7aA1D2"
BUY_AMOUNT = 0.01   # ETH me

# ========== INIT ==========
w3 = Web3(Web3.HTTPProvider(BASE_RPC))
telegram_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

router_abi = '[{"inputs":[{"internalType":"address","name":"token","type":"address"},{"internalType":"uint256","name":"amountOutMin","type":"uint256"},{"internalType":"uint256","name":"amountInMax","type":"uint256"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"exactInputSingle","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"payable","type":"function"}]'
router = w3.eth.contract(address=UNISWAP_ROUTER, abi=router_abi)

# ========== UTILS ==========
def send_telegram(msg):
    try:
        requests.post(telegram_url, data={"chat_id": TELEGRAM_CHAT_ID, "text": msg})
    except Exception as e:
        print("Telegram Error:", e)

def check_honeypot(token_address):
    try:
        token_abi = [
            {"constant": False, "inputs": [{"name": "_to", "type": "address"}, {"name": "_value", "type": "uint256"}], 
             "name": "transfer", "outputs": [{"name": "", "type": "bool"}], "type": "function"}
        ]
        token = w3.eth.contract(address=token_address, abi=token_abi)
        token.functions.transfer(WALLET_ADDRESS, 1).estimate_gas({'from': WALLET_ADDRESS})
        return True
    except:
        return False

def get_liquidity(token_address):
    url = "https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v3"
    query = """
    {
      pools(first:1, where: {token0: "%s"}) {
        totalValueLockedETH
      }
    }
    """ % token_address.lower()
    try:
        res = requests.post(url, json={"query": query})
        eth_liq = float(res.json()['data']['pools'][0]['totalValueLockedETH'])
        return eth_liq
    except:
        return 0.0

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
    send_telegram(f"✅ Bought token: {token_address}\nTx: {tx_hash.hex()}")

# ========== MAIN LOOP ==========
def detect_new_tokens():
    latest_block = w3.eth.block_number
    print(f"Starting from block: {latest_block}")
    while True:
        block = w3.eth.get_block('latest', full_transactions=True)
        for tx in block.transactions:
            if tx.to is None:  # contract deployment
                receipt = w3.eth.get_transaction_receipt(tx.hash)
                address = receipt.contractAddress
                try:
                    abi = [
                        {"constant": True, "inputs": [], "name": "symbol", "outputs": [{"name": "", "type": "string"}], "type": "function"},
                        {"constant": True, "inputs": [], "name": "name", "outputs": [{"name": "", "type": "string"}], "type": "function"},
                        {"constant": True, "inputs": [], "name": "decimals", "outputs": [{"name": "", "type": "uint8"}], "type": "function"},
                    ]
                    token_contract = w3.eth.contract(address=address, abi=abi)
                    symbol = token_contract.functions.symbol().call()
                    name = token_contract.functions.name().call()
                    decimals = token_contract.functions.decimals().call()

                    # Filters
                    if not check_honeypot(address):
                        send_telegram(f"⚠ Honeypot Token Skipped: {address}")
                        continue
                    liquidity = get_liquidity(address)
                    if liquidity < 5:
                        send_telegram(f"⚠ Low Liquidity (<5 ETH) Token Skipped: {address}")
                        continue

                    msg = f"New Safe Token:\nName: {name}\nSymbol: {symbol}\nDecimals: {decimals}\nAddress: {address}\nLiquidity: {liquidity} ETH"
                    print(msg)
                    send_telegram(msg)

                    # Auto Buy
                    buy_token(address)

                except Exception as e:
                    print(f"Error reading token: {e}")
        time.sleep(2)

if __name__ == "__main__":
    detect_new_tokens()
