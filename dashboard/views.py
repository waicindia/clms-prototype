from __future__ import unicode_literals
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import HttpResponseRedirect, HttpResponse
from django.conf import settings
import requests
import json
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from .models import *
from django.contrib.auth.models import User ,auth
from django.db.models import Subquery
from master_data.models import *
from django.http import JsonResponse
from django.db import connection
from django.utils.encoding import smart_str
from datetime import datetime
import csv
from django.core.management import call_command
from django.http import HttpResponseRedirect

#****************************************************************************
# Login Function
#****************************************************************************
def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password =request.POST.get('password')
        user=authenticate(request,username=username, password=password)
        if user is not None:
            login(request, user)
            load_user_details_to_session(request,user)
            return HttpResponseRedirect('/dashboard/')
        else:
            msg="Invalid Username and Password"
    return render(request,'dashboard/login.html',locals())


#****************************************************************************
# Function to load user details to session
#****************************************************************************
def load_user_details_to_session(request, user):
    from django.contrib.contenttypes.models import ContentType
    location_relation = UserLocationRelation.objects.filter(user_id=user.id).first()
    user_location_id=location_relation.location_id
    location_hierarchy_type_id=location_relation.location_hierarchy_type.id

    request.session['user_location_id']=user_location_id
    request.session['location_hierarchy_type_id']=location_hierarchy_type_id
    request.session['user_name']=request.user.get_full_name()
    centre_content_type = ContentType.objects.get(app_label='master_data', model='centre')
    state_content_type = ContentType.objects.get(app_label='master_data', model='state')
    district_content_type = ContentType.objects.get(app_label='master_data', model='district')
    shelterhome_content_type = ContentType.objects.get(app_label='master_data', model='shelterhome')
    #User Level
    # if location_hierarchy_type_id==4:
    #     request.session['userlevel']="Super"
    # else:
    user_level = ContentType.objects.filter(pk = location_hierarchy_type_id).values('app_label','model').first()
    request.session['userlevel']=user_level['model'] if user_level else ""

    if request.user.is_superuser or location_hierarchy_type_id==centre_content_type.id: #Super or Center User
        request.session['user_location'] = ((0,''), (0,''), (0,''))

    elif location_hierarchy_type_id==state_content_type.id: #State User 
        state = State.objects.filter(pk = user_location_id).values('id','name','centre').first()
        request.session['user_location'] = ((state['id'],state['name']), (0,''), (0,''))

    elif location_hierarchy_type_id==district_content_type.id: #District User
        district = District.objects.filter(pk = user_location_id).values('id','name','state').first()
        state = State.objects.filter(pk = district['state']).values('id','name','centre').first()
        request.session['user_location'] = ((state['id'],state['name']), (district['id'],district['name']), (0,''))

    elif location_hierarchy_type_id==shelterhome_content_type.id: #Shelterhome User
        shelter_home = ShelterHome.objects.filter(pk = user_location_id).values('id','name','district').first()
        district = District.objects.filter(pk = shelter_home['district']).values('id','name','state').first()
        state = State.objects.filter(pk = district['state']).values('id','name','centre').first()
        request.session['user_location'] = ((state['id'],state['name']), (district['id'],district['name']), (shelter_home['id'],shelter_home['name'])) 


#****************************************************************************
# Logout Function
#****************************************************************************
def logout_view(request):
    logout(request)
    return HttpResponseRedirect('/login/')  


#****************************************************************************
# Pagination Function
#****************************************************************************
def pagination_function(request,data):
    records_per_page = Config.objects.get(code='report_records_per_page')
    #t = tuple(data.items())
    paginator = Paginator(data, records_per_page.value)
    page = request.GET.get('page',1)
    try:
        pagination = paginator.page(page)
    except PageNotAnInteger:
        pagination = paginator.page(1)
    except EmptyPage:
        pagination = paginator.page(paginator.num_pages)
    return pagination


#****************************************************************************
# Raw SQL
#****************************************************************************
def return_sql_results(sql):
  cursor = connection.cursor()
  cursor.execute(sql)
  descr = cursor.description
  rows = cursor.fetchall()
  data = [dict(zip([column[0] for column in descr], row)) for row in rows]

  return data
  

#****************************************************************************
# update pie chart data to replace dummy data with actual values
#****************************************************************************
def set_pie_chart_data(sql, data):
    cursor = connection.cursor()
    cursor.execute(sql)
    #descr = cursor.description
    rows = cursor.fetchall()
    #data = [dict(zip([column[0] for column in descr], row)) for row in rows]
    counter = 0
    #all queries always return one row - even when no data exists
    row = rows[0]
    for item in list(row):
        counter = counter + 1
        data[counter][1] = item
    return data

#****************************************************************************
# update column chart data  and labels to replace dummy data with actual values
# labels only for dynamic bars - last 6 months kind of charts
#****************************************************************************
def set_column_chart_data(sql, data, labels, bar_colors):
    cursor = None
    try:
        cursor = connection.cursor()
        cursor.execute(sql)
        rows = cursor.fetchall()
        counter = 0
        data[0].append({'role':'style'})
        #all queries always return one row - even when no data exists
        row = rows[0]
        for item in list(row):
            counter = counter + 1
            data[counter][1] = item
            data[counter].append(bar_colors[counter-1])
            if labels is not None and labels != []:
                data[counter][0] = labels[counter-1]
    finally:
        if cursor:
            cursor.close()
    return data


#****************************************************************************
# update table chart data to replace dummy data with actual values
#****************************************************************************
def set_table_chart_data(sql, data):
    cursor = connection.cursor()
    cursor.execute(sql)
    rows = cursor.fetchall()
    newdata = []
    newdata.append(data[0])
    for row in rows:
        #newdata.append(list(map(str, list(row))))
        newdata.append(list(row))
    return newdata

#****************************************************************************
# update table chart data to replace dummy data with actual values
# labels only for dynamic bars - top 5 recommended adoption
#****************************************************************************
def set_bar_chart_data_and_labels(sql, data, bar_colors):
    cursor = None
    try:
        cursor = connection.cursor()
        cursor.execute(sql)
        rows = cursor.fetchall()
        counter = 0
        data[0].append({'role':'style'})
        #all queries always return one row - even when no data exists
        #clear all data from the data list except for the first element
        data = data[:1]
        url_keys = []
        for row in rows:
            #for item in row:
            bar_info  = []
            counter = counter + 1
            row_data = list(row)
            #set label
            bar_info.append(row_data[0].replace('_','\n').replace('-','\n'))
            bar_info.append(row_data[1])
            bar_info.append(bar_colors[counter-1])
            if len(row_data) == 3:
                #add the ids to the url_keys - state_id, district_id, shelter_home_id based on the filters
                url_keys.append(row_data[2])
            # data[counter][0] = row_data[0]
            # #set value
            # data[counter][1] = row_data[1]
            # #set color for bar
            # data[counter].append(bar_colors[counter-1])
            data.append(bar_info)
    finally:
        if cursor:
            cursor.close()
    return data, url_keys

