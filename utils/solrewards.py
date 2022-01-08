#!/opt/local/bin/python

import argparse
from solana.rpc.api import Client
import requests
import json
import dateutil.parser
from datetime import *

LPERS = 1000000000

parser = argparse.ArgumentParser(description='Show Solana staking rewards by epoch. Pass in one or more staking account addresses (csv if more than one) and either a beginning epoch number and optional end epoch number (uses last complete epoch of end epoch is not defined) or a year to calculate for all epochs in a year. Displays a simpe total of all rewards for the perion (in SOL) along withm if verbose output is specified, rewards per epoch.')
epoch_group = parser.add_argument_group('epoch-based', 'Specify range by epochs')
date_group = parser.add_argument_group('date-based', 'Specify range by year')
parser.add_argument("-ad", "--addresses", type=str, required=True, help="Staking account address, csv if more than one")
parser.add_argument("-v", "--verbose", action="store_true", help="Print rewards per epoch as well as final amount for all epochs")
date_group.add_argument("-yr", "--year", type=int, choices=[2021,2022], help="Year to return rewards for, only 2021 and 2022 currently supported")
epoch_group.add_argument("-be", "--beginepoch", type=int, help="Beginning epoch number")
epoch_group.add_argument("-ee", "--endepoch", type=int, help="End epoch number, defaults to most recent completed epoch if omitted")
args = parser.parse_args()

# Manual year->begin/end epoch mapping - this is too messy and slow to determine dynamically
epochyears = {2021: [135,263], 2022: [264,None]}

client = Client("https://api.mainnet-beta.solana.com")
api = 'https://api.mainnet-beta.solana.com'

ads = args.addresses.split(',')
curr_epoch = client.get_epoch_info()["result"]["epoch"]

# Use year if preferred
if args.year:
  be = epochyears[args.year][0]
  if epochyears[args.year][1]:
    ee = epochyears[args.year][1]
  else:
    ee = curr_epoch
else:
  be = args.beginepoch
  if not args.endepoch:
    ee = curr_epoch
  else:
    ee = args.endepoch

def get_reward_for_epoch(ads, epoch):
  # Missing in python API lib so have to do this manually with JSON RPC

  body=f"""{{
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getInflationReward",
        "params": [
           [{",".join(list(map(lambda a:'"%s"' % a,ads)))}], {{"epoch": {epoch}}}
        ]
      }}
  """
  
  r = requests.post(api, headers={"Content-Type": "application/json"}, json=json.loads(body))
  return r.json()["result"]

rewards = {}

for e in range(be, ee+1):
  if args.verbose:
    print(f"{e}:", end='')
  rewards.setdefault(e, 0)
  for r in get_reward_for_epoch(ads, e):
    if r is None:
      continue
    if r["amount"]:
      rewards[e] += r["amount"] / LPERS # convert to SOL
  if args.verbose:
    print(f"{rewards[e]}")

print(f"Total:{sum(rewards.values())}")



