= Balance Sheet for FY {{cfg.fy}}
:company: {{cfg.company.name}}

== Balance Sheet as on 31 March {{cfg.fy+1}}

// https://cleartax.in/s/balance-sheet/
[options="header",cols="4,1,2,2"]
|===
| Particulars | Note No. | {{cfg.fy}}-{{cfg.fy+1}} | {{cfg.fy-1}}-{{cfg.fy}}

h| I. EQUITY AND LIABILITIES | | |
h| 1) Shareholder's Funds | | |
| (a) Share Capital | 1 | {{account.liabilities.share_capital|money}} | {{prev_account.liabilities.share_capital|money}}
| (b) Reserves and Surplus | | {{account.liabilities.surplus|money}} | {{prev_account.liabilities.surplus|money}}
| (c) Money received against share warrants | | |
h| (2) Share application money pending allotment | | |
h| (3) Non-Current Liabilities | | |
| (a) Long-term borrowings | | {{account.liabilities.longterm_borrowing|money}} | {{prev_account.liabilities.longterm_borrowing|money}}
| (b) Deferred tax liabilities (Net) | | {{account.liabilities.deferred_tax|money}} | {{prev_account.liabilities.deferred_tax|money}}
| (c) Other Long term liabilities | | {{account.liabilities.longterm_liability|money}} | {{prev_account.liabilities.longterm_liability|money}}
| (d) Long term provisions | | {{account.liabilities.longterm_provisions|money}} | {{prev_account.liabilities.longterm_provisions|money}}
h| (4) Current Liabilities | | |
| (a) Short-term borrowings | 2 | {{account.liabilities.shortterm_borrowing|money}} | {{prev_account.liabilities.shortterm_borrowing|money}}
| (b) Trade payables | | {{account.liabilities.trade_payable|money}} | {{prev_account.liabilities.trade_payable|money}}
| (c) Other current liabilities | | {{account.liabilities.other_current_liabilities|money}} | {{prev_account.liabilities.other_current_liabilities|money}}
| (d) Short-term provisions | | {{account.liabilities.shortterm_provisions|money}} | {{prev_account.liabilities.shortterm_provisions|money}}
h| Total | | {{account.liabilities.total|money}} | {{prev_account.liabilities.total|money}}
h| II. Assets | | |
h| (1) Non-current assets | | {{account.assets.non_current|money}} | {{prev_account.assets.non_current|money}}
| (a) Fixed assets | | {{account.assets.fixed|money}} | {{prev_account.assets.fixed|money}}
| (i) Tangible assets | | {{account.assets.tangible|money}} | {{prev_account.assets.tangible|money}}
| (ii) Intangible assets | | {{account.assets.intangible|money}} | {{prev_account.assets.intangible|money}}
| (iii) Capital work-in-progress | | {{account.assets.wip_capital|money}} | {{prev_account.assets.wip_capital|money}}
| (iv) Intangible assets under development | | {{account.assets.intangile_wip|money}} | {{prev_account.assets.intangile_wip|money}}
| (b) Non-current investments | | {{account.assets.investments_non_current|money}} | {{prev_account.assets.investments_non_current|money}}
| (c) Deferred tax assets (net) | | {{account.assets.deferred_tax|money}} | {{prev_account.assets.deferred_tax|money}}
| (d) Long term loans and advances | | {{account.assets.longterm_loan|money}} | {{prev_account.assets.longterm_loan|money}}
| (e) Other non-current assets | | {{account.assets.other_non_current|money}} | {{prev_account.assets.other_non_current|money}}
h| (2) Current assets | | |
| (a) Current investments | | {{account.assets.investments|money}} | {{prev_account.assets.investments|money}}
| (b) Inventories | | {{account.assets.inventory|money}} | {{prev_account.assets.inventory|money}}
| (c) Trade receivables | | {{account.assets.trade_receivables|money}} | {{prev_account.assets.trade_receivables|money}}
| (d) Cash and cash equivalents | | {{account.assets.cash|money}} | {{prev_account.assets.cash|money}}
| (e) Short-term loans and advances | | {{account.assets.shortterm_loans|money}} | {{prev_account.assets.shortterm_loans|money}}
| (f) Other current assets | | {{account.assets.misc_current|money}} | {{prev_account.assets.misc_current|money}}
h| Total | | {{account.assets.total|money}} | {{prev_account.assets.total|money}}
|===

NOTE: Short-term provisions include TDS Liability and Auditor Fees.

<<<