#****************************************************************************
# Dropdown Filter Condition
#****************************************************************************
def filter_condtition(request,sql_query):
    state_id, district_id, shelter_home_id = 0, 0, 0
    if request.method == "POST":
        state_id = request.POST.get('state')
        district_id = request.POST.get('district')
        shelter_home_id = request.POST.get('shelter_home')
    elif request.method == "GET":
        state_id = request.GET.get('state')
        district_id = request.GET.get('district')
        shelter_home_id = request.GET.get('shelter_home')    

    #assigned user_location is a tuple of ((state_id,state_name), (district_id, district_name), (shelter_home_id, shelter_home_name)) for any user. 
    #Admin will have ((0,''), (0,''), (0,''))
    assigned_location = request.session.get('user_location')
    #if user location is none, in case user has logged in on the /admin django admin page and opened the dashboard url
    # session values will not set 
    if assigned_location is None:
        load_user_details_to_session(request,request.user)
        assigned_location = request.session.get('user_location')
    if state_id is None or state_id == 0:
        state_id = assigned_location[0][0]
    if district_id is None or district_id == 0:
        district_id = assigned_location[1][0]
    if shelter_home_id is None or shelter_home_id == 0:
        shelter_home_id = assigned_location[2][0]
    
    state_cond = ""
    district_cond = ""
    shelter_cond = ""
    if state_id and state_id != 0:
        state_cond = " and state_id = " + str(state_id)
    if district_id and district_id != 0:
        district_cond = " and district_id = " + str(district_id)
    if shelter_home_id and shelter_home_id != 0:
        shelter_cond = " and shelter_home_id = " + str(shelter_home_id)
    sql_query = sql_query.replace("@@state_filter",state_cond).replace("@@district_filter",district_cond).replace("@@shelter_filter",shelter_cond)
    return sql_query

#****************************************************************************
# Function to get locations based on user role/mapping and dropdown selection
#****************************************************************************
@login_required(login_url='/login/')
def get_user_locations_data(request):
    if request.method == "POST":
        state_id = request.POST.get('state') if request.POST.get('state') else 0
        district_id = request.POST.get('district') if request.POST.get('district') else 0
        shelter_home_id = request.POST.get('shelter_home') if request.POST.get('shelter_home') else 0
    elif request.method == "GET":
        state_id = request.GET.get('state') if request.GET.get('state') else 0
        district_id = request.GET.get('district') if request.GET.get('district') else 0
        shelter_home_id = request.GET.get('shelter_home') if request.GET.get('shelter_home') else 0
    state_list = []
    district_list = []
    shelter_home_list = []

    #assigned user_location is a tuple of ((state_id,state_name), (district_id, district_name), (shelter_home_id, shelter_home_name)) for any user. 
    #Admin will have ((0,''), (0,''), (0,''))
    assigned_location = request.session.get('user_location')
    #if user location is none, in case user has logged in on the /admin django admin page and opened the dashboard url
    # session values will not set 
    if assigned_location is None:
      load_user_details_to_session(request,request.user)
      assigned_location = request.session.get('user_location')
      
    if assigned_location[0][0] != 0:
      state_id = assigned_location[0][0]
      state_list = [{'id':state_id,'name':assigned_location[0][1]}]
    if assigned_location[1][0] != 0:
      district_id = assigned_location[1][0]
      district_list = [{'id':district_id,'name':assigned_location[1][1]}]
    if assigned_location[2][0] != 0:
      shelter_home_id = assigned_location[2][0]
      shelter_home_list = [{'id':shelter_home_id,'name':assigned_location[2][1]}]
    if state_list == []:
      state_list = list(State.objects.values('id','name').order_by('name'))
    if district_list == []:
      district_list = list(District.objects.filter(state = state_id).values('id','name').order_by('name'))
    if shelter_home_list == []:
      shelter_home_list = list(ShelterHome.objects.filter(district = district_id).values('id','name').order_by('name'))
    return {'state_list':state_list, 'district_list':district_list, 'shelter_home_list':shelter_home_list, "state_id":state_id, "district_id":district_id, "shelter_home_id":shelter_home_id}


