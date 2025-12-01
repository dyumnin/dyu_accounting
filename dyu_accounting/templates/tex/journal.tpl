\section{ Cashbook for {{account_name}} as on 31 March {{cfg.fy+1}} }

\begin{tabular}
 Date  & Payee & Narration & Amount \hline
{%for txn in account%}
{{txn.date}}    & {{txn.payee}}  & {{txn.narration}}    & {{txn.amount.number|round(2)}} \\
{%endfor%}
\end{tabular}
