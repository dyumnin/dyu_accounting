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
<div class="container-fluid bg-primary">
<div class="row">
<div class="col-12">
<p class="h1">{{company.name}}</p>
<p class="lead">{{company.address}}</p>
</div>
</div>
</div>
<div id="content">{% block content %}{% endblock %}</div>
<div id="footer" class="bg-alert text-muted">
        {% block footer %}
Unaudited Financial Statement
        {% endblock %}
    </div>
</body>
</html>
