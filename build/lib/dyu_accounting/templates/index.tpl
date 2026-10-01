{%extends "base.tpl"%}
{%block title%} Financial Statements for {{ay}} {%endblock%}
{%block content%}
<div class="row">
<div class="col-6">
<h2> Cashbooks</h2>
<ol>
{% for j in reports.journal%}
<li><a href="{{j}}"> {{j}}</a>, </li>
{%endfor%}
</ol>
</div>
<div class="col-6">
<h2> Depreciation of Goods</h2>
{% for j in reports.depreciation%}
<a href="{{j}}"> {{j}}</a>
{%endfor%}

</div>
<div class="col-6">
<h2> Balance Sheet </h2>
{% for j in reports.balance_sheet%}
<a href="{{j}}"> {{j}}</a>
{%endfor%}

</div>
<div class="col-6">

<h2> Profit/Loss Statement</h2>
{% for j in reports.pnl%}
<a href="{{j}}"> {{j}}</a>
{%endfor%}

</div>
<div class="col-6">
<h2> GST Statement</h2>
{% for j in reports.gst%}
<a href="{{j}}"> {{j}}</a>
{%endfor%}
{%endblock%}
