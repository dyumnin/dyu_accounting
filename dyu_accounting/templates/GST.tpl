{%extends "base.tpl"%}
{%block title%} GST Table for FY {{fy}}{%endblock%}
{%block content%}
<h2> GST Table for FY {{fy}}</h2>
<table class="table table-bordered">
<tr><th>Month/Quarter</th> <th>Category</th><th>Amount</th></tr>
{%for x in range(data|length)%}
{%for keys in data[x]%}
<tr><th>{{1+x}}</th> <th>{{keys}}</th><th>{{data[x][keys]}}</th></tr>
{%endfor%}
{%endfor%}
{%endblock%}
</table>



