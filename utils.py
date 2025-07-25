from web3 import Web3
import requests

def check_honeypot(w3, token_address, wallet):
    try:
        token_abi = [
            {"constant": False, "inputs": [{"name": "_to", "type": "address"}, {"name": "_value", "type": "uint256"}], "name": "transfer", "outputs": [{"name": "", "type": "bool"}], "type": "function"},
        ]
        token = w3.eth.contract(address=token_address, abi=token_abi)
        token.functions.transfer(wallet, 1).estimate_gas({'from': wallet})
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
    res = requests.post(url, json={"query": query})
    try:
        eth_liq = float(res.json()['data']['pools'][0]['totalValueLockedETH'])
        return eth_liq
    except:
        return 0.0
