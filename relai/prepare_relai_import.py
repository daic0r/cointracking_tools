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
        self.exchange = "Relai"
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


#    transactionType,date,outSellAmount,outSellAsset,inBuyAmount,inBuyAsset,feeAmount,feeAsset,fixedFee,fixedFeeAsset,operationId
#    trade,2023-05-10T10:37:35Z,150,EUR,0.00589831,BTC,1.5,EUR,0, - ,b06786a1-d6ea-4a83-9042-ad9f6b93597b
def transaction_from_row(row):
    date = datetime.datetime.strptime(row[1], "%Y-%m-%dT%H:%M:%SZ")

    trans_deposit = Transaction("Deposit", float(row[2]), row[3], "", "", 0.0, row[3], "", date - datetime.timedelta(seconds=1), str(uuid.uuid4()))
    trans_trade = Transaction("Trade", float(row[4]), row[5], float(row[2]), row[3], float(row[6]), row[7], "", date, row[10])
    return (trans_deposit, trans_trade)

if len(sys.argv) != 2:
    print("Usage: python prepare_relai_import.py <Transaction file> [<output file>]")
    sys.exit(1)

# Open the file
trans_file = sys.argv[1]
if not os.path.exists(trans_file):
    print(f"File {trans_file} does not exist")
    sys.exit(1)

transactions = []
with open(trans_file, "r") as trans_f:
    trans_reader = csv.reader(trans_f, delimiter=",")
    trans_reader.__next__()


    # "Type","Buy","Cur.","Sell","Cur.","Fee","Cur.","Exchange","Group","Comment","Date","Tx-ID"

    for row in trans_reader:
        (trans_deposit, trans_trade) = transaction_from_row(row)
        transactions.append(trans_deposit)
        transactions.append(trans_trade)

out_file = sys.argv[3] if len(sys.argv) == 4 else "relai_export.csv"
with open(out_file, "w") as out_f:
    out_f.write(str(Transaction.get_header()))
    out_f.writelines(map(lambda t: str(t), transactions));

# for trans in transactions:
#     print(trans)

print(f"Output written to {out_file}")
