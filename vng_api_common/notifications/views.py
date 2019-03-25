from django.views.generic import TemplateView

from .kanalen import KANAAL_REGISTRY


class KanalenView(TemplateView):
    template_name = 'vng_api_common/kanalen.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['kanalen'] = sorted(KANAAL_REGISTRY, key=lambda s: s.label)
        return context
