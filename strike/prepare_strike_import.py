import csv
import sys
import uuid
import os.path
import datetime


# "Type","Buy","Cur.","Sell","Cur.","Fee","Cur.","Exchange","Group","Comment","Date","Tx-ID"
class Transaction:
    def __init__(self, type, buy, buy_currency, sell, sell_currency, fee, fee_currency, comment, date, tx_id):
        self.type = type
        self.buy = buy
        self.buy_currency = buy_currency
        self.sell = sell
        self.sell_currency = sell_currency
        self.fee = fee
        self.fee_currency = fee_currency
        self.exchange = "Strike"
        self.group = ""
        self.comment = comment
        self.date = date
        if len(tx_id) == 0:
            self.tx_id = uuid.uuid4()
        else:
            self.tx_id = tx_id

    def get_header():
        return f'"Type","Buy","Cur.","Sell","Cur.","Fee","Cur.","Exchange","Group","Comment","Date","Tx-ID"\n'

    def __str__(self):
        ret = f'"{self.type}",';
        if isinstance(self.buy, float):
            ret += f'"{self.buy:.8f}",'
        else:
            ret += f'"{self.buy}",'
        ret += f'"{self.buy_currency}",'
        if isinstance(self.sell, float):
            ret += f'"{self.sell:.8f}",'
        else:
            ret += f'"{self.sell}",'
        ret += f'"{self.sell_currency}",'
        if isinstance(self.fee, float):
            ret += f'"{self.fee:.8f}",'
        else:
            ret += f'"{self.fee}",'
        ret += f'"{self.fee_currency}",'
        ret += f'"{self.exchange}",'
        ret += f'"{self.group}",'
        ret += f'"{self.comment}",'
        ret +=f'"{self.date}",'
        ret += f'"{self.tx_id}"\n'
        return ret


def transaction_from_row(row):
    amount = float(row[4])
    currency = row[5]
    trans_type = ""
    date = datetime.datetime.strptime(row[1], "%Y-%m-%d %H:%M:%S")
    if (amount > 0 and currency == "BTC") or (amount < 0 and currency == "EUR"):
        trans_type = "Trade"
    elif amount > 0 and currency == "EUR":
        trans_type = "Deposit"
    elif amount < 0 and currency == "BTC":
        trans_type = "Withdrawal"

    trans = None
    if amount > 0:
        trans = Transaction(trans_type, amount, currency, "", "", float(row[6]), row[7], row[8], date, row[0])
    else:
        trans = Transaction(trans_type, "", "", abs(amount), currency, float(row[6]), row[7], row[8], date, row[0])

    return trans

# Transactions in Strike exports are separated like this:
#
# 28062cb0-20cc-4398-9b5e-1cea6c76e5ea,2024-07-23 16:30:13,Completed,Exchange,-49.36,EUR,0.64,EUR,
# 730ca2c7-6562-45a6-8f74-95a741f77a4e,2024-07-23 16:30:13,Completed,Exchange,0.00080587,BTC,0,BTC,
#
# We need to merge these into a single transaction
def merge_separated_trades(transaction1: Transaction, transaction2: Transaction):
    assert(transaction1.date == transaction2.date)
    assert(transaction1.exchange == transaction2.exchange)
    assert((transaction1.buy_currency == "BTC" and transaction2.sell_currency == "EUR") or (transaction1.sell_currency == "EUR" and transaction2.buy_currency == "BTC"))
    assert((transaction1.sell_currency == "EUR" and isinstance(transaction1.fee, float)) or (transaction2.sell_currency == "EUR" and isinstance(transaction2.fee, float)))

    buy_amount = transaction1.buy if transaction1.buy_currency == "BTC" else transaction2.buy
    sell_amount = transaction1.sell+transaction1.fee if transaction1.sell_currency == "EUR" else transaction2.sell+transaction2.fee
    fee = transaction1.fee if (isinstance(transaction1.fee, float) and float(transaction1.fee) != 0) else transaction2.fee

    return Transaction("Trade", buy_amount, "BTC", sell_amount, "EUR", fee, "EUR", transaction1.comment, transaction1.date, transaction1.tx_id)


if len(sys.argv) != 3:
    print("Usage: python prepare_strike_import.py <BTC transaction file> <EUR transaction file> [<output file>]")
    sys.exit(1)

# Open the file
btc_file = sys.argv[1]
eur_file = sys.argv[2]
if not os.path.exists(btc_file):
    print(f"File {btc_file} does not exist")
    sys.exit(1)
if not os.path.exists(eur_file):
    print(f"File {eur_file} does not exist")
    sys.exit(1)

transactions = []
with open(btc_file, "r") as btc_f, open(eur_file, "r") as eur_f:
    btc_reader = csv.reader(btc_f, delimiter=",")
    eur_reader = csv.reader(eur_f, delimiter=",")
    btc_reader.__next__()
    eur_reader.__next__()


    # "Type","Buy","Cur.","Sell","Cur.","Fee","Cur.","Exchange","Group","Comment","Date","Tx-ID"
    # Transaction ID,Time (UTC),Status,Transaction Type,Amount,Currency,Fee Amount,Fee Currency,Description
    for row in btc_reader:
        trans = transaction_from_row(row)
        transactions.append(trans)
    for row in eur_reader:
        trans = transaction_from_row(row)
        transactions.append(trans)

sorted_transactions = sorted(transactions, key=lambda x: x.date)
for (i, trans) in enumerate(sorted_transactions):
    if trans is None:
        continue
    if i < len(sorted_transactions) - 1:
        if sorted_transactions[i].date == sorted_transactions[i+1].date:
            merged = merge_separated_trades(sorted_transactions[i], sorted_transactions[i+1])
            sorted_transactions[i] = merged
            sorted_transactions[i+1] = None

sorted_transactions.remove(None)

out_file = sys.argv[3] if len(sys.argv) == 4 else "strike_export.csv"
with open(out_file, "w") as out_f:
    out_f.write(str(Transaction.get_header()))
    out_f.writelines(map(lambda t: str(t), sorted_transactions));

# for trans in sorted_transactions:
#     print(trans)

print(f"Output written to {out_file}")
