
\section{ P \& L statement as on 31 March {{cfg.fy+1}} }
\begin{tabular}
& Particulars             & Amount                \\\hline
& Income                  &                       \\
& Revenue from Operations & {{pnl.revenue| round(3)}}  \\
& Total Revenue           & {{pnl.revenue| round(3)}}  \\
& Expenses                &                       \\
& Salary(Net)             & {{pnl.salary| round(3)}}                                        \\
& Depreciation            & {{pnl.depreciation| round(3)}}                                        \\
& Other Expenses          & {{pnl.misc_expenses}} \\
& Total Expenses          & {{pnl.expenses_total  | round(3)}}\\
& Profit/Loss             & {{pnl.profit | round(3)}} {%if pnl.profit >0 %} (Loss) {%endif%} \\
\end{tabular}

Note: Salary deductions(TDS,PF are counted as liabilities and transfer as Expenses:INR:GOI,GOK)
