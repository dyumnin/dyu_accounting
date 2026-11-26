= Depreciation Report

{% set start_fy = [min_fy, max_fy - 2]|max %}
{% set year_count = max_fy - start_fy + 1 %}
<<<
[.landscape]
--
== Depreciation Table as per MCA Rules

NOTE: Showing the last 3 years ({{start_fy}}-{{max_fy}}). Full history is in the underlying ledger.

[cols="5,2,1,1,1,1,1{% for _ in range(year_count) %},1{% endfor %}",options="header"]
|===
| Narration | Category | Depreciation Rate | Purchase Price | Purchase Date | Method | Scrap Value{% for year in range(start_fy,max_fy+1) %} | {{year}}{% endfor %}

{% for txn in depr.mca -%}
| {{txn.narration}} | {{txn.category}} | {{txn.rate|round(2)}} | {{txn.cost|money}} | {{txn.purchased_on}} | {{txn.method}} | {{txn.scrap|round(2)}}{% for year in range(start_fy,max_fy+1) %} | {% if year in txn.table %}{{txn.table[year]|round(2)}}{% endif %}{% endfor %}

{% endfor -%}
s| Total s| - s| - s| - s| - s| - s| -{% for year in range(start_fy,max_fy+1) %} s| {% if year in depr.total.mca %}{{depr.total.mca[year]|round(2)}}{% endif %}{% endfor %}

|===

== Depreciation Table as per IT Rules

NOTE: Showing the last 3 years ({{start_fy}}-{{max_fy}}). Full history is in the underlying ledger.

[cols="4,2,1{% for _ in range(year_count) %},2,1{% endfor %}",options="header"]
|===
| Block | Type | Rate{% for year in range(start_fy,max_fy+1) %} | Block Value {{year}} | Depreciation {{year}}{% endfor %}

{% for key,txn in depr.it.items() -%}
| {{key}} | {{txn['block']}} | {{txn.rate|round(2)}}{% for year in range(start_fy,max_fy+1) %} | {% if year in txn.table %}{{txn.table[year]['amount']|money}}{% endif %} | {% if year in txn.table %}{{txn.table[year]['depr']|round(2)}}{% endif %}{% endfor %}

{% endfor -%}
s| Total s| s| {% for year in range(start_fy,max_fy+1) %} s| s| {% if year in depr.total.it %}{{depr.total.it[year]|round(2)}}{% endif %}{% endfor %}

|===
--
<<<
