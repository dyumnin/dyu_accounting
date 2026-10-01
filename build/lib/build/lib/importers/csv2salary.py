with open("salary.csv", 'r') as csv:
    for idx, line in enumerate(csv):
        if idx > 0:
            r = line.split(',')
            print(f"2017-07-01 open Expenses:INR:Salary:{r[1]}     INR")
            for i in range(12):
                print(f'2019-{1+((i)%12)}-01 * "Salary {r[1]}"')
                print(f'\tExpenses:INR:Salary:{r[1]}')
                print('\tLiabilities:INR:ProfessionalTax 200 INR')
                print(f'\tLiabilities:INR:TDS {float(r[2+i])*0.1} INR')
                print(f'\tAssets:INR:Bank:Current -{float(r[2+i])} INR')

with open("sales.csv", 'r') as csv:
    for idx, line in enumerate(csv):
        if idx > 0:
            r = line.split(',')
            print(f"2017-07-01 open Income:INR:{r[1]}     INR")
            for i in range(12):
                print(f'2019-{1+((i)%12)}-01 * "Sales to {r[1]}"')
                print(f'\tIncome:INR:{r[1]} -{float(r[2+i])} INR')
                print(f'\tLiabilities:INR:GST:IGST  {float(r[2+i])*0.2}INR')
                print('\tAssets:INR:Bank:Current')
