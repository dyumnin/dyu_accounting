import sys
import pandas as pd
import argparse


parser = argparse.ArgumentParser(
    description='Convert Bank Statement to beancount file')
parser.add_argument('--bank', choices="idfc icici".split(),
                    help="Name of Bank")
parser.add_argument('--type', choices="cc bank".split(),
                    help="Type of Statement, credit card, bank etc.")
parser.add_argument('--skip_row', type=int, help="Rows to skip, Zero indexed")
parser.add_argument('--date_col', type=int,
                    help="Column containing Transaction Date, zero indexed")
parser.add_argument('--infile', nargs=1)
parser.add_argument('--outfile', nargs=1, type=argparse.FileType('w'))
args = parser.parse_args()
print(args)

print("All numbers are 0 indexed")
# stmt_type = int(input("Statement type:\n1:CC\n2:Bank\n"))
# skip_row = int(input("Number of Rows to skip"))
# date_col = int(input("Col# containing TXN Date"))
# outfile = input("Output file")
print(f"file={args.infile[0]}")
cc = pd.read_excel(
    args.infile[0], skiprows=args.skip_row,
    header=0)
# with open(args.outfile[0], 'w') as of:
if 1:
    of = args.outfile[0]

    # ICICI Credit Card Statement Processing
    if args.bank == 'icici':
        if args.type == 'cc':
            for i, r in cc.iterrows():
                if not pd.isnull(r[0]):
                    txn_date = pd.to_datetime(r[1]).strftime("%Y-%m-%d")
                    of.write(
                        f'{txn_date} * " {r[3]}"\n')
                    if r[0] == 'i':
                        of.write(f'\tExpenses:INR:Internet {r[6]} INR\n')
                    elif r[0] == 'm':
                        of.write(f'\tExpenses:INR:Phone {r[6]} INR\n')
                    else:
                        of.write(f'\tExpenses:INR:Misc {r[6]} INR\n')

                    of.write('\tLiabilities:INR:CreditCard\n\n')

    # ICICI Bank Statement Processing
        if args.type == 'bank':
            for i, r in cc.iterrows():
                if not pd.isnull(r[0]):
                    txn_date = pd.to_datetime(r[3]).strftime("%Y-%m-%d")
                    print(r[3])
                    of.write(f'{txn_date} * " {r[5]}" "{r[0]}"\n')
                    of.write(f'\tExpenses:INR:Misc {r[6]} INR\n')

                    of.write('\tLiabilities:INR:CEOBank\n\n')
    # IDFC Bank Statement Processing
    if args.bank == 'idfc':
        if args.type == 'bank':
            for i, r in cc.iterrows():
                print(f'--------{r[0]}----')
                if not pd.isnull(r[0]):
                    txn_date = pd.to_datetime(r[0]).strftime("%Y-%m-%d")
                    of.write(f'{txn_date} * " {r[2]}"\n')
                    if not pd.isnull(r[4]):  # Debit
                        of.write(f'\tExpenses:INR:Misc {r[4]} INR\n')
                    else:
                        of.write(f'\tAssets:INR:AccountReceivable -{r[5]} INR\n')

                    of.write('\tAssets:INR:Bank\n\n')
