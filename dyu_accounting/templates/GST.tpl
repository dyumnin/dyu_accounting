{%extends "base.tpl"%}
{%block title%} GST Table for FY {{cfg.fy}}{%endblock%}
{%block content%}
<h2> GST Table for FY {{cfg.fy}}</h2>
<table class="table table-bordered">
<tr><th>Month/Quarter</th> <th>Category</th><th>Amount</th></tr>
{%for x in range(gst|length)%}
{%for keys in gst[x]%}
<tr><th>{{1+x}}</th> <th>{{keys}}</th><th>{{gst[x][keys]}}</th></tr>
{%endfor%}
{%endfor%}
{%endblock%}
</table>



