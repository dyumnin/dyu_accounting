\section{Depreciation Table fy {{cfg.fy}} - {{cfg.fy+1}} }
% ref: https://cleartax.in/s/balance-sheet/
\subsection{MCA WDV Method}
\begin{tabular}{p{0.1\textwidth}p{0.1\textwidth} {%for i in range(min_fy,max_fy+6)%} p{1cm}{%endfor%}}
\hline
 Narration & Category & Depreciation Rate & Purchase Price   & Purchase Date  & Method  & Scrap Value {%for year in range(min_fy,max_fy+1)%} &{{year}} {%endfor%} \\ \hline
{%for txn in depr.mca%}
{{txn.narration}} & {{txn.category}} & {{txn.rate|round(3)}} & {{txn.cost}} & {{txn.purchased_on}} & {{txn.method}} & {{txn.scrap|round(2)}}  {%for year in range(min_fy,max_fy+1)%} & {%if year in txn.table %} {{txn.table[year]|round(3)}} {%endif%} {%endfor%} &
{%endfor%}
\\
& Total & - & - & - & - & - & - {%for year in range(min_fy,max_fy+1)%} &{%if year in depr.total.mca%}{{depr.total.mca[year]|round(3)}}{%endif%} {%endfor%} \\
\end{tabular}

\subsection{ Depreciation Table as per IT Rules, SLM Method}

\begin{tabular}{p{0.1\textwidth}p{0.1\textwidth}{%for year in range(min_fy,max_fy+2)%}  p{1cm} p{1cm} {%endfor%}}
Block  & Type & Rate {%for year in range(min_fy,max_fy+1)%}  &{{year}} &{{year}} {%endfor%}

&  & & {%for year in range(min_fy,max_fy+1)%} & Block Value & Depreciation {%endfor%} \\
{%for key,txn in depr.it.items() %}  &{{key}} &{{txn['block']}} &{{txn.rate}}
{%-for year in range(min_fy,max_fy+1)-%}
&{%-if year in txn.table %} {{txn.table[year]['amount']}} {%-endif-%} 
&{%if year in txn.table %} {{txn.table[year]['depr'] }} {%endif-%} 
{%endfor%} &
{%endfor%}
& Total & &
{%-for year in range(min_fy,max_fy+1)-%}
& &{%if year in depr.total.it%}{{depr.total.it[year]|round(3)}}{%endif-%}
{%endfor%}

\end{tabular}
