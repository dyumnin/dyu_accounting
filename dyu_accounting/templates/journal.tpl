<!--https://cleartax.in/s/balance-sheet/ -->
{%extends "base.tpl"%}
{%block title%} Depreciation Table{%endblock%}
{%block content%}
<h2>Cashbook for {{account_name}} as on 31 March {{ay}}</h2>

<table  class="table table-bordered">
<tr><th> Date </th> <th> Payee</th> <th> Narration</th> <th> Amount</th> </tr>
{%for txn in account%}
<tr><td>{{txn.date}}   </td> <td> {{txn.payee}} </td> <td> {{txn.narration}}  </td>  <td> {{txn.amount.number|round(2)}} </td> </tr>
{%endfor%}
</table>

{%endblock%}
