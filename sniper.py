import os, time, requests
from web3 import Web3
from dotenv import load_dotenv
from buy import buy_token
from utils import check_honeypot, get_liquidity

load_dotenv()

BASE_RPC = os.getenv("BASE_RPC")
WALLET_ADDRESS = os.getenv("WALLET_ADDRESS")
PRIVATE_KEY = os.getenv("PRIVATE_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

w3 = Web3(Web3.HTTPProvider(BASE_RPC))
telegram_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

def send_telegram(msg):
    requests.post(telegram_url, data={"chat_id": TELEGRAM_CHAT_ID, "text": msg})

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

                    # Honeypot check
                    safe = check_honeypot(w3, address, WALLET_ADDRESS)
                    # Liquidity check
                    liquidity = get_liquidity(address)

                    if not safe:
                        send_telegram(f"⚠ Honeypot Detected, Skipping!\n{address}")
                        continue
                    if liquidity < 5:
                        send_telegram(f"⚠ Low Liquidity (<5 ETH), Skipping!\n{address}")
                        continue

                    msg = f"New Safe Token:\nName: {name}\nSymbol: {symbol}\nDecimals: {decimals}\nAddress: {address}\nLiquidity: {liquidity} ETH"
                    print(msg)
                    send_telegram(msg)

                    # Auto-buy
                    buy_token(address)

                except Exception as e:
                    print(f"Not ERC20 or error: {e}")
        time.sleep(2)

if __name__ == "__main__":
    detect_new_tokens()
