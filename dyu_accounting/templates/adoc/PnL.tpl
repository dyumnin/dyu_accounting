= Profit and Loss Statement for AY {{cfg.fy+1}}

== P & L Statement as on 31 March {{cfg.fy+1}}

[options="header",cols="4,2"]
|===
| Particulars | Amount

h| Income |
| Revenue from Operations | {{pnl.revenue|round(3)}}
h| Total Revenue | {{pnl.revenue|round(3)}}
h| Expenses |
| Salary (Net) | {{pnl.salary|round(3)}}
| Depreciation | {{pnl.depreciation|round(3)}}
| Other Expenses | {{pnl.misc_expenses}}
h| Total Expenses | {{pnl.expenses_total|round(3)}}
h| Profit/Loss | {{pnl.profit|round(3)}}{% if pnl.profit > 0 %} (Loss){% endif %}
|===

NOTE: Salary deductions (TDS, PF) are counted as liabilities and transferred as Expenses:INR:GOI,GOK.
