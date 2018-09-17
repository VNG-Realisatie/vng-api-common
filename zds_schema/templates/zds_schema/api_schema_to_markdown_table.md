{% load zds_schema %}# Resources

Dit document beschrijft de (RGBZ-)objecttypen die als resources ontsloten
worden met de beschikbare attributen.

{% for table in tables %}
## {{ table.resource }}

| Attribuut | Omschrijving | Type | Verplicht | CRUD* |
| --- | --- | --- | --- | --- |{% for row in table.rows %}
| {{ row.label|md_table_cell }} | {{ row.description|md_table_cell }} | {{ row.type|md_table_cell }} | {{ row.required|yesno:"ja,nee" }} | {{ row|crud }} |{% endfor %}
{% endfor %}

* Create, Read, Update, Delete
