import os
import json
import pandas as pd
from typing import Tuple

def get_account(name, platform):
    pass

def get_portfolio(name, platform):
    pass

def get_orders(key):
    pass

def get_open_orders(key):
    pass

def get_trades(key):
    pass

def get_position(key):
    pass

def get_balance(key):
    pass



def get_client_account(key) -> Tuple[str, str]:
    """returns the parent account of the client_key"""
    account, platform = tblob.load.map("clients").content[key]
    return account, platform

def get_credentials(account, platform):
    """returns the credentials for the account"""
    cred_path = os.path.join(
        os.getenv("CREDENTIALS_DIR", ""),
        f"{platform}-{account}",
        "key.json"
    )
    with open(cred_path) as f:
        creds = json.load(f)
        return creds

def get_order_owner (order_id: str, platform: str, account: str):
    """finds and returns the client key that placed this order"""
    #use tblob.load.map("orders") for order_id: client_key hash table
    tb = tblob.load.map("orders", platform).content
    return tb.get(order_id, f"{platform}-{account}-default")

def update_orders(orders: list, account, platform: str):
    """updates the orders table with the new orders"""
    df = pd.DataFrame(orders)
    df.set_index("orderId", inplace=True)
    df['client'] = df.apply(lambda x: get_order_owner(x.name, platform, account), axis=1)
    grouped = df.groupby("client")
    for client, group in grouped:
        group.drop(columns=["client"], inplace=True)
        tb = tblob.load.orders(client).content
        prev_orders = tb
        prev_df = pd.DataFrame(prev_orders)
        prev_df.set_index("orderId", inplace=True)
        prev_df = prev_df[~prev_df.index.isin(group.index)]
        new_df = pd.concat([prev_df, group])
        new_df.reset_index(inplace=True)
        rows = new_df.to_dict(orient="records")
        input("check if cols are preserverd (order_id)")
        tb.content = rows
        tb.save()


def set_position(client_key: str, asset: str, ammount: float, timestamp: float = 0):
    """sets a custom position of the asset at a given timestamp, recent
    position is calculated using orders that are updated after the
    timestamp"""
    tb = tblob.edit.position(client_key)
    tb.content[asset] = {"ammount": ammount, "timestamp": int(timestamp)}
    tb.save()

def get_orders(client_key: str, pairs = None, status = None):
    all_orders = tblob.load.orders(client_key).content
    orders = list(
            filter(
            lambda x:
                (not status or x["status"] == status)
                and (not pairs or x["pair"] in pairs),
            all_orders
        )
    )
    return orders

def get_position(client_key: str, assets: list = []):
    """returns the balance for the given client_key and assets using
    the orders table and pre-set balance"""
    orders = tblob.load.orders(client_key).content
    ammount_holding = calculate_ammount_holding(orders)
    deposits = tblob.load.deposits(client_key).content

    position = {}
    for asset in assets:
        deposit = deposits.get(asset, 0)
        holding = ammount_holding.get(asset, {"full": deposit, "locked": 0})
        holding["free"] = holding["full"] - holding["locked"]
        position[asset] = holding
    return position


def calculate_ammount_holding(orders: list):
    df = pd.DataFrame(orders)
    #filter out filled and partially filled orders
    #seperate pairs
    df['base'] = df.apply(lambda x: x.pair.split("/")[0], axis=1)
    df['quote'] = df.apply(lambda x: x.pair.split("/")[1], axis=1)
    df['sign'] = df.apply(lambda x: 1 if x.side == "BUY" else -1, axis=1)
    df['base_ammount'] = df.apply(lambda x: x.sign * x.filled_qty, axis=1)
    df['quote_ammount'] = df.apply(lambda x: -x.sign * x.filled_quote_qty, axis=1)
    df['remaining_amount'] = df.apply(lambda x: (x.qty - x.filled_qty) if x.status == "WORKING" and x.price > 0 else 0, axis=1)
    df['locked_asset'] = df.apply(lambda x: x.base if x.side == 'BUY' else x.quote, axis=1)
    df['locked_ammount'] = df.apply(lambda x: x.remaining_amount * x.price if x.side == 'BUY' else x.remaining_amount, axis=1)

    base_df = df[['base', 'base_ammount']].groupby("base").sum()
    quote_df = df[['quote', 'quote_ammount']].groupby("quote").sum()
    locked_df = df[['locked_asset', 'locked_ammount']].groupby("locked_asset").sum()
    holding = {}
    for base in base_df.index:
        if base not in holding:
            holding[base] = {"full": 0, "locked": 0}
        holding[base]["full"] += base_df.loc[base].base_ammount
    for quote in quote_df.index:
        if quote not in holding:
            holding[quote] = {"full": 0, "locked": 0}
        holding[quote]["full"] += base_df.loc[quote].base_ammount
    for asset in locked_df.index:
        holding[asset]["locked"] += locked_df.loc[asset].locked_ammount
    return holding

def get_involved_pairs(client_key: str):
    """returns a list of pairs that the client_key owned at some point"""
    tb = tblob.load.orders(client_key).content
    df = pd.DataFrame(tb)
    return df.pair.unique().tolist()

def get_clients(name, platform):
    """returns a list of client_keys"""
    acc = tblob.load.account(name, platform).content
    return acc["clients"]


