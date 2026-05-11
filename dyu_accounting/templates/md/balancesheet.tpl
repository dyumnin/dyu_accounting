---
title: Balance Sheet for fy {{cfg.fy}} 
ref: https://cleartax.in/s/balance-sheet/
---
# Balance Sheet as on 31 March {{cfg.fy+1}}

| Particulars                                   | Note No. | {{cfg.fy}}-{{cfg.fy+1}}                           | {{cfg.fy-1}}-{{cfg.fy}}                                | 
| -----------                                   | ---      | ----------                                        | -----------                                            | 
| I. EQUITY AND LIABILITIES                     |          |                                                   |                                                        | 
| 1) Shareholder's Funds                        |          |                                                   |                                                        | 
| (a) Share Capital                             | 1        | {{account.liabilities.share_capital}}             | {{prev_account.liabilities.share_capital}}             | 
| (b) Reserves and Surplus                      |          | {{account.liabilities.surplus}}                   | {{account.liabilities.surplus}}                        | 
| (c) Money received against share warrants     |          |                                                   |                                                        | 
| (2) Share application money pending allotment |          |                                                   |                                                        | 
| (3) Non-Current Liabilities                   |          |                                                   |                                                        | 
| (a) Long-term borrowings                      |          | {{account.liabilities.longterm_borrowing}}        | {{prev_account.liabilities.longterm_borrowing}}        | 
| (b) Deferred tax liabilities (Net)            |          | {{account.liabilities.deferred_tax}}              | {{prev_account.liabilities.deferred_tax}}              | 
| (c) Other Long term liabilities               |          | {{account.liabilities.longterm_liability}}        | {{prev_account.liabilities.longterm_liability}}        | 
| (d) Long term provisions                      |          | {{account.liabilities.longterm_provisions}}       | {{prev_account.liabilities.longterm_provisions}}       | 
| (4) Current Liabilities                       |          |                                                   |                                                        | 
| (a) Short-term borrowings                     | 2        | {{account.liabilities.shortterm_borrowing}}       | {{prev_account.liabilities.shortterm_borrowing}}       | 
| (b) Trade payables                            |          | {{account.liabilities.trade_payable}}             | {{prev_account.liabilities.trade_payable}}             | 
| (c) Other current liabilities                 |          | {{account.liabilities.other_current_liabilities}} | {{prev_account.liabilities.other_current_liabilities}} | 
| (d) Short-term provisions                     |          | {{account.liabilities.shortterm_provisions}}      | {{prev_account.liabilities.shortterm_provisions}}      | 
| Total                                         |          | {{account.liabilities.total}}                     | {{prev_account.liabilities.total}}                     | 
| II.Assets                                     |          |                                                   |                                                        | 
| (1) Non-current assets                        |          | {{account.assets.non_current}}                    | {{prev_account.assets.non_current}}                    | 
| (a) Fixed assets                              |          | {{account.assets.fixed}}                          | {{prev_account.assets.fixed}}                          | 
| (i) Tangible assets                           |          | {{account.assets.tangible}}                       | {{prev_account.assets.tangible}}                       | 
| (ii) Intangible assets                        |          | {{account.assets.intangible}}                     | {{prev_account.assets.intangible}}                     | 
| (iii) Capital work-in-progress                |          | {{account.assets.wip_capital}}                    | {{prev_account.assets.wip_capital}}                    | 
| (iv) Intangible assets under development      |          | {{account.assets.intangile_wip}}                  | {{prev_account.assets.intangile_wip}}                  | 
| (b) Non-current investments                   |          | {{account.assets.investments_non_current}}        | {{prev_account.assets.investments_non_current}}        | 
| (c) Deferred tax assets (net)                 |          | {{account.assets.deferred_tax}}                   | {{prev_account.assets.deferred_tax}}                   | 
| (d) Long term loans and advances              |          | {{account.assets.longterm_loan}}                  | {{prev_account.assets.longterm_loan}}                  | 
| (e) Other non-current assets                  |          | {{account.assets.other_non_current}}              | {{prev_account.assets.other_non_current}}              | 
| (2) Current assets                            |          |                                                   |                                                        | 
| (a) Current investments                       |          | {{account.assets.investments}}                    | {{prev_account.assets.investments}}                    | 
| (b) Inventories                               |          | {{account.assets.inventory}}                      | {{prev_account.assets.inventory}}                      | 
| (c) Trade receivables                         |          | {{account.assets.trade_receivables}}              | {{prev_account.assets.trade_receivables}}              | 
| (d) Cash and cash equivalents                 |          | {{account.assets.cash}}                           | {{prev_account.assets.cash}}                           | 
| (e) Short-term loans and advances             |          | {{account.assets.shortterm_loans}}                | {{prev_account.assets.shortterm_loans}}                | 
| (f) Other current assets                      |          | {{account.assets.misc_current}}                   | {{prev_account.assets.misc_current}}                   | 
| Total                                         |          | {{account.assets.total}}                          | {{prev_account.assets.total}}                          | 


2) shortterm_provisions=TDS Liability, Auditor Fees 
\newpage
