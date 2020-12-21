## Notificaties
## Berichtkenmerken voor {{ project_name }} API

Kanalen worden typisch per component gedefinieerd. Producers versturen berichten op bepaalde kanalen,
consumers ontvangen deze. Consumers abonneren zich via een notificatiecomponent (zoals {{ 'https://notificaties-api.vng.cloud/api/v1/schema/'|urlize }}) op berichten.

Hieronder staan de kanalen beschreven die door deze component gebruikt worden, met de kenmerken bij elk bericht.

De architectuur van de notificaties staat beschreven op {{ 'https://github.com/VNG-Realisatie/notificaties-api'|urlize }}.

{% for kanaal in kanalen %}
### {{ kanaal.label }}

**Kanaal**
`{{ kanaal.label }}`

{{ kanaal.description|default:""|urlize }}

**Resources en acties**

{% for resource, actions in kanaal.get_usage %}
* <code>{{ resource }}</code>: {{ actions|join:", " }}
{% endfor %}
{% endfor %}