#****************************************************************************
# Dashboard
#****************************************************************************
@login_required(login_url='/login/')
def dashboard(request):
    # if 'user_location' not in request.session:
    #     if request.user.is_superuser:
    #         request.session['user_location'] = ((0,''), (0,''), (0,''))
        
    #state = get_state(request)
    user_location = get_user_locations_data(request)
    #print(user_location)
    hide_charts = []

    #retaining dropdown values
    states_id=""
    districts_id=""
    shelter_homes_id=""
    if request.POST.get('state'):
        states_id = int(request.POST.get('state'))
    elif user_location["state_id"] != 0:
        states_id = user_location["state_id"]
    if request.POST.get('district'):
        districts_id = int(request.POST.get('district'))
    elif user_location["district_id"] != 0:
        districts_id = user_location["district_id"]
    if request.POST.get('shelter_home'):
        shelter_homes_id = int(request.POST.get('shelter_home'))
    elif user_location["shelter_home_id"] != 0:
        shelter_homes_id = user_location["shelter_home_id"]
 
    data_values_from_db = {"last_contact_with_family":[],"recommended_adoption_view":[], "stay_since_adoption_inquiry":[], "stay_in_cci":[], "last_review_by_cwc":[],"child_adpotion_status":[],"categories_in_cci":[]}
    
    data_meta = { "chart":{"last_contact_with_family":{
                        "chart_title":"Child’s Last Contact with Family",
                        "chart_height": "400px",
                        "bar_colors":['#FF3333', '#32B517', '#FFEA00', '#FFAA00', '#FF3333'],
                        "on_click_urls": [],
                        "on_click_handler": "",
                        "datas": [['', ''],['No family contact',  37],['Less than 6 months ago',  10],['More than 6 months ago',  25],['More than 1 year ago',  59],['More than 2 years ago',  18]],
                        "options": {
                                      "chart": {
                                        "title": '',
                                        "subtitle": '',
                                      },
                                      "legend": { "position": 'none', "alignment": 'end', },
                                       "hAxis": { "title": "",  },
                                       "chartArea": { 'width': '90%', 'height': '90%', 'top': '5%', 'left': '10%', 'bottom': '50'},
                                       "vAxis": {
                                                "minValue":"0","format":"0","title": "Number of children","gridlines": { 'color': '#eee6ff', 'count': 10, }, "titleTextStyle": {"fontSize": 14,'italic': 'false'}, "viewWindow":{"min":"0"},
                                            },
                                        "annotations":{
                                            "alwaysOutside": "true",
                                            "datum":{
                                                "stem":{
                                                    "color":'transparent',
                                                    "length":'2',
                                                }
                                            },
                                            "textStyle":{
                                                "color": 'black',
                                                "bold": 'true',
                                            },
                                        }
                                    },
                        "chart_type": "COLUMNCHART",
                        "div": "col-md-6",
                      },
                      "recommended_adoption_view":{
                        "chart_title":"Children Recommended for Adoption Inquiry",
                        "chart_height": "400px",
                        "bar_colors":['#FFAA00','#FFAA00','#FFAA00','#FFAA00','#FFAA00','#FFAA00'],
                        "on_click_urls": [],
                        "on_click_handler": "recommended_adoption_view_click_handler",
                        "datas": [['', ''],["Feb '21",  30],["Jan '21",  50],["Dec '20",  20],["Nov '20",  10],["Oct '20",  40],],
                        "options": {
                                      "chart": {
                                        "title": '',
                                        "subtitle": '',
                                      },
                                      "legend": { "position": 'none', "alignment": 'end', },
                                       "vAxis": { "title": "",  },
                                       "chartArea": { 'width': '75%', 'height': '90%', 'top': '5%', 'left': '100', 'bottom': '10%', 'right':'10%'},
                                       "hAxis": {
                                                "minValue":"0","format":"0","title": "Number of Children Flagged","gridlines": { 'color': '#eee6ff', 'count': 10, }, "titleTextStyle": {"fontSize": 14,'italic': 'false'},"viewWindow":{"min":"0"},
                                            },
                                        "annotations":{
                                            "alwaysOutside": "true",
                                            "datum":{
                                                "stem":{
                                                    "color":'transparent',
                                                    "length":'2',
                                                }
                                            },
                                            "textStyle":{
                                                "color": 'black',
                                                "bold": 'true',
                                            },
                                        },
                                        'bar': { 'groupWidth': '40' },
                                    },
                        "chart_type": "BARCHART",
                        "div": "col-md-6",
                      },
                      "stay_since_adoption_inquiry":{
                        "chart_title":"Length of Time Since the Adoption Inquiry is Pending",
                        "chart_height": "400px",
                        "bar_colors":['#32B517','#FFEC19', '#FFAA00', '#FF3333'],
                        "on_click_urls": [],
                        "on_click_handler": "",
                        "datas": [['', ''],['0-6 months',  2],['More than 6 months', 3],['More than 1 year',  251],['More than 2 years',  1021], ],
                        "options": {
                                      "chart": {
                                        "title": '',
                                        "subtitle": '',
                                      },
                                      "legend": { "position": 'none', "alignment": 'end', },
                                       "hAxis": { "title": "",  },
                                       "width": "95%",
                                       "height": "95%",
                                       "chartArea": { 'width': '80%', 'height': '90%', 'top': '5%', 'left': '10%', 'bottom': '50'},
                                       "vAxis": {
                                                "format":"0","title": "Number of children","gridlines": { 'color': '#eee6ff'}, "titleTextStyle": {'fontSize':'14','italic': 'false'},
                                            },
                                        "annotations":{
                                            "alwaysOutside": "true",
                                            "datum":{
                                                "stem":{
                                                    "color":'transparent',
                                                    "length":'2',
                                                }
                                            },
                                            "textStyle":{
                                                "color": 'black',
                                                "bold": 'true',
                                            },
                                        }
                                    },
                        "chart_type": "COLUMNCHART",
                        "div": "col-md-6",
                      },
                      "stay_in_cci":{
                        "chart_title":"Children’s Length of Stay in Child Care Institutions (CCIs)",
                        "chart_height": "400px",
                        "on_click_urls": [],
                        "on_click_handler": "",
                        "datas": [['', ''],['<= 6 months', 1],['> 6 months and <= 1 year', 5],['1-3 years', 50],['3-5 years', 41],['> 5 years', 83],],
                        "options": {
                                      "chart": {
                                        "title": '',
                                        "subtitle": '',
                                      },
                                      "legend": { "position": 'left', "maxLines": "3"},
                                      "pieSliceText": 'value-and-percentage',
                                      "title": '% of Children',
                                      "colors": ['#32B517','#FFAA00','#19B2FF','#6C5EE6','#FF3333'],
                                       "chartArea": { 'width': '95%', 'height': '80%', 'top': '15%', 'bottom': '10%'},
                                    },
                        "chart_type": "PIECHART",
                        "div": "col-md-6",
                      },
                      "last_review_by_cwc":{
                        "chart_title":"Last Review of Child’s Case by the Child Welfare Committee (CWC)",
                        "chart_height": "400px",
                        "on_click_urls": [],
                        "on_click_handler": "",
                        "datas": [['', ''],['0-3 months ago', 46],['3-6 months ago', 46],['6-9 months ago', 42], ['9-12 months ago', 21], ['> 1 year ago', 42],],
                        "options": {
                                      "chart": {
                                        "title": '',
                                        "subtitle": '',
                                      },
                                      "legend": { "position": 'left', "maxLines": "3"},
                                      "pieSliceText": 'value-and-percentage',
                                      "title": '% of Children',
                                      "colors": ['#32B517','#FFAA00','#19B2FF','#6C5EE6','#FF3333'],
                                       "chartArea": { 'width': '95%', 'height': '80%', 'top': '15%', 'bottom': '10%'},
                                    },
                        "chart_type": "PIECHART",
                        "div": "col-md-6",
                      },
                      "child_adpotion_status":{
                        "chart_title":"Children Adpotion Status",
                        "chart_height": "400px",
                        "on_click_urls": [],
                        "on_click_handler": "",
                        "datas": [['', ''],['Recommended for Adoption Inquiry', 46],['Legally Free for Adoption', 46],['Other Children', 42],['Not Flagged',0]],
                        "options": {
                                      "chart": {
                                        "title": '',
                                        "subtitle": '',
                                      },
                                      "legend": { "position": 'left', "maxLines": "3"},
                                      "pieSliceText": 'value-and-percentage',
                                      "title": '% of Children',
                                      "colors": ['#FFAA00', '#32B517','#19B2FF','#898376'],
                                       "chartArea": { 'width': '95%', 'height': '80%', 'top': '15%', 'bottom': '10%'},
                                    },
                        "chart_type": "PIECHART",
                        "div": "col-md-6",
                      },
                      "categories_in_cci":{
                        "chart_title":"Categories of Children in Child Care Institutions (CCIs)",
                        "chart_height": "220px",
                        "on_click_urls": [],
                        "on_click_handler": "",
                        "datas": [['State','Total No. of <br/>Children', 'Abandoned', 'Orphaned - <br/>No Guardians', 'Orphaned - <br/>Unfit Guardians', 'Children with <br/>Unfit Parents','Trafficked', 'Surrendered','Children with <br/>Fit Guardians'],['Assam',  10, 1, 8, 2, 4, 5, 8, 12],['Bihar',  14, 11, 2, 8, 2, 8, 10, 11],['Chhattisgarh',  12, 1, 12, 0, 2, 2, 1, 2],['Goa',  21, 12, 7, 4, 2, 2, 19, 12],['Gujarat',  20, 10, 8, 5, 4, 2, 8, 4],['Haryana',  10, 5, 7, 6, 8, 7, 4, 7],['Jharkhand', 20, 15, 2, 8, 8, 5, 5, 8],['Karnataka', 45, 25, 0, 2, 0, 1, 1, 21],['Kerala',  10, 1, 8, 2, 4, 5, 8, 12],['Maharashtra',  14, 11, 2, 8, 2, 8, 10, 11],['Nagaland',  12, 1, 12, 0, 2, 2, 1, 2],['Punjab',  21, 12, 7, 4, 2, 2, 19, 12],['Sikkim',  20, 10, 8, 5, 4, 2, 8, 4],['Tamil Nadu',  10, 5, 7, 6, 8, 7, 4, 7],['Telangana', 20, 15, 2, 8, 8, 5, 5, 8],['Uttar Pradesh', 45, 25, 0, 2, 0, 1, 1, 21]],
                        "options": {
                                    "allowHtml": "true",
                                    "showRowNumber": 'true',
                                    "width": '100%', 
                                    "height": '200px',
                                    "cssClassNames": {"tableCell":"tableCell", "headerCell":"headerCell","oddTableRow":"oddTableRow","selectedTableRow":"selectedTableRow","hoverTableRow":"hoverTableRow"},
                                    },
                        "chart_type": "TABLECHART",
                        "div": "col-md-12",
                      }}
            }

    #pie chart - widget #7 - last_review_by_cwc - Last Review of Child’s Case by the Child Welfare Committee (CWC) 
    last_review = """select coalesce(sum(case when (num_months_last_review < 3 or (num_months_last_review = 3 and additional_days_last_review = 0)) then 1 else 0 end),0) as less_than_three,
                        coalesce(sum(case when ((num_months_last_review = 3 and additional_days_last_review > 0) or (num_months_last_review > 3 and num_months_last_review < 6) or (num_months_last_review = 6 and additional_days_last_review = 0)) then 1 else 0 end),0) as three_to_six_months,
                        coalesce(sum(case when ((num_months_last_review = 6 and additional_days_last_review > 0) or (num_months_last_review > 6 and num_months_last_review < 9) or (num_months_last_review = 9 and additional_days_last_review = 0)) then 1 else 0 end),0) as six_to_nine_months,
                        coalesce(sum(case when ((num_months_last_review = 9 and additional_days_last_review > 0) or (num_months_last_review > 9 and num_months_last_review < 12) or (num_months_last_review = 12 and additional_days_last_review = 0)) then 1 else 0 end),0) as nine_months_to_year,
                        coalesce(sum(case when ((num_months_last_review = 12 and additional_days_last_review > 0) or num_months_last_review > 12) then 1 else 0 end),0) as greater_than_one_year
                        from dash_child_days_lastreview_view
                        where 1=1 @@state_filter @@district_filter @@shelter_filter"""
    last_review = filter_condtition(request,last_review)
    data_values_from_db["last_review_by_cwc"] = set_pie_chart_data(last_review, data_meta["chart"]["last_review_by_cwc"]["datas"])

    #pie chart - widget #6 - stay_in_cci - Children’s Length of Stay in Child Care Institutions (CCIs)
    len_of_stay = """select coalesce(sum(case when (((stay_in_months + floor(additional_days/30::numeric)) < 6) or ((stay_in_months + floor(additional_days/30::numeric)) = 6 and additional_days::int%30 = 0)) then 1 else 0 end),0) as less_than_six,
                        coalesce(sum(case when (((stay_in_months + floor(additional_days/30::numeric)) = 6 and additional_days::int%30 > 0) or ((stay_in_months + floor(additional_days/30::numeric)) > 6 and (stay_in_months + floor(additional_days/30::numeric)) < 12) or ((stay_in_months + floor(additional_days/30::numeric)) = 12 and additional_days::int%30 = 0)) then 1 else 0 end),0) as six_months_to_one_year,
                        coalesce(sum(case when (((stay_in_months + floor(additional_days/30::numeric)) = 12 and additional_days::int%30 > 0) or ((stay_in_months + floor(additional_days/30::numeric)) > 12 and (stay_in_months + floor(additional_days/30::numeric)) < 36) or ((stay_in_months + floor(additional_days/30::numeric)) = 36 and additional_days::int%30 = 0)) then 1 else 0 end),0) as one_to_three_year,
                        coalesce(sum(case when (((stay_in_months + floor(additional_days/30::numeric)) = 36 and additional_days::int%30 > 0) or ((stay_in_months + floor(additional_days/30::numeric)) > 36 and (stay_in_months + floor(additional_days/30::numeric)) < 60) or ((stay_in_months + floor(additional_days/30::numeric)) = 60 and additional_days::int%30 = 0)) then 1 else 0 end),0) as three_to_five_year,
                        coalesce(sum(case when (((stay_in_months + floor(additional_days/30::numeric)) = 60 and additional_days::int%30 > 0) or ((stay_in_months + floor(additional_days/30::numeric)) > 60)) then 1 else 0 end),0) as greater_than_five_year
                        from (
                            select dcc.child_id, sum(dcc.stay_in_months) as stay_in_months, sum(additional_days) as additional_days
                            from dash_child_cci_stay_view dcc
                            inner join(select row_number() over (partition by child_id order by date_of_admission desc) as shelter_num, shelter_home_id as recent_shelter_home_id, child_id, admission_number, date_of_admission
                                        from  child_management_childshelterhomerelation 
                                        where active = 2
                            ) csr on dcc.child_id = csr.child_id and csr.shelter_num = 1 and dcc.shelter_home_id = csr.recent_shelter_home_id
                            where 1=1 @@state_filter @@district_filter @@shelter_filter
                            group by dcc.child_id
                        ) as x"""
    len_of_stay = filter_condtition(request,len_of_stay)
    data_values_from_db["stay_in_cci"] = set_pie_chart_data(len_of_stay, data_meta["chart"]["stay_in_cci"]["datas"])

    #pie chart - widget #4 - child_adpotion_status - Children Adpotion Status
    adpotion_status = """select coalesce(sum(case when flagged_status = 1 then 1 else 0 end),0) as recommended_for_adoption,
                            coalesce(sum(case when flagged_status = 2 then 1 else 0 end),0) as legally_free_for_adoption,
                            coalesce(sum(case when flagged_status = 3 then 1 else 0 end),0) as not_applicable,
                            coalesce(sum(case when flagged_status is null or flagged_status not in (1,2,3) then 1 else 0 end),0) as not_flagged
                            from (
                                select child_id, flagged_status
                                from dash_child_adpotion_status_view 
                                where 1=1 @@state_filter @@district_filter @@shelter_filter
                            ) as x"""
    adpotion_status = filter_condtition(request,adpotion_status)
    data_values_from_db["child_adpotion_status"] = set_pie_chart_data(adpotion_status, data_meta["chart"]["child_adpotion_status"]["datas"])
    
    #column chart - widget #1 - last_contact_with_family - Child’s Last Contact with Family
    last_contact = """select coalesce(sum(case when num_months_last_visit = -1 then 1 else 0 end),0) as no_fam_contact,
                        coalesce(sum(case when ((num_months_last_visit >= 0 and num_months_last_visit < 6) or (num_months_last_visit = 6 and additional_days_last_visit = 0)) then 1 else 0 end),0) as less_six_months,
                        coalesce(sum(case when ((num_months_last_visit = 6 and additional_days_last_visit > 0) or (num_months_last_visit > 6 and num_months_last_visit < 12) or (num_months_last_visit = 12 and additional_days_last_visit = 0)) then 1 else 0 end),0) as six_months_to_one_year,
                        coalesce(sum(case when ((num_months_last_visit = 12 and additional_days_last_visit > 0) or (num_months_last_visit > 12 and num_months_last_visit < 24) or (num_months_last_visit = 24 and additional_days_last_visit = 0)) then 1 else 0 end),0) as more_one_year,
                        coalesce(sum(case when ((num_months_last_visit = 24 and additional_days_last_visit > 0) or (num_months_last_visit > 24)) then 1 else 0 end),0) as greater_than_two_year
                        from dash_child_days_lastvisit_view
                        where 1=1 @@state_filter @@district_filter @@shelter_filter"""
    last_contact = filter_condtition(request,last_contact)
    data_values_from_db["last_contact_with_family"] = set_column_chart_data(last_contact, data_meta["chart"]["last_contact_with_family"]["datas"], [], data_meta["chart"]["last_contact_with_family"]["bar_colors"])

    #column chart - widget #2 - recommended_adoption_view - Children Recommended for Adoption Inquiry
    # adopt_inquiry = """select x1.month_key, sum(case when x2.child_id is null then 0 else 1 end)
    #                     from (
    #                         select to_char((to_date(to_char(now(),'YYYY-MM-01'),'YYYY-MM-DD') - cast(mn||' months' as interval)), 'Mon ''YY') month_key
    #                         from (select generate_series(0,5) as mn ) as a1
    #                     ) as x1
    #                     left outer join dash_recommended_adoption_view x2 on x2.reco_ready_month = x1.month_key and reco_ready_date >= (to_date(to_char(now(),'YYYY-MM-01'),'YYYY-MM-DD') - interval '5 months') 
    #                     where 1 = 1 @@state_filter @@district_filter @@shelter_filter
    #                     group by x1.month_key"""
    # adopt_inquiry = """select coalesce(sum(case when reco_ready_month = to_char(now(),'Mon ''YY') then 1 else 0 end),0) as current_month,
    #                     coalesce(sum(case when reco_ready_month = to_char((to_date(to_char(now(),'YYYY-MM-01'),'YYYY-MM-DD') - interval '1 months'), 'Mon ''YY') then 1 else 0 end),0) as month_minus_one,
    #                     coalesce(sum(case when reco_ready_month = to_char((to_date(to_char(now(),'YYYY-MM-01'),'YYYY-MM-DD') - interval '2 months'), 'Mon ''YY') then 1 else 0 end),0) as month_minus_two,
    #                     coalesce(sum(case when reco_ready_month = to_char((to_date(to_char(now(),'YYYY-MM-01'),'YYYY-MM-DD') - interval '3 months'), 'Mon ''YY') then 1 else 0 end),0) as month_minus_three,
    #                     coalesce(sum(case when reco_ready_month = to_char((to_date(to_char(now(),'YYYY-MM-01'),'YYYY-MM-DD') - interval '4 months'), 'Mon ''YY') then 1 else 0 end),0) as month_minus_four
    #                     from dash_recommended_adoption_view
    #                     where reco_ready_date >= (to_date(to_char(now(),'YYYY-MM-01'),'YYYY-MM-DD') - interval '4 months')
    #                     @@state_filter @@district_filter @@shelter_filter """
    # adopt_inquiry = filter_condtition(request,adopt_inquiry)
    #create labels for last 6 months including current month
    # labels = []
    # cursor = None
    # try:
    #     labels_sql = """select to_char((to_date(to_char(now(),'YYYY-MM-01'),'YYYY-MM-DD') - cast(mn||' months' as interval)), 'Mon ''YY') month_key
    #                 from (select generate_series(0,4) as mn ) as a1"""
    #     cursor = connection.cursor()
    #     cursor.execute(labels_sql)
    #     result = cursor.fetchall()
    #     for row in result:
    #         labels.append(row[0])
    #     #labels = ["Shelter005_TS_Medchal-Malkajgiri", "Shelter001_TS_Medchal-Malkajgiri","Shelter001_TS_Hyderabad","Shelter001_MH_Mumbai City","Shelter005_TS_Nizamabad","Shelter004_TS_Nalgonda"]
    #     #labels = ["Shelter005\nTS\nMedchal Malkajgiri", "Shelter001\nTS\nMedchal Malkajgiri","Shelter001\nTS\nHyderabad","Shelter001\nMH\nMumbai City","Shelter005\nTS\nNizamabad"]
         
    # finally:
    #     if cursor:
    #         cursor.close()
    # data_values_from_db["recommended_adoption_view"] = set_column_chart_data(adopt_inquiry, data_meta["chart"]["recommended_adoption_view"]["datas"], labels, data_meta["chart"]["recommended_adoption_view"]["bar_colors"])

    #column chart - widget #2 - Children Recommended for Adoption Inquiry
    if states_id == "":
        recommended_adoption_view = """select state_name, coalesce(count(*),0) as num_recommended, state_id
                                        from dash_recommended_adoption_view
                                        where 1=1 and flagged_status = 1 group by state_name, state_id order by count(*) desc, state_name limit 5"""
        url_template = '/custom-report/?page=1&state={0}&district=&shelter_home='
    elif states_id != "" and districts_id == "":
        recommended_adoption_view = """select district_name, coalesce(count(*),0) as num_recommended, district_id
                                        from dash_recommended_adoption_view
                                        where 1=1 and flagged_status = 1 @@state_filter group by district_name,district_id order by count(*) desc, district_name limit 5"""
        url_template = '/custom-report/?page=1&state=' + str(states_id) + '&district={0}&shelter_home='
    elif districts_id != "" and shelter_homes_id == "":
        recommended_adoption_view = """select shelter_homename, coalesce(count(*),0) as num_recommended, shelter_home_id
                                        from dash_recommended_adoption_view
                                        where 1=1 and flagged_status = 1 @@state_filter @@district_filter group by shelter_homename,shelter_home_id order by count(*) desc, shelter_homename limit 5"""
        url_template = '/custom-report/?page=1&state=' + str(states_id) + '&district=' + str(districts_id) + '&shelter_home={0}'
    elif districts_id != "" and shelter_homes_id != "":
        recommended_adoption_view = """select shelter_homename, coalesce(count(*),0) as num_recommended,shelter_home_id
                                        from dash_recommended_adoption_view
                                        where 1=1 and flagged_status = 1 @@state_filter @@district_filter @@shelter_filter group by shelter_homename,shelter_home_id order by count(*) desc, shelter_homename limit 5"""
        url_template = '/custom-report/?page=1&state=' + str(states_id) + '&district=' + str(districts_id) + '&shelter_home={0}'
    recommended_adoption_view = filter_condtition(request,recommended_adoption_view)
    data_values_from_db["recommended_adoption_view"], url_keys = set_bar_chart_data_and_labels(recommended_adoption_view, data_meta["chart"]["recommended_adoption_view"]["datas"], data_meta["chart"]["recommended_adoption_view"]["bar_colors"])
    # urls contain the list of urls for each bar in the barchart - on click of the bar, the url will open in new window/tab
    on_click_urls = []
    for id in url_keys:
        on_click_urls.append(url_template.format(id))
    data_meta["chart"]["recommended_adoption_view"]["on_click_urls"] = on_click_urls

    #column chart - widget #3 - Length of Time Since the Adoption Inquiry is Pending 
    adopt_inquiry_pending = """select coalesce(sum(case when (reco_ready_in_months < 6 or (reco_ready_in_months = 6 and additional_days_reco_ready = 0)) then 1 else 0 end),0) as zero_to_six_month,
                                coalesce(sum(case when ((reco_ready_in_months = 6 and additional_days_reco_ready > 0) or (reco_ready_in_months > 6 and reco_ready_in_months < 12) or (reco_ready_in_months = 12 and additional_days_reco_ready = 0)) then 1 else 0 end),0) as six_months_to_one_year,
                                coalesce(sum(case when ((reco_ready_in_months = 12 and additional_days_reco_ready > 0) or (reco_ready_in_months > 12 and reco_ready_in_months < 24) or (reco_ready_in_months = 24 and additional_days_reco_ready = 0)) then 1 else 0 end),0) as one_to_two_year,
                                coalesce(sum(case when ((reco_ready_in_months = 24 and additional_days_reco_ready > 0) or reco_ready_in_months > 24) then 1 else 0 end),0) as greater_than_two_year
                                from (
                                    select child_id, extract( year  from (age(now()::TIMESTAMP, reco_ready_date::TIMESTAMP))) * 12 + 
                                    extract( month  from (age(now()::TIMESTAMP, reco_ready_date::TIMESTAMP))) as reco_ready_in_months,
                                    extract( days from (age(now()::TIMESTAMP, reco_ready_date::TIMESTAMP))) as additional_days_reco_ready
                                    from dash_recommended_adoption_view 
                                    where 1=1 and flagged_status = 1 @@state_filter @@district_filter @@shelter_filter
                                ) as x"""
    adopt_inquiry_pending = filter_condtition(request,adopt_inquiry_pending)
    data_values_from_db["stay_since_adoption_inquiry"] = set_column_chart_data(adopt_inquiry_pending, data_meta["chart"]["stay_since_adoption_inquiry"]["datas"], [], data_meta["chart"]["stay_since_adoption_inquiry"]["bar_colors"])

    # #pie chart - widget #5 - Categories of Children in Child Care Institutions (CCIs)
    child_category = ""
    if states_id == "":
        # display the state chart for admin and center user when the state filter is not selected
        # #child_category_state
        child_category= """select state_name, coalesce(sum(child_count),0)::integer as total_children,
                                sum(abandoned_count + fam_not_trace_count)::integer as abandoned_count,
                                sum( orp_no_guardian_count)::integer as  orp_no_guardian_count,
                                sum( unfit_guardian_poverty_count + unfit_guardian_addict_count + unfit_guardian_abuse_count + unfit_guardian_criminal_count + unfit_guardian_unsound_count + unfit_guardian_needcare_count + unfit_guardian_unwilling_count)::integer as unfit_guardian_count,
                                sum( unfit_parent_poverty_count + unfit_parent_single_count + unfit_parent_addict_count + unfit_parent_abuse_count + unfit_parent_criminal_count + unfit_parent_unsound_count + unfit_parent_needcare_count + unfit_parent_unwilling_count)::integer as  unfit_parent_count,
                                sum( was_trafficked_count)::integer as  was_trafficked_count,
                                sum( surrendered_count)::integer as  surrendered_count,
                                sum(orp_fit_guardian_count + fit_parent_count)::integer as fit_guardian_parent_count
                                from dash_child_cci_category 
                                group by state_name"""
        data_meta["chart"]["categories_in_cci"]["datas"][0][0] = 'State'
    elif states_id != "" and districts_id == "":
        # display the district chart for state user or admin/center user when state_id is selected
        # #child_category_district
        child_category = """select district_name, coalesce(sum(child_count),0)::integer as total_children,
                                    sum(abandoned_count + fam_not_trace_count)::integer as abandoned_count,
                                    sum( orp_no_guardian_count)::integer as  orp_no_guardian_count,
                                    sum( unfit_guardian_poverty_count + unfit_guardian_addict_count + unfit_guardian_abuse_count + unfit_guardian_criminal_count + unfit_guardian_unsound_count + unfit_guardian_needcare_count + unfit_guardian_unwilling_count)::integer as unfit_guardian_count,
                                    sum( unfit_parent_poverty_count + unfit_parent_single_count + unfit_parent_addict_count + unfit_parent_abuse_count + unfit_parent_criminal_count + unfit_parent_unsound_count + unfit_parent_needcare_count + unfit_parent_unwilling_count)::integer as  unfit_parent_count,
                                    sum( was_trafficked_count)::integer as  was_trafficked_count,
                                    sum( surrendered_count)::integer as  surrendered_count,
                                    sum(orp_fit_guardian_count + fit_parent_count)::integer as fit_guardian_parent_count
                                    from dash_child_cci_category 
                                    where 1=1 @@state_filter
                                    group by district_name"""
        data_meta["chart"]["categories_in_cci"]["datas"][0][0] = 'District'
    elif districts_id != "" and shelter_homes_id == "":
        # display the district chart for state user or admin/center user when state_id is selected
        # #child_category_district
        child_category = """select shelter_homename, coalesce(sum(child_count),0)::integer as total_children,
                                    sum(abandoned_count + fam_not_trace_count)::integer as abandoned_count,
                                    sum( orp_no_guardian_count)::integer as  orp_no_guardian_count,
                                    sum( unfit_guardian_poverty_count + unfit_guardian_addict_count + unfit_guardian_abuse_count + unfit_guardian_criminal_count + unfit_guardian_unsound_count + unfit_guardian_needcare_count + unfit_guardian_unwilling_count)::integer as unfit_guardian_count,
                                    sum( unfit_parent_poverty_count + unfit_parent_single_count + unfit_parent_addict_count + unfit_parent_abuse_count + unfit_parent_criminal_count + unfit_parent_unsound_count + unfit_parent_needcare_count + unfit_parent_unwilling_count)::integer as  unfit_parent_count,
                                    sum( was_trafficked_count)::integer as  was_trafficked_count,
                                    sum( surrendered_count)::integer as  surrendered_count,
                                    sum(orp_fit_guardian_count + fit_parent_count)::integer as fit_guardian_parent_count
                                    from dash_child_cci_category 
                                    where 1=1 @@state_filter @@district_filter
                                    group by shelter_homename"""
        data_meta["chart"]["categories_in_cci"]["datas"][0][0] = 'Shelter Home'
    elif districts_id != "" and shelter_homes_id != "":
        # display the district chart for state user or admin/center user when state_id is selected
        # #child_category_district
        child_category = """select shelter_homename, coalesce(sum(child_count),0)::integer as total_children,
                                    sum(abandoned_count + fam_not_trace_count)::integer as abandoned_count,
                                    sum( orp_no_guardian_count)::integer as  orp_no_guardian_count,
                                    sum( unfit_guardian_poverty_count + unfit_guardian_addict_count + unfit_guardian_abuse_count + unfit_guardian_criminal_count + unfit_guardian_unsound_count + unfit_guardian_needcare_count + unfit_guardian_unwilling_count)::integer as unfit_guardian_count,
                                    sum( unfit_parent_poverty_count + unfit_parent_single_count + unfit_parent_addict_count + unfit_parent_abuse_count + unfit_parent_criminal_count + unfit_parent_unsound_count + unfit_parent_needcare_count + unfit_parent_unwilling_count)::integer as  unfit_parent_count,
                                    sum( was_trafficked_count)::integer as  was_trafficked_count,
                                    sum( surrendered_count)::integer as  surrendered_count,
                                    sum(orp_fit_guardian_count + fit_parent_count)::integer as fit_guardian_parent_count
                                    from dash_child_cci_category
                                    where 1=1 @@state_filter @@district_filter @@shelter_filter
                                    group by shelter_homename"""
        data_meta["chart"]["categories_in_cci"]["datas"][0][0] = 'Shelter Home'
        #reduce the height of the table chart when displaying for shelterhome as only one row will be displayed
        data_meta["chart"]["categories_in_cci"]["chart_height"] = '100px'
        data_meta["chart"]["categories_in_cci"]["options"]["height"] = '80px'
    # for district and shelter level users, do not display the table chart
    if child_category != "":
        child_category = filter_condtition(request,child_category)
        data_values_from_db["categories_in_cci"] = set_table_chart_data(child_category, data_meta["chart"]["categories_in_cci"]["datas"])
    else:
        hide_charts.append("categories_in_cci")

    # #pie chart - widget #5 - Categories of Children in Child Care Institutions (CCIs)
    # child_category_district = filter_condtition(request,child_category_district)
    # data_values_from_db["categories_in_cci"] = set_table_chart_data(child_category_district, data_meta["chart"]["categories_in_cci"]["datas"])

    #build chart data json with calculated values and meta data (chart title, axis title, tooltip text and chart note from chartmeta table) from database 
    chart_meta = ChartMeta.objects.filter(active = 2).order_by('id')
    chart_list = []
    chart_dict = data_meta.get("chart")
    for cht in chart_meta:
        if cht.chart_name in hide_charts:
            continue
        cht_info = chart_dict.get(cht.chart_name)
        cht_info["chart_title"] = cht.chart_title
        cht_info["datas"] = data_values_from_db[cht.chart_name]
        #chart_type values: 1=Column Chart, 2=Pie Chart, 3=Table Chart, 4=Bar Chart
        if cht.chart_type in (1,4):
            cht_info["options"]["vAxis"]["title"] = cht.vertical_axis_title
            cht_info["options"]["hAxis"]["title"] = cht.horizontal_axis_title
        elif cht.chart_type == 2:
            cht_info["options"]["title"] = cht.vertical_axis_title  
        cht_info.update({"tooltip":cht.chart_tooltip})
        cht_info.update({"chart_note":cht.chart_note}) 
        cht_info.update({"chart_name":cht.chart_name})        
        chart_list.append(cht_info)
    data = { "chart":chart_list}

    disclaimer = Config.objects.get(code='disclaimer')
    return render(request,'dashboard/dashboard.html',{'data': json.dumps(data), 'state':user_location["state_list"], 'district':user_location["district_list"], 'shelter_home':user_location["shelter_home_list"], 'disclaimer':disclaimer,'user_location':user_location,'data_html':data,'states_id':states_id,'districts_id':districts_id,'shelter_homes_id':shelter_homes_id})
 

