{%extends "base.tpl"%}
{%block title%}Profit and Loss Statement for AY {{cfg.fy+1}} {%endblock%}
{%block content%}
<h2>P & L statement as on 31 March {{cfg.fy+1}}</h2>
<table class="table table-bordered">
<tr><th>Particulars</th> <th>Amount</th></tr>
<tr> <th>Income</th> <th></th></tr>
<tr> <td>Revenue from Operations</td> <td>{{pnl.revenue|round(3)}}</td></tr>
<tr> <th>             Total Revenue         </th> <th>{{pnl.revenue|round(3)}}</th></tr>

<tr> <th>Expenses</th> <th></th></tr>
<tr> <td>Salary(Net)</td> <td>{{pnl.salary|round(3)}}</td></tr>
<tr> <td>Depreciation</td> <td>{{pnl.depreciation|round(3)}}</td></tr>
<tr> <td>Other Expenses</td> <td>{{pnl.misc_expenses}}</td></tr>
<tr> <th>Total Expenses                      </th> <th>{{pnl.expenses_total|round(3)}}</th></tr>
<tr> <th> Profit/Loss                       </th> <th>{{pnl.profit|round(3)}} {%if pnl.profit >0 %} (Loss) {%endif%}</th></tr>

</table>
<p>
Note: Salary deductions(TDS,PF are counted as liabilities and transfer as Expenses:INR:GOI,GOK)
{%endblock%}


