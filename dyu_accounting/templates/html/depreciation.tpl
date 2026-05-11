<!--https://cleartax.in/s/balance-sheet/ -->
{%extends "base.tpl"%}
{%block title%} Depreciation Table{%endblock%}
{%block content%}
<h2>Depreciation Table as per MCA Rules</h2>


<table class="table table-bordered ">
<tr><th> Narration </th><th> Category</th> <th> Depreciation Rate</th> <th> Purchase Price </th>  <th> Purchase Date</th>  <th> Method</th>  <th> Scrap Value</th>
{%for year in range(min_fy,max_fy+1)%}
<th>{{year}}</th>
{%endfor%} </tr>
{%for txn in depr.mca%}
<tr><td>{{txn.narration}}   </td> <td> {{txn.category}} </td>
<td> {{txn.rate|round(3)}}  </td>
<td> {{txn.cost}}  </td>
<td> {{txn.purchased_on}}  </td>
<td> {{txn.method}}  </td>
<td> {{txn.scrap|round(2)}}  </td>
{%for year in range(min_fy,max_fy+1)%}
<th>
{%if year in txn.table %}
{{txn.table[year]|round(3)}}
{%endif%}</th>
{%endfor%} </tr>
</tr>
{%endfor%}
<tr>
<th> Total </th>
<td> - </td>
<td> - </td>
<td> - </td>
<td> - </td>
<td> - </td>
<td> - </td>
{%for year in range(min_fy,max_fy+1)%}
<th>{%if year in depr.total.mca%}{{depr.total.mca[year]|round(3)}}{%endif%}</th>
{%endfor%}
  
</tr>
</table>

<h2>Depreciation Table as per IT Rules, SLM Method</h2>
<table class="table table-bordered">
<tr><th> Block </th> <th> Type </th><th> Rate</th>
{%for year in range(min_fy,max_fy+1)%}
<th colspan=2>{{year}}</th>
{%endfor%} </tr>
<tr><th>  </th> <th>  </th><th> </th>
{%for year in range(min_fy,max_fy+1)%}
<th >Block Value</th>
<th >Depreciation</th>
{%endfor%} </tr>
{%for key,txn in depr.it.items() %}
<tr>
<td>{{key}}</td>
<td>{{txn['block']}}</td>
<td>{{txn.rate}}</td>
{%for year in range(min_fy,max_fy+1)%}
<td>{%if year in txn.table %}
{{txn.table[year]['amount']}}
{%endif%} </td>
<td>{%if year in txn.table %}
{{txn.table[year]['depr'] }}
{%endif%} </td>
{%endfor%}</th> </tr>
{%endfor%}
<tr>
<th>Total</th>
<td></td>
<td></td>
{%for year in range(min_fy,max_fy+1)%}
<td></td>
<th>{%if year in depr.total.it%}{{depr.total.it[year]|round(3)}}{%endif%}</th>
{%endfor%}
</tr> 
</table>
{%endblock%}