#****************************************************************************
# Get State List
#**************************************************************************** 
def get_state(request):
      state = State.objects.values('id','name').order_by('name')
      return state


#****************************************************************************
# List and Detail Function
#****************************************************************************    
@login_required(login_url='/login/')
def lists(request):
    data = {"1":['1','a','101','a'],
            "2":['2','b','102','b'],
            "3":['3','c','103','c'],
            "4":['4','d','104','d'],
            "5":['5','e','105','e'],
            "6":['6','f','106','f'],}

    t = tuple(data.items())
    paginator = Paginator(t, 5)
    page = request.GET.get('page',1)
    try:
        projects = paginator.page(page)
    except PageNotAnInteger:
        projects = paginator.page(1)
    except EmptyPage:
        projects = paginator.page(paginator.num_pages)

    return render(request,'dashboard/lists.html',locals())


#****************************************************************************
# Details Form Function
#****************************************************************************
@login_required(login_url='/login/')
def detail(request,pk):
    pk=pk
    if request.method == 'POST':
        data=request.POST
        
    return render(request,'dashboard/detail_page.html',locals())


#****************************************************************************
# State Side Bar Function
#****************************************************************************
@login_required(login_url='/login/')
def state_bar(request):
    return render(request,'dashboard/state_bar.html',locals())


