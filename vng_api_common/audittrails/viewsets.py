from django.db import transaction

from rest_framework import viewsets

from ..viewsets import NestedViewSetMixin
from .api.serializers import AuditTrailSerializer
from .constants import AuditTrailAction
from .models import AuditTrail


class AuditTrailMixin:
    audit = None

    def get_audittrail_main_object_url(self, data, main_resource):
        return data[main_resource]

    def create_audittrail(self, status_code, action, version_before_edit, version_after_edit):
        data = version_after_edit if version_after_edit else version_before_edit
        if self.basename == self.audit.main_resource:
            main_object = data['url']
        else:
            main_object = self.get_audittrail_main_object_url(data, self.audit.main_resource)

        trail = AuditTrail(
            bron=self.audit.component_name,
            actie=action,
            actieWeergave=AuditTrailAction.labels.get(action, ''),
            resultaat=status_code,
            hoofdObject=main_object,
            resource=self.basename,
            resourceUrl=data['url'],
            oud=version_before_edit,
            nieuw=version_after_edit,
        )
        trail.save()


class AuditTrailCreateMixin(AuditTrailMixin):
    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        self.create_audittrail(
            response.status_code,
            AuditTrailAction.create,
            version_before_edit=None,
            version_after_edit=response.data,
        )
        return response


class AuditTrailUpdateMixin(AuditTrailMixin):
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        version_before_edit = serializer.data

        action = AuditTrailAction.partial_update if kwargs.get('partial', False) else AuditTrailAction.update

        response = super().update(request, *args, **kwargs)
        self.create_audittrail(
            response.status_code,
            action,
            version_before_edit=version_before_edit,
            version_after_edit=response.data,
        )
        return response


class AuditTrailDestroyMixin(AuditTrailMixin):
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        version_before_edit = serializer.data

        if self.basename == self.audit.main_resource:
            with transaction.atomic():
                response = super().destroy(request, *args, **kwargs)
                self._destroy_related_audittrails(version_before_edit['url'])
                return response
        else:
            response = super().destroy(request, *args, **kwargs)
            self.create_audittrail(
                response.status_code,
                AuditTrailAction.delete,
                version_before_edit=version_before_edit,
                version_after_edit=None
            )
            return response

    def _destroy_related_audittrails(self, main_object_url):
        AuditTrail.objects.filter(hoofdObject=main_object_url).delete()


class AuditTrailViewsetMixin(AuditTrailCreateMixin,
                             AuditTrailUpdateMixin,
                             AuditTrailDestroyMixin):
    pass


class AuditTrailViewset(viewsets.ReadOnlyModelViewSet, NestedViewSetMixin):
    queryset = AuditTrail.objects.all()
    serializer_class = AuditTrailSerializer
    lookup_field = 'uuid'

    main_resource_lookup_field = None       # Must be overwritten by subclasses

    def get_queryset(self):
        base = super().get_queryset()
        identifier = self.kwargs.get(self.main_resource_lookup_field)
        if identifier:
            return base.filter(hoofdObject__contains=identifier)
        return base
