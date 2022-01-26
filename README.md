# Accounting setup to automate generation of various financial statements for Compliance with Indian Govt.
This setup is built over the beancount plain text accounting system. For details check https://beancount.github.io/docs/index.html

This is an opionionated opensource setup for maintaining the book of accounts and generating financial statements and reports as required by GOI.

Currently the following financial statements are supported.

1. Balance Sheet.
2. Profit and Loss Statements
3. Account Statement
4. Depreciation calculation as per MCA WDV and IT SLM Method.
 
There is an example account in the example folder, the generated report can be seen here [FY 2019 Report](example/reports_fy_2019.pdf)

Note: 

1. These scripts work for me and my Company, Based on the rules applicable to your organisation, you may have to tweak the results.
2. I am an engineer not a CA. **Always get the output audited by your auditor.** 


# Installation

```
pip3 install dyu_accounting
```

For the latest, untested version you can install from this git repo.
```
git clone <repo name>
cd <repo name>
pip install .
```

# Generation reports

Once you have installed this package and generated a compliant Accounting file (see example directory) you can generate the required reports by running 

```
mkdir reports/2019
account --in ledger.beancount --fy 2019 --out reports/2019/  
```

# Example

The example folder contains a sample book of accounts dealing with

1. Salary and deductions like TDS, PF etc.
2. Purchase of long term Assets
3. Purchase of Goods.
3. Sale of Goods.
4. GST
5. Depreciation


## Setting up your chart of accounts for use with this package.
The program picks details of your charts of accounts from two sources

1. `config.json` This file should be in the folder from where the script is invoked, It sets the various report generation options.
2. The attributes specified while opening an account. These attributes are used to classify the account in different categories while generating balance sheet or calculating depreciation.

The attributes used to associate an account with a balance, specified as `balance_sheet: "attribute"` sheet item are as follows.
		
* liabilities.share_capital' 
* liabilities.surplus'                   
* liabilities.longterm_borrowing'        
* liabilities.deferred_tax'              
* liabilities.longterm_liability'        
* liabilities.longterm_provisions'       
* liabilities.shortterm_borrowing'       
* liabilities.trade_payable'             
* liabilities.other_current_liabilities' 
* liabilities.shortterm_provisions'      
* assets.non_current'                    
* assets.fixed'                          
* assets.tangible'                       
* assets.intangible'                     
* assets.wip_capital'                    
* assets.intangile_wip'                  
* assets.investments_non_current'        
* assets.deferred_tax'                   
* assets.longterm_loan'                  
* assets.other_non_current'              
* assets.investments'                    
* assets.inventory'                      
* assets.trade_receivables'              
* assets.cash'                           
* assets.shortterm_loans'                
* assets.misc_current'                   

The attributes used to specify the depreciation category of an account is as follows

| Attribute       | IT Block  | MCA life | MCA wdv % | slm %   | it_wdv % |
| ----            | ----      | ----     | ----      | ----    | ----     |
| Furniture       | furniture | 10       | (25.88)   | (9.5)   | (10)     |
| OfficeEquipment | furniture | 5        | (45.07)   | (19.00) | (10)     |
| Phone           | phone     | 5        | (45.07)   | (19.00) | (15)     |
| Server          | laptop    | 6        | (39.3)    | (15)    | (40)     |
| Laptop          | laptop    | 3        | (63.16)   | (31.67) | (40)     |
| Electrical      | furniture | 10       | (25.88)   | (9.50)  | (10)     |

# GST Scheme

## Setup

Create one or more accounts matching the following pattern

* `Assets.*GST` for GST Paid on inward supplies
* `Liabilities.*GST` for GST Collected on outward supplies
 
# Balance Sheet

This module follows the new Balance Sheet format at https://cleartax.in/s/balance-sheet/

# TODO

## Electronic Report Generation.

* Departments like MCA, IT, GST, TDS have the facility to generate report in a structured format (e.g. JSON or XML) and upload it to their portal.
* At some point in the future we will generate reports in these Offline upload formats.
* A known problem with these formats is, they are not frozen, the department periodically issues new revisions. So while coding the report generation for a given format is trivial, Keeping track or frequent format changes and ensuring that they are in sync with latest revision is a chore.

## Interface with external database.

We typically have different databases for different purpose,
e.g.
1. Employee information will be in HR and Payroll database.
2. Inventory will be in Inventory management system
3. Bank, Credit card and Wallet Transactions are in the reports generated by those financial entities.

We should be able to automatically import entries match them with each other and write out a beancount file.


# KNPS:

* MCA Depreciation considers the entire year and not the actual days in use.

# Contribution

If you have a background in accounting and are interested in enhancing this application raise a ticket and we can discuss.
