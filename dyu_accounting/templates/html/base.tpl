<!DOCTYPE html>
<html lang="en">
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.0.2/dist/css/bootstrap.min.css" rel="stylesheet" integrity="sha384-EVSTQN3/azprG1Anm3QDgpJLIm9Nao0Yz1ztcQTwFspd3yD65VohhpuuCOmLASjC" crossorigin="anonymous">
    {% block head %}
    <title>{% block title %}{% endblock %} </title>
    {% endblock %}
</head>
<body>
<div class="container-fluid">
	<div class="row">
		<div class="col-md-12">
			<div class="pb-2 mt-4 mb-2 border-bottom">
				<span class="h1">{{cfg.company.name}} <small>{{cfg.company.address}}</small></span>
			</div>
			<div class="row">
				<div class="col-md-12">
{% block content %}{% endblock %}
				</div>
			</div>
		</div>
	</div>
	<div class="row">
		<div class="col-md-12">
        {% block footer %}
Unaudited Financial Statement
        {% endblock %}
</div>
</div>
</div>
</body>
</html>
---
