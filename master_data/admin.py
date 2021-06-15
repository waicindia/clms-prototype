from django.contrib import admin
from .models import *
from django.apps import apps
from import_export.admin import ImportExportModelAdmin
from child_management.admin import ImportExportFormat


@admin.register(Centre)
class CentreAdmin(ImportExportModelAdmin, ImportExportFormat):
	list_display = ['name','active']
	fields = ['name','active']
	search_fields = ['name', ]


@admin.register(State)
class StateAdmin(ImportExportModelAdmin, ImportExportFormat):
	list_display = ['name','centre','active']
	fields = ['name','centre','active']
	search_fields = ['name', ]
    

@admin.register(District)
class DistrictAdmin(ImportExportModelAdmin, ImportExportFormat):
	list_display = ['name','state','active']
	fields = ['name','state','active']
	list_filter = ['state__name', ]
	search_fields = ['name', ]


@admin.register(ShelterHome)
class ShelterHomeAdmin(ImportExportModelAdmin, ImportExportFormat):
	list_display = ['name','district','address','latitude','longitude','active']
	fields = ['name','district','address','latitude','longitude','active']
	search_fields = ['name', 'district__name']


@admin.register(Relationship)
class RelationshipAdmin(ImportExportModelAdmin, ImportExportFormat):
	list_display = ['name','active']
	fields = ['name','active']
	search_fields = ['name', ]


@admin.register(ChildClassification)
class ChildClassificationAdmin(ImportExportModelAdmin, ImportExportFormat):
	list_display = ['name','use_for_flagging','active']
	fields = ['name','use_for_flagging','active']
	search_fields = ['name', ]


@admin.register(UserLocationRelation)
class UserLocationRelationAdmin(ImportExportModelAdmin, ImportExportFormat):
	list_display = ['user','group','location_hierarchy_type', 'location_id', 'active']
	fields = ['user','group','location_hierarchy_type', 'location_id', 'active']
	search_fields = ['user', 'group']


@admin.register(Config)
class ConfigAdmin(ImportExportModelAdmin, ImportExportFormat):
	list_display = ['code','value','active']
	fields = ['code','value','active']
	search_fields = ['code']


@admin.register(ChartMeta)
class ChartMetaAdmin(ImportExportModelAdmin, ImportExportFormat):
	list_display = ['chart_type','chart_name','chart_title','vertical_axis_title','horizontal_axis_title','chart_note','chart_tooltip','active']
	fields = ['chart_type','chart_name','chart_title','vertical_axis_title','horizontal_axis_title','chart_note','chart_tooltip','active']
	search_fields = ['chart_name']