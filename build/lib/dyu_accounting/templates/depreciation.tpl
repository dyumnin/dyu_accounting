# Depreciation Table as per MCA Rules

| Narration | Category | Depreciation Rate | Purchase Price   | Purchase Date  | Method  | Scrap Value {%for year in range(min_fy,max_fy+1)%} |{{year}} {%endfor%} |
{%for txn in depr.mca%}
|{{txn.narration}} | {{txn.category}} | {{txn.rate|round(3)}} | {{txn.cost}} | {{txn.purchased_on}} | {{txn.method}} | {{txn.scrap|round(2)}}  {%for year in range(min_fy,max_fy+1)%} | {%if year in txn.table %} {{txn.table[year]|round(3)}} {%endif%} {%endfor%} |
{%endfor%}
|
| Total | - | - | - | - | - | - {%for year in range(min_fy,max_fy+1)%} |{%if year in depr.total.mca%}{{depr.total.mca[year]|round(3)}}{%endif%} {%endfor%} |

# Depreciation Table as per IT Rules, SLM Method

| Block  | Type | Rate {%for year in range(min_fy,max_fy+1)%}  |{{year}} |{{year}} {%endfor%}

|  | | {%for year in range(min_fy,max_fy+1)%} | Block Value | Depreciation {%endfor%} |
{%for key,txn in depr.it.items() %}  |{{key}} |{{txn['block']}} |{{txn.rate}}
{%-for year in range(min_fy,max_fy+1)-%}
|{%-if year in txn.table %} {{txn.table[year]['amount']}} {%-endif-%} 
|{%if year in txn.table %} {{txn.table[year]['depr'] }} {%endif-%} 
{%endfor%} |
{%endfor%}
| Total | |
{%-for year in range(min_fy,max_fy+1)-%}
| |{%if year in depr.total.it%}{{depr.total.it[year]|round(3)}}{%endif-%}
{%endfor%}
| 