#****************************************************************************
# District Side Bar Function
#****************************************************************************
@login_required(login_url='/login/')
def district_bar(request):
    return render(request,'dashboard/district_bar.html',locals())

#****************************************************************************
# District Data Based on state_id
#****************************************************************************
def district_data(request, pk):
    if request.method == 'POST':
        district = District.objects.filter(state = pk).values('id','name').order_by('name')
    return JsonResponse({'district': list(district)})


#****************************************************************************
# Shelter Home Data Based on district_id
#****************************************************************************
def shelterhome_data(request, pk):
    if request.method == 'POST':
        shelter_home = ShelterHome.objects.filter(district = pk).values('id','name').order_by('name')
    return JsonResponse({'shelter_home': list(shelter_home)})


#****************************************************************************
# XLS Export Function
#****************************************************************************    
# def write_excel(excel_content,filename):
#     response = HttpResponse(excel_content, content_type='application/vnd.ms-excel')
#     response['Content-Disposition'] = 'attachment; filename=%s.xls' %(str(filename))
#     return response


#****************************************************************************
# Custom Report Function
#****************************************************************************    
@login_required(login_url='/login/')
def custom_report(request):
    state = get_state(request)
    user_location = get_user_locations_data(request)
    form_url =  '/custom-report/'

    #retaining dropdown values
    states_id=""
    districts_id=""
    shelter_homes_id=""
    if request.method == "POST" and request.POST.get('state'):
        states_id = int(request.POST.get('state'))
    elif request.method == "GET" and request.GET.get('state'):
        states_id = int(request.GET.get('state'))
    elif user_location["state_id"] != 0:
        states_id = user_location["state_id"]
    if request.method == "POST" and request.POST.get('district'):
        districts_id = int(request.POST.get('district'))
    elif request.method == "GET" and request.GET.get('district'):
        districts_id = int(request.GET.get('district'))
    elif user_location["district_id"] != 0:
        districts_id = user_location["district_id"]
    if request.method == "POST" and request.POST.get('shelter_home'):
        shelter_homes_id = int(request.POST.get('shelter_home'))
    elif request.method == "GET" and request.GET.get('shelter_home'):
        shelter_homes_id = int(request.GET.get('shelter_home'))
    elif user_location["shelter_home_id"] != 0:
        shelter_homes_id = user_location["shelter_home_id"]  

    report_query = """select 
                        state_name,
                        district_name,
                        shelter_home_name,
                        child_name,
                        coalesce(case_number,'') as case_number,
                        coalesce(dob,'') as dob,
                        (case when age_year = 0 and age_plus_months = 0 then 'NA' else ((case when age_year = 0 then '' when age_year = 1 then '1 year and ' else age_year || ' years and ' end)
                            || age_plus_months || (case when age_plus_months <= 1 then ' month' else ' months' end)) end) as age,
                        coalesce(gender,'') as gender,
                        coalesce(date_flagged_for_adpotion_inquiry,'') as date_flagged_for_adpotion_inquiry,
                        (case when adoption_inquiry_pending_years = -1 and adoption_inquiry_pending_months = -1 then 'NA' else ((case when adoption_inquiry_pending_years = 0 then '' when adoption_inquiry_pending_years = 1 then '1 year and ' else adoption_inquiry_pending_months || ' years and ' end)
                            || (case when adoption_inquiry_pending_months = 0 and adoption_inquiry_pending_years <= 0 then '< 1 month' when adoption_inquiry_pending_months = 0 or adoption_inquiry_pending_months = 1 then adoption_inquiry_pending_months || ' month' else adoption_inquiry_pending_months || ' months' end)) end) as adoption_pending_duration,
                        coalesce(flagging_reason,'') as flagging_reason,
                        coalesce(last_family_visit,'') as last_family_visit,
                        coalesce(guardian_listed,'') as guardian_listed,
                        coalesce(classification,'') as classification,
                        coalesce(total_shelter_home_stay,'') as shelter_home_stay,
                        coalesce(last_cwc_review_duration,'') as last_cwc_review_duration,
                        coalesce(date_of_admission,'') as date_of_admission,
                        coalesce(admission_number,'') as admission_number
                        from rep_child_details_view 
                        where 1=1 @@state_filter @@district_filter @@shelter_filter"""
    report_query = filter_condtition(request,report_query)
    data = return_sql_results(report_query)

    data = pagination_function(request,data)

    current_page = request.GET.get('page',1)
    page_number_start = int(current_page) - 5 if int(current_page) > 5 else 1
    page_number_end = page_number_start + 10 if page_number_start + 10 < data.paginator.num_pages else data.paginator.num_pages+1
    display_page_range = range(page_number_start, page_number_end)
        

    if request.GET.get('export') == 'true':
        if request.method == "GET":
            result = filter_condtition(request,report_query)
            export_data = return_sql_results(result)
            file_name = "Children_Recommended_(Flagged)_for_Adoption_Inquiry_Report_"+str(datetime.now().date())
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename=%s.csv' %(str(file_name))
            row_num = 0
            writer = csv.writer(response)
            writer.writerow(['Sl.No',
                            'State',
                            'District',
                            'Shelter Name',
                            'Child Name',
                            'Case Number',
                            'DOB',
                            'Age',
                            'Gender',
                            'Date on Which Child was Flagged for Adoption Inquiry',
                            'How Long has the Adoption Inquiry been Pending?',
                            'Reason for Flagging the Child',
                            'Family Visit Tracking',
                            'Guardian Listed',
                            'Child Classification',
                            'Length of Stay in the Shelter',
                            'Duration since the last CWC Periodic Review',
                            'Date of Admission',
                            'Admission No.',])

            for obj in export_data:
                row_num += 1
                writer.writerow((row_num, 
                     obj['state_name'],
                     obj['district_name'],
                     obj['shelter_home_name'],
                     obj['child_name'],
                     obj['case_number'],
                     obj['dob'],
                     obj['age'],
                     obj['gender'],
                     obj['date_flagged_for_adpotion_inquiry'],
                     obj['adoption_pending_duration'],
                     obj['flagging_reason'],
                     obj['last_family_visit'],
                     obj['guardian_listed'],
                     obj['classification'],
                     obj['shelter_home_stay'],
                     obj['last_cwc_review_duration'],
                     obj['date_of_admission'],
                     obj['admission_number'],))
            return response                  
    return render(request,'dashboard/custom_report.html',locals())


