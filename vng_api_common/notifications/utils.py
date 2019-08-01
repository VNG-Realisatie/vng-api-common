from .kanalen import Kanaal


def notification_documentation(kanaal: Kanaal):
    """
    Generate notification documentation for an OpenAPI specification containing
    the relevant resources and actions for a given KANAAL
    """
    doc = f"""### Notificaties \
           \n\nDeze API publiceert notificaties op het kanaal `{kanaal.label}`. \
           \n\n{kanaal.description}
           \n\n**Resources en acties**\n\n"""

    for resource, actions in kanaal.get_usage():
        doc += f"""- `{resource}`: {', '.join(actions)}\n"""
    return doc
