{% load vng_api_common markup_tags %}
# {{ project_name }} scopes
## {{ site_title }}

Scopes worden typisch per component gedefinieerd en geven aan welke rechten er zijn.
Het JWT van de aanroepende component geeft aan welke rechten deze component heeft of wil verkrijgen.

{% for scope in scopes %}
### {{ scope.label }}

**Scope**
`{{ scope.label }}`

{{ scope.description|default:"" }}
{% endfor %}
