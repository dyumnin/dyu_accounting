= GST Table for FY {{cfg.fy}}

[options="header",cols="1,3,2,2"]
|===
| Month/Quarter | Category | Assets | Liabilities

{% for x in range(gst|length) %}
{% for account in accounts %}
| {{x+1}} | {{account|esc}} | {{ (gst[x]['Assets'][account] if account in gst[x]['Assets'] else '')|money }} | {{ (gst[x]['Liabilities'][account] if account in gst[x]['Liabilities'] else '')|money }}
{% endfor %}
{% endfor %}
|===
