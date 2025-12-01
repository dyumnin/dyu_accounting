import datetime
import random
from dateutil.relativedelta import relativedelta
start_date = datetime.date(2019, 4, 1)
employees = [
    {'name': 'Amar', 'salary': 10000, "joining": datetime.date(2019, 4, 1)},
    {'name': 'Akbar', 'salary': 25000,
     "joining": datetime.date(2019, 5, 1)},
    {'name': 'Anthony', 'salary': 15000, "joining": datetime.date(2019, 9, 1)},
    {'name': 'John', 'salary': 17000, "joining": datetime.date(2019, 12, 1)},
    {'name': 'Jaani', 'salary': 27000, "joining": datetime.date(2020, 1, 1)},
    {'name': 'Janardhan', 'salary': 27000,
        "joining": datetime.date(2020, 3, 1)},
    {'name': 'Ram', 'salary': 29000, "joining": datetime.date(2020, 6, 1)},
    {'name': 'Rahim', 'salary': 19000, "joining": datetime.date(2020, 7, 1)},
    {'name': 'Ramona', 'salary': 29000, "joining": datetime.date(2020, 8, 1)},
    {'name': 'Kabir', 'salary': 49000, "joining": datetime.date(2020, 9, 1)}
]

for e in employees:
    print(f'{e["joining"]} open Expenses:INR:Salary:{e["name"]}')
    print(f"""
{e['joining']} * "VendorZ" "{e['name']} Joining Package"
    Assets:INR:Equipment:Laptop 40000 INR ; Laptop
    Assets:INR:Equipment:Furniture 10000 INR ; Table
    Assets:INR:Equipment:Furniture 7000 INR ; Chair
    Assets:INR:GST:ITC:CGST      5000        INR
    Assets:INR:GST:ITC:SGST      5000        INR
    Liabilities:INR:AccountPayable:Vendor:Z
{e['joining']+datetime.timedelta(days=5)} * "Payment for {e['name']} Joining Package"
    Assets:INR:Bank:Current -57000 INR
    Liabilities:INR:AccountPayable:Vendor:Z
        """)

    # Salary
    for i in range(40):
        payday = e['joining']+relativedelta(months=+i, days =+29)
        print(f"""
{payday} * "{e['name']}" "Salary for {payday}"
    Assets:INR:Bank:Current -{e['salary']} INR
    Liabilities:INR:ProfessionalTax 200 INR
    Liabilities:INR:TDS {0.1 * e['salary']} INR
    Expenses:INR:Salary:{e['name']}
            """)
        compli_day = e['joining']+relativedelta(months=+i, days =+32)
        print(f"""
{compli_day} * "{e['name']}" "compliance"
    Liabilities:INR:ProfessionalTax -200 INR
    Liabilities:INR:TDS -{0.1 * e['salary']} INR
    Expenses:INR:GOK  200 INR
    Expenses:INR:GOI  {0.1 * e['salary']}  INR
            """)

    pass
for i in range(12):
    x_buydate = start_date + relativedelta(months=+i)
    #quant = "{ %d INR}" % (random.randint(1, 10))
    quant = "{ 1000 INR}"

    print(f"""
{x_buydate} * "VendorX" "Nuts {x_buydate}"
    Assets:NUTS:Equipment:Consumable 1 NUTS {quant}
    Liabilities:INR:AccountPayable:Vendor:X
    Liabilities:INR:GST:CGST      102        INR
    Liabilities:INR:GST:SGST      102        INR
    """)
    y_buydate = start_date + relativedelta(months=+i,days=2)
    #quant = "{ %d INR}" % (random.randint(1, 10))
    quant = "{ 1000 INR}"

    print(f"""
{y_buydate} * "VendorY" "Bolts {x_buydate}"
    Assets:BOLTS:Equipment:Consumable 1 BOLTS {quant}
    Liabilities:INR:AccountPayable:Vendor:Y
    Liabilities:INR:GST:CGST      102        INR
    Liabilities:INR:GST:SGST      102        INR
    """)
    # Manufacture
    c_buydate = start_date + relativedelta(months=+i,days=20)
    #quant = "{ %d INR}" % (random.randint(1, 10))
    quant2 = "{ 2000 INR}"
    equ="{}"

    print(f"""
{y_buydate} * "Manufacture" "1 Unit built {y_buydate}"
    Assets:BOLTS:Equipment:Consumable -1 BOLTS {equ}
    Assets:NUTS:Equipment:Consumable -1 NUTS {equ}
    Assets:NUTBOLT:Equipment:Consumable 1 NUTBOLT {quant2}
    """)
    print(f"""
{c_buydate} * "Sale" "Sale 1 Unit {c_buydate}"
    Assets:NUTBOLT:Equipment:Consumable -1 NUTBOLT {equ}
    Assets:INR:AccountReceivable 2500 INR
    Liabilities:INR:GST:CGST      212        INR
    Liabilities:INR:GST:SGST      212        INR
    Income:Customer:C
    """)
    print(f"""
{c_buydate+ relativedelta(days=+20) } * "Check" "Sales Income {c_buydate}"
    Assets:INR:AccountReceivable -2500 INR
    Assets:INR:Bank:Current
{c_buydate+ relativedelta(days=+21) } * "Payment" "Vendor bill cleared"
    Assets:INR:Bank:Current
    Liabilities:INR:AccountPayable:Vendor:X 1000 INR
    Liabilities:INR:AccountPayable:Vendor:Y 1000 INR


    """)
