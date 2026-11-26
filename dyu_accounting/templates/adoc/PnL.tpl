= Profit and Loss Statement for AY {{cfg.fy+1}}

== P & L Statement as on 31 March {{cfg.fy+1}}

[options="header",cols="4,2"]
|===
| Particulars | Amount

h| Income |
| Revenue from Operations | {{pnl.revenue|round(2)}}
h| Total Revenue | {{pnl.revenue|round(2)}}
h| Expenses |
| Salary (Net) | {{pnl.salary|round(2)}}
| Depreciation | {{pnl.depreciation|round(2)}}
| Other Expenses | {{pnl.misc_expenses|round(2)}}
h| Total Expenses | {{pnl.expenses_total|round(2)}}
h| Profit/Loss | {{pnl.profit|round(2)}}{% if pnl.profit < 0 %} (Loss){% endif %}

|===

NOTE: Salary deductions (TDS, PF) are counted as liabilities and transferred as Expenses:INR:GOI,GOK.
