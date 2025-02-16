from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.db.models import Max, Avg, Min, Count
from django.db.models.functions import TruncDate, TruncHour
from django.utils import timezone
from datetime import timedelta
from .models import (
    Sensor, SensorData, SensorType, Location, 
    Organization, Alert, MaintenanceLog
)

@login_required
def dashboard(request):
    user_orgs = request.user.organizations.all()
    context = {
        'organizations': user_orgs,
        'total_sensors': Sensor.objects.filter(organization__in=user_orgs).count(),
        'active_alerts': Alert.objects.filter(
            sensor__organization__in=user_orgs,
            acknowledged=False
        ).count(),
        'sensors_by_status': Sensor.objects.filter(organization__in=user_orgs)\
            .values('status')\
            .annotate(count=Count('id'))
    }
    return render(request, 'sensor/dashboard.html', context)

@login_required
def sensor_list(request, org_id=None):
    if org_id:
        organization = get_object_or_404(Organization, id=org_id)
        sensors = Sensor.objects.filter(organization=organization)
    else:
        sensors = Sensor.objects.filter(organization__in=request.user.organizations.all())
    
    return render(request, 'sensor/sensor_list.html', {
        'sensors': sensors,
        'sensor_types': SensorType.objects.all(),
        'locations': Location.objects.all()
    })

@login_required
def sensor_detail(request, sensor_id):
    sensor = get_object_or_404(Sensor, id=sensor_id)
    end_date = timezone.now()
    start_date = end_date - timedelta(days=7)
    
    context = {
        'sensor': sensor,
        'recent_data': SensorData.objects.filter(
            sensor=sensor,
            timestamp__range=(start_date, end_date)
        ).order_by('-timestamp')[:100],
        'active_alerts': Alert.objects.filter(
            sensor=sensor,
            acknowledged=False
        ),
        'maintenance_logs': MaintenanceLog.objects.filter(sensor=sensor)[:5]
    }
    return render(request, 'sensor/sensor_detail.html', context)

@login_required
def get_sensor_data(request, sensor_id):
    sensor = get_object_or_404(Sensor, id=sensor_id)
    timeframe = request.GET.get('timeframe', '24h')
    
    end_date = timezone.now()
    if timeframe == '24h':
        start_date = end_date - timedelta(hours=24)
        truncate = TruncHour
    else:  # '7d' or default
        start_date = end_date - timedelta(days=7)
        truncate = TruncDate
    
    data = SensorData.objects.filter(
        sensor=sensor,
        timestamp__range=(start_date, end_date)
    ).annotate(
        period=truncate('timestamp')
    ).values('period').annotate(
        avg_value=Avg('value'),
        min_value=Min('value'),
        max_value=Max('value')
    ).order_by('period')
    
    return JsonResponse(list(data), safe=False)

@login_required
def alerts(request):
    alerts = Alert.objects.filter(
        sensor__organization__in=request.user.organizations.all(),
        acknowledged=False
    ).select_related('sensor')
    return render(request, 'sensor/alerts.html', {'alerts': alerts})

@login_required
def acknowledge_alert(request, alert_id):
    if request.method == 'POST':
        alert = get_object_or_404(Alert, id=alert_id)
        alert.acknowledged = True
        alert.acknowledged_by = request.user
        alert.acknowledged_at = timezone.now()
        alert.save()
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error'}, status=400)

@login_required
def sensor_analytics(request, sensor_id):
    sensor = get_object_or_404(Sensor, id=sensor_id)
    end_date = timezone.now()
    start_date = end_date - timedelta(days=30)
    
    daily_stats = SensorData.objects.filter(
        sensor=sensor,
        timestamp__range=(start_date, end_date)
    ).annotate(
        date=TruncDate('timestamp')
    ).values('date').annotate(
        avg_value=Avg('value'),
        max_value=Max('value'),
        min_value=Min('value'),
        reading_count=Count('id')
    ).order_by('date')
    
    return JsonResponse({
        'daily_stats': list(daily_stats),
        'alert_count': Alert.objects.filter(
            sensor=sensor,
            timestamp__range=(start_date, end_date)
        ).count(),
        'uptime_percentage': calculate_uptime(sensor, start_date, end_date)
    })

def calculate_uptime(sensor, start_date, end_date):
    total_readings = SensorData.objects.filter(
        sensor=sensor,
        timestamp__range=(start_date, end_date)
    ).count()
    
    expected_readings = (end_date - start_date).total_seconds() / sensor.reading_interval
    
    if expected_readings == 0:
        return 100.0
    
    return (total_readings / expected_readings) * 100
