"""
Basic behind-the-scenes maintenance for superusers,
via django.contrib.admin.
"""

import models
from django.contrib.admin import SimpleListFilter
from django.contrib.gis import admin
from .apikey.models import ApiKey


class SubmissionSetFilter (SimpleListFilter):
    """
    Used to filter a list of submissions by type (set name).
    """
    title = 'Submission Set'
    parameter_name = 'set'

    def lookups(self, request, model_admin):
        qs = model_admin.get_queryset(request)
        qs = qs.order_by('parent__name').distinct('parent__name').values('parent__name')
        return [(elem['parent__name'], elem['parent__name']) for elem in qs]

    def queryset(self, request, qs):
        parent__name = self.value()
        if parent__name:
            qs = qs.filter(parent__name=parent__name)
        return qs


class DataSetFilter (SimpleListFilter):
    """
    Used to filter a list of submitted things by dataset slug.
    """
    title = 'Dataset'
    parameter_name = 'dataset'

    def lookups(self, request, model_admin):
        qs = model_admin.get_queryset(request)
        qs = qs.order_by('dataset__slug').distinct('dataset__slug').values('dataset__slug')
        return [(elem['dataset__slug'], elem['dataset__slug']) for elem in qs]

    def queryset(self, request, qs):
        dataset__slug = self.value()
        if dataset__slug:
            qs = qs.filter(dataset__slug=dataset__slug)
        return qs


class SubmittedThingAdmin(admin.OSMGeoAdmin):
    date_hierarchy = 'created_datetime'
    list_display = ('id', 'created_datetime', 'updated_datetime', 'submitter_name', 'dataset')
    list_filter = (DataSetFilter,)
    search_fields = ('submitter__username', 'data',)

    raw_id_fields = ('submitter', 'dataset')

    def submitter_name(self, obj):
        return obj.submitter.username if obj.submitter else None

    def get_queryset(self, request):
        qs = super(SubmittedThingAdmin, self).get_queryset(request)
        user = request.user
        if not user.is_superuser:
            qs = qs.filter(dataset__owner=user)
        return qs


class InlineApiKeyAdmin(admin.StackedInline):
    model = ApiKey.datasets.through


class InlineGroupAdmin(admin.StackedInline):
    model = models.Group
    filter_horizontal = ('submitters',)
    extra = 1


class DataSetAdmin(admin.ModelAdmin):
    list_display = ('display_name', 'slug', 'owner')
    prepopulated_fields = {'slug': ['display_name']}
    inlines = [InlineApiKeyAdmin, InlineGroupAdmin]


class PlaceAdmin(SubmittedThingAdmin):
    model = models.Place


class SubmissionSetAdmin(admin.ModelAdmin):
    list_display = ('id', 'name',)
    list_filter = ('name',)


class SubmissionAdmin(SubmittedThingAdmin):
    model = models.Submission

    list_display = SubmittedThingAdmin.list_display + ('place', 'set_',)
    list_filter = (SubmissionSetFilter,) + SubmittedThingAdmin.list_filter
    list_select_related = ('parent',)
    search_fields = ('parent__name',) + SubmittedThingAdmin.search_fields

    def set_(self, obj):
        return obj.parent.name
    set_.short_description = 'Set'
    set_.admin_order_field = 'parent__name'

    def place(self, obj):
        return obj.parent.place_id
    place.admin_order_field = 'parent__place'


class ActionAdmin(admin.ModelAdmin):
    date_hierarchy = 'created_datetime'
    list_display = ('id', 'created_datetime', 'action', 'submitter_name')

    def submitter_name(self, obj):
        return obj.submitter.username if obj.submitter else None


class InlineGroupPermissionAdmin(admin.TabularInline):
    model = models.GroupPermission
    extra = 0


class GroupAdmin(admin.ModelAdmin):
    raw_id_fields = ('dataset',)
    filter_horizontal = ('submitters',)
    inlines = [InlineGroupPermissionAdmin]

    class Media:
        js = (
            'admin/js/jquery-1.11.0.min.js',
            'admin/js/jquery-ui-1.10.4.min.js',
            'admin/js/admin-list-reorder.js',
        )


admin.site.register(models.DataSet, DataSetAdmin)
admin.site.register(models.Place, PlaceAdmin)
admin.site.register(models.SubmissionSet, SubmissionSetAdmin)
admin.site.register(models.Submission, SubmissionAdmin)
admin.site.register(models.Action, ActionAdmin)
admin.site.register(models.Group, GroupAdmin)
