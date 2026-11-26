= Depreciation Report

{% set start_fy = [min_fy, max_fy - 2]|max %}
{% set year_count = max_fy - start_fy + 1 %}
== Depreciation Table as per MCA Rules

NOTE: Showing the last 3 years ({{start_fy|fy_label}} to {{max_fy|fy_label}}). Full history is in the underlying ledger.

[.landscape]
<<<

[cols="5,2,1,1,1,1,1{% for _ in range(year_count) %},1{% endfor %}",options="header"]
|===
| Narration | Category | Depreciation Rate | Purchase Price | Purchase Date | Method | Scrap Value{% for year in range(start_fy,max_fy+1) %} | {{year|fy_label}}{% endfor %}

{% for txn in depr.mca -%}
{% if max_fy in txn.table %}
| {{txn.narration|esc}} | {{txn.category|esc}} | {{txn.rate|round(2)}} | {{txn.cost|money}} | {{txn.purchased_on}} | {{txn.method}} | {{txn.scrap|round(2)}}{% for year in range(start_fy,max_fy+1) %} | {% if year in txn.table %}{{txn.table[year]|round(2)}}{% endif %}{% endfor %}

{% endif %}
{% endfor -%}
s| Total s| - s| - s| - s| - s| - s| -{% for year in range(start_fy,max_fy+1) %} s| {% if year in depr.total.mca %}{{depr.total.mca[year]|round(2)}}{% endif %}{% endfor %}

|===

[.portrait]
<<<

== Depreciation Table as per IT Rules

NOTE: Showing the last 3 years ({{start_fy|fy_label}} to {{max_fy|fy_label}}). Full history is in the underlying ledger.

[.landscape]
<<<

[cols="4,2,1{% for _ in range(year_count) %},2,1{% endfor %}",options="header"]
|===
| Block | Type | Rate{% for year in range(start_fy,max_fy+1) %} | Block Value {{year|fy_label}} | Depreciation {{year|fy_label}}{% endfor %}

{% for key,txn in depr.it.items() -%}
{% if max_fy in txn.table %}
| {{key|esc}} | {{txn['block']|esc}} | {{txn.rate|round(2)}}{% for year in range(start_fy,max_fy+1) %} | {% if year in txn.table %}{{txn.table[year]['amount']|money}}{% endif %} | {% if year in txn.table %}{{txn.table[year]['depr']|round(2)}}{% endif %}{% endfor %}

{% endif %}
{% endfor -%}
s| Total s| s| {% for year in range(start_fy,max_fy+1) %} s| s| {% if year in depr.total.it %}{{depr.total.it[year]|round(2)}}{% endif %}{% endfor %}

|===

[.portrait]
<<<
