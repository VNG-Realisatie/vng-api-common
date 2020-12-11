{% load vng_api_common markup_tags %}
# Autorisaties
## Scopes voor {{ project_name }} API

Scopes worden typisch per component gedefinieerd en geven aan welke rechten er zijn.
Zie de repository van de [Autorisaties API](https://github.com/VNG-Realisatie/autorisaties-api)

{% for scope in scopes %}
### {{ scope.label }}

**Scope**
`{{ scope.label }}`

{{ scope.description|default:"" }}
{% endfor %}
