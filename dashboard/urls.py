from django.urls import path, include
from dashboard.views import *


app_name = "dashboard"
urlpatterns = [
	path('',login_view, name="login"),
    path('login/',login_view, name="login"),
    path('logout/',logout_view, name="logout"),
    path('dashboard/',dashboard, name="dashboard"),

    path('list/',lists, name="list"),
    path('detail/<pk>/',detail, name="detail"),

    path('state-bar/',state_bar, name="state_bar"),
    path('district-bar/',district_bar, name="district_bar"),

    path('district-data/<int:pk>',district_data, name="district_data"),
    path('shelterhome-data/<int:pk>',shelterhome_data, name="shelterhome_data"), 

    path('custom-report/',custom_report, name="custom_report"),
    path('baseline-report/',baseline_report, name="baseline_report"),

    path('flag-history/',flag_history, name="flag_history"),
    path('flag-history-script-status/',flag_history_script_status, name="flag_history_script_status"),

	]