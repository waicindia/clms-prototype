from django.contrib import admin
from .models import *
from django.apps import apps
from import_export.admin import ImportExportModelAdmin, ImportExportMixin
from import_export.formats import base_formats
from import_export import resources, fields
from import_export.fields import Field


class ImportExportFormat(ImportExportMixin):
    def get_export_formats(self):
        formats = (base_formats.CSV,base_formats.XLSX,base_formats.XLS,)
        return [f for f in formats if f().can_export()]

    def get_import_formats(self):
        formats = (base_formats.CSV,base_formats.XLSX,base_formats.XLS,)
        return [f for f in formats if f().can_import()]


class GuardianInline(admin.StackedInline):
    model = Guardian
    extra = 1

class ChildShelterHomeRelationInline(admin.TabularInline):
    model = ChildShelterHomeRelation
    extra = 1

class FamilyVisitInline(admin.TabularInline):
    model = FamilyVisit
    extra = 1

class ExportResourcesClass(resources.ModelResource):
	flagged_status = fields.Field(attribute='get_%s_display' % 'flagged_status',column_name='flagged_status')
	class Meta:
		export_order = ('id','active','created_on','modified_on','child','flagged_date','reason_for_flagging','flagged_status')
		model = ChildFlaggedHistory


@admin.register(Child)
class ChildAdmin(ImportExportModelAdmin, ImportExportFormat):
	list_display = ('case_number','first_name','middle_name','last_name','dob','sex','aadhaar_number','cwc_started_the_process_of_declaring','cwc_order_number','get_child_classification','date_declaring_child_free_for_adoption','remarks','image')
	fields = ['case_number','first_name','middle_name','last_name','dob','sex','aadhaar_number','cwc_started_the_process_of_declaring','cwc_order_number','child_classification','date_declaring_child_free_for_adoption','remarks','image']
	list_filter = ['child_classification', 'sex',]
	search_fields = ['case_number', 'first_name', 'aadhaar_number']

	inlines = [GuardianInline, ChildShelterHomeRelationInline, FamilyVisitInline]

	def get_child_classification(self, obj):
		return "\n".join([a.name for a in obj.child_classification.all()])
	get_child_classification.short_description = 'child_classification'	
	get_child_classification.admin_order_field = 'child_classification'	



@admin.register(Guardian)
class GuardianAdmin(ImportExportModelAdmin, ImportExportFormat):
	list_display = ['child__case_number','name','relationship','address','contact_number','image']
	fields = ['child','name','relationship','address','contact_number','image']
	list_filter = ['relationship__name']
	a = 'child__case_number'
	search_fields = ['name', 'child__first_name', a]

	def child__case_number(self, obj):
		return f'{obj.child.first_name} - {obj.child.case_number}'
	child__case_number.short_description = 'child'	
	child__case_number.admin_order_field = 'child'



@admin.register(ChildShelterHomeRelation)
class ChildShelterhomeRelationAdmin(ImportExportModelAdmin, ImportExportFormat):
	list_display = ['child__case_number','shelter_home','admission_number','date_of_admission','date_of_exit','active']
	fields = ['child','shelter_home','admission_number','date_of_admission','date_of_exit','active']
	list_filter = ['shelter_home__name',]
	search_fields = ['child__first_name', 'child__case_number', 'child__aadhaar_number', 'shelter_home__name']

	def child__case_number(self, obj):
		return f'{obj.child.first_name} - {obj.child.case_number}'
	child__case_number.short_description = 'child'
	child__case_number.admin_order_field = 'child'



@admin.register(FamilyVisit)
class FamilyVisitAdmin(ImportExportModelAdmin, ImportExportFormat):
	list_display = ['child__case_number','guardian','date_of_visit','active']
	fields = ['child','guardian','date_of_visit','active']
	search_fields = ['child__case_number', 'child__first_name', 'guardian__name']

	def child__case_number(self, obj):
		return f'{obj.child.first_name} - {obj.child.case_number}'
	child__case_number.short_description = 'child'
	child__case_number.admin_order_field = 'child'


@admin.register(ChildFlaggedHistory)
class ChildFlaggedHistoryAdmin(ImportExportModelAdmin, ImportExportFormat):
	list_display = ['child__case_number','flagged_date','reason_for_flagging','flagged_status','active']
	fields = ['child','flagged_date','reason_for_flagging','flagged_status','active']
	search_fields = ['child__case_number', 'child__first_name',]

	def child__case_number(self, obj):
		return f'{obj.child.first_name} - {obj.child.case_number}'
	child__case_number.short_description = 'child'
	child__case_number.admin_order_field = 'child'

	def get_export_resource_class(self):
		return ExportResourcesClass	


@admin.register(ChildCWCHistory)
class ChildCWCHistoryAdmin(ImportExportModelAdmin, ImportExportFormat):
	list_display = ['child__case_number','last_date_of_cwc_order_or_review','active']
	fields = ['child','last_date_of_cwc_order_or_review','active']
	search_fields = ['child__case_number', 'child__first_name',]

	def child__case_number(self, obj):
		return f'{obj.child.first_name} - {obj.child.case_number}'
	child__case_number.short_description = 'child'	
	child__case_number.admin_order_field = 'child'