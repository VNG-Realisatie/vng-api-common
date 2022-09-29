from django.conf import settings
from django.utils.module_loading import import_string


def register_extensions():
    """
    Loads DRF spectacular extensions set through the SPECTACULAR_EXTENSIONS setting
    """
    extensions = settings.SPECTACULAR_EXTENSIONS

    for extension in extensions:
        import_string(extension)
