# Cashbook for {{account_name}} as on 31 March {{cfg.fy+1}}

| Date  | Payee | Narration | Amount |
{%for txn in account%}
|{{txn.date}}    | {{txn.payee}}  | {{txn.narration}}    | {{txn.amount.number|round(2)}} |
{%endfor%}
