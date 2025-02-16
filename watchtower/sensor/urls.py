from django.urls import path
from . import views

app_name = 'sensor'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('sensors/', views.sensor_list, name='sensor_list'),
    path('organization/<int:org_id>/sensors/', views.sensor_list, name='org_sensor_list'),
    path('sensor/<int:sensor_id>/', views.sensor_detail, name='sensor_detail'),
    path('sensor/<int:sensor_id>/data/', views.get_sensor_data, name='sensor_data'),
    path('sensor/<int:sensor_id>/analytics/', views.sensor_analytics, name='sensor_analytics'),
    path('alerts/', views.alerts, name='alerts'),
    path('alert/<int:alert_id>/acknowledge/', views.acknowledge_alert, name='acknowledge_alert'),
] 