#****************************************************************************
# Baseline Report Function
#****************************************************************************    
@login_required(login_url='/login/')
def baseline_report(request):
    state = get_state(request)
    user_location = get_user_locations_data(request)
    form_url =  '/baseline-report/'

    #retaining dropdown values
    states_id=""
    districts_id=""
    shelter_homes_id=""
    if request.method == "POST" and request.POST.get('state'):
        states_id = int(request.POST.get('state'))
    elif request.method == "GET" and request.GET.get('state'):
        states_id = int(request.GET.get('state'))
    elif user_location["state_id"] != 0:
        states_id = user_location["state_id"]
    if request.method == "POST" and request.POST.get('district'):
        districts_id = int(request.POST.get('district'))
    elif request.method == "GET" and request.GET.get('district'):
        districts_id = int(request.GET.get('district'))
    elif user_location["district_id"] != 0:
        districts_id = user_location["district_id"]
    if request.method == "POST" and request.POST.get('shelter_home'):
        shelter_homes_id = int(request.POST.get('shelter_home'))
    elif request.method == "GET" and request.GET.get('shelter_home'):
        shelter_homes_id = int(request.GET.get('shelter_home'))
    elif user_location["shelter_home_id"] != 0:
        shelter_homes_id = user_location["shelter_home_id"]    
    report_query = """select 
                        state_name,
                        district_name,
                        shelter_home_name,
                        coalesce(case_number,'') as case_number,
                        first_name, 
                        middle_name,
                        last_name,
                        coalesce(dob,'') as dob,
                        coalesce(gender,'') as gender,
                        coalesce(classification,'') as classification, 
                        coalesce(reco_adoption_inquiry,'') as reco_adoption_inquiry,
                        coalesce(admission_number,'') as admission_number,
                        coalesce(date_of_admission,'') as date_of_admission,
                        coalesce(guardian_name,'') as guardian_name,
                        coalesce(guardian_relation,'') as guardian_relation,
                        coalesce(guardian_most_recent_visit,'') as guardian_most_recent_visit,
                        coalesce(last_review_date,'') as last_review_date,
                        coalesce(cwc_started_adoption_inquiry,'') as cwc_started_adoption_inquiry,
                        coalesce(cwc_order_number,'') as cwc_order_number,
                        coalesce(date_declaring_child_free_for_adoption,'') as date_declaring_child_free_for_adoption
                        from rep_child_baseline_report 
                    where 1=1 @@state_filter @@district_filter @@shelter_filter"""
    report_query = filter_condtition(request,report_query)
    data = return_sql_results(report_query)
    #print(data)

    data = pagination_function(request,data)

    current_page = request.GET.get('page',1)
    page_number_start = int(current_page) - 5 if int(current_page) > 5 else 1
    page_number_end = page_number_start + 10 if page_number_start + 10 < data.paginator.num_pages else data.paginator.num_pages+1
    display_page_range = range(page_number_start, page_number_end)


    if request.GET.get('export') == 'true':
        if request.method == "GET":
            result = filter_condtition(request,report_query)
            export_data = return_sql_results(result)
            file_name = "Baseline_Report_"+str(datetime.now().date())
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename=%s.csv' %(str(file_name))
            row_num = 0
            writer = csv.writer(response)
            writer.writerow(['Sl.No',
                            'State',
                            'District',
                            'Shelter Home',
                            'Case Number',
                            'First Name',
                            'Middle Name',
                            'Last Name',
                            'Date of Birth',
                            'Gender',
                            'Child Classification',
                            'Recommended for Adoption Inquiry(Yes/No)',
                            'Admission Number',
                            'Date of Admission',
                            'Name of Guardian',
                            'Relationship',
                            'Date of Last Guardian Visit',
                            'Last Date of CWC Order or Review',
                            'CWC Started the Adoption Inquiry Process',
                            'CWC Order Number Declaring Child Free for Adoption',
                            'Date Declaring Child Free for Adoption',])
            for obj in export_data:
                row_num += 1
                writer.writerow((row_num, obj['state_name'],
                     obj['district_name'],
                     obj['shelter_home_name'],
                     obj['case_number'],
                     obj['first_name'],
                     obj['middle_name'],
                     obj['last_name'],
                     obj['dob'],
                     obj['gender'],
                     obj['classification'],
                     obj['reco_adoption_inquiry'],
                     obj['admission_number'],
                     obj['date_of_admission'],
                     obj['guardian_name'],
                     obj['guardian_relation'],
                     obj['guardian_most_recent_visit'],
                     obj['last_review_date'],
                     obj['cwc_started_adoption_inquiry'],
                     obj['cwc_order_number'],
                     obj['date_declaring_child_free_for_adoption'],))
            return response
    return render(request,'dashboard/baseline_report.html',locals())   


#****************************************************************************
#Function to run Flagging History Script
#****************************************************************************    
@login_required(login_url='/login/')
def flag_history(request):
    call_command('flagging_history')
    return HttpResponseRedirect('/admin')


#****************************************************************************
#Function to check Flagging History Script Status
#****************************************************************************    
@login_required(login_url='/login/')
def flag_history_script_status(request):
    if request.method == 'GET':
        script_status_check = Config.objects.get(code='flagging_history_script_status')
        script_status = script_status_check.value
    return JsonResponse({'script_status': script_status})   