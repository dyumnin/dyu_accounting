= Financial Statements for AY {{cfg.fy+1}}
:toc:
:toc-title: Reports

== Cashbooks

{% for j in reports.journal %}
* link:{{j}}[{{j}}]
{% endfor %}

== Depreciation of Assets

{% for j in reports.depreciation %}
* link:{{j}}[{{j}}]
{% endfor %}

== Balance Sheet

{% for j in reports.balance_sheet %}
* link:{{j}}[{{j}}]
{% endfor %}

== Profit/Loss Statement

{% for j in reports.pnl %}
* link:{{j}}[{{j}}]
{% endfor %}

== GST Statement

{% for j in reports.gst %}
* link:{{j}}[{{j}}]
{% endfor %}
