from django.core.management.base import BaseCommand, CommandError
from django.db import connection
from django.db.models import Q
import os
import datetime
from datetime import timedelta
from child_management.models import *
from master_data.models import *
from django.contrib.postgres.aggregates import BoolOr
import sys
import traceback


#****************************************************************************
# Child Flagging History storing function
#****************************************************************************
class Command(BaseCommand):
	help = 'Check child details and record any change in the flagging status or reason'
	def add_arguments(self, parser):
		parser.add_argument('-a', '--all', action='store_true', help='Create an admin account')
		
	def handle(self, *args, **options):
		review_all_children = options['all']
		import logging
		logger = logging.getLogger(__name__)
		today = datetime.date.today()
		yesterday = today - datetime.timedelta(days=1)
		cfd_value = Config.objects.get(code='cfd')
		flagging_history_script_status = Config.objects.get(code='flagging_history_script_status')
		if review_all_children == False and flagging_history_script_status == True:
			logger.info("Flagging history script is running. Multiple simulatenous runs not allowed.")
			return 
		# get the date which is x days from today.
		# x is configured in the config table with the key "cfd"
		try:
			flagging_history_script_status.value=True
			flagging_history_script_status.save()
			x_days_ago = today - datetime.timedelta(days=int(cfd_value.value))
			logger.debug("x_days_ago:" + str(x_days_ago))
			if review_all_children:
				#review all children
				# Changed from modified yesterday to active child list as the logic involves time since last visit and time since admission 
				# and these affect the status even though the child is not updated
				review_child_list = Child.objects.filter(active=2).values('id','case_number','first_name','cwc_order_number').annotate(flagstatus = BoolOr('child_classification__use_for_flagging'))
			else:
				#review all children with child details updated yesterday or today
				children_info_shelter_updated = ChildShelterHomeRelation.objects.filter(modified_on__date__gte=yesterday,active=2).values_list('child_id',flat=True)
				children_info_visit_updated = FamilyVisit.objects.filter(modified_on__date__gte=yesterday,active=2).values_list('child_id',flat=True)
				children_updated = list(set(children_info_shelter_updated) | set(children_info_visit_updated))
				review_child_list = Child.objects.filter((Q(modified_on__date__gte=yesterday) | Q(id__in=children_updated)) &  Q(active=2)).values('id','case_number','first_name','cwc_order_number').annotate(flagstatus = BoolOr('child_classification__use_for_flagging'))
				#review_child_list = Child.objects.filter(modified_on__date__gte=yesterday).values('id','case_number','first_name','cwc_order_number').annotate(flagstatus = BoolOr('child_classification__use_for_flagging'))
			logger.info("review_child_list_QUERY:"+str(review_child_list.query))
			if review_child_list:
				logger.info("review_child_list Count:"+ str(review_child_list.count()))
				for data in review_child_list:
					if data["cwc_order_number"]:
						logger.debug("1.order_number:" + data["cwc_order_number"])
						flagging_status = 2 #Legally free for adoption
						reason = "LFA order issued by the CWC"
					else: 
						child_shelter = ChildShelterHomeRelation.objects.filter(child=data['id'],active=2).order_by('date_of_admission', 'id').first()
						# if child_shelter:
						# 	logger.info("child_shelter_QUERY:" + str(child_shelter.query))
						family_visit = FamilyVisit.objects.filter(child=data['id'],active=2).order_by('-date_of_visit','-id').first()
						# if family_visit:
						# 	logger.info("family_visit_QUERY:" + str(family_visit.query))
						if child_shelter and child_shelter.date_of_admission <= x_days_ago and family_visit is None:
							logger.debug("2.date_of_admission:" + str(child_shelter.date_of_admission))
							flagging_status = 1 #Child recommended for adoption enquiry
							reason = "No family visit"
						elif child_shelter and child_shelter.date_of_admission <= x_days_ago and family_visit and family_visit.date_of_visit <= x_days_ago:
							logger.debug("3.date_of_admission:" + str(child_shelter.date_of_admission) + " date_of_visit:" + str(family_visit.date_of_visit))
							flagging_status = 1 #Child recommended for adoption enquiry
							reason = "Last family visit more than 180 days ago"
						elif data["flagstatus"] == True:
							logger.debug("4.flagstatus:" + str(data["flagstatus"]))
							flagging_status = 1 #Child recommended for adoption enquiry
							reason = "Child has no guardian or child's guardian is unfit/unintersted to raise the child"
						elif child_shelter is None:
							logger.debug("5.child_shelter: None")
							flagging_status = 3 #Not applicable
							reason = "Child's CCI information is not available"
						elif child_shelter and child_shelter.date_of_admission > x_days_ago:
							logger.debug("6.date_of_admission: "  + str(child_shelter.date_of_admission))
							flagging_status = 3 #Not applicable
							reason = "Child's stay in CCI less than 180 days and child's guardian's fitness needs to be evaluated"
						elif family_visit and family_visit.date_of_visit > x_days_ago:
							logger.debug("7.date_of_visit: "  + str(family_visit.date_of_visit))
							flagging_status = 3 #Not applicable
							reason = "Family visited in the last 180 days and child's guardian's fitness needs to be evaluated"
						else:
							logger.debug("8.else")
							flagging_status = 3 #Not applicable
							reason = "Not Applicable"

					# added a filter to check flagged date less than or equal to today to allow manual entry of flagging history for demo purpose
					# A future date flagging can be added directly for a child and 
					# this will not be overwitten by this script as this will set the flag date to today
					previous_status = ChildFlaggedHistory.objects.filter(child=data['id'],active=2).filter(flagged_date__lte=today).order_by('-id').first()
					if previous_status:
						# logger.info("previous_status_QUERY:"+str(previous_status.query))
						logger.debug("previous_status.flagged_status: " + str(previous_status.flagged_status) + " previous_status.reason_for_flagging:" + previous_status.reason_for_flagging)
					#logger.debug("flagging_status:" + str(flagging_status) + " reason:" + reason)
					logger.debug("0.child_details:" + data["case_number"] + "::::" + str(data["id"]) + "::::flagging_status:" + str(flagging_status) + " reason:" + reason)
					if previous_status is None or previous_status.flagged_status != flagging_status or previous_status.reason_for_flagging != reason:
						ChildFlaggedHistory.objects.create(
						child=Child.objects.get(id=data['id']),
						flagged_date=today,
						reason_for_flagging=reason,
						flagged_status=flagging_status,
						)
						if previous_status:
							previous_status.active = 0
							previous_status.save()
		except Exception as ex1:
			exc_type, exc_value, exc_traceback = sys.exc_info()
			error_stack = repr(traceback.format_exception(exc_type, exc_value, exc_traceback))
			logger.error(error_stack)
		finally:
			flagging_history_script_status.value=False
			flagging_history_script_status.save()