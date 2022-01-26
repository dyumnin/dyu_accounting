{%extends "base.tpl"%}
{%block title%} GST Table for FY {{cfg.fy}}{%endblock%}
{%block content%}
<h2> GST Table for FY {{cfg.fy}}</h2>
<table class="table table-bordered">
<tr><th>Month/Quarter</th> <th>Category</th><th>Assets</th><th>Liabilities</th></tr>
{%for x in range(gst|length)%}
{%for account in accounts %}
<tr><td> {{x+1}}</td><td>{{account}}</td>
{%for keys in ['Assets', 'Liabilities']%}
<td>{{gst[x][keys][account]}}</td>
{%endfor%}
{%endfor%}
{%endfor%}
{%endblock%}
</table>



