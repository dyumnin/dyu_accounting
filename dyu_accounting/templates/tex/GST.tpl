---
title: GST Table for FY {{cfg.fy}} 
---
\section{ GST Table for FY {{cfg.fy}} }

\begin{tabular}
Month/Quarter &Category&Assets&Liabilities
{%for x in range(gst|length)-%}
{%for account in accounts -%}  {{x+1}}&{{account}}
{%-for keys in ['Assets', 'Liabilities']-%} &{{gst[x][keys][account]}}
{%endfor%}
{%endfor%}
{%endfor%}
\end{tabular}
