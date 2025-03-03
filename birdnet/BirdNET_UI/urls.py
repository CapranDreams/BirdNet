from django.urls import path
from . import views
from .consumers import BirdConsumer

urlpatterns = [
    path('', views.serve_index, name='serve_index'),
    path('api/birds/', views.get_birds, name='get_birds'),
    path('api/birds_now/', views.get_birds_now, name='get_birds_now'),
    path('api/detections_this_week/', views.get_detections_this_week, name='get_detections_this_week'),
    path('api/detections_this_week_genus_only/', views.get_detections_this_week_genus_only, name='get_detections_this_week_genus_only'),
    path('api/detections_this_week_second_name_only/', views.get_detections_this_week_second_name_only, name='get_detections_this_week_second_name_only'),
    path('api/bird_detections_count/', views.get_bird_detections_count, name='get_bird_detections_count'),
    path('api/wav_spectrogram/', views.get_wav_spectrogram, name='get_wav_spectrogram'),
    path('download_database/', views.download_database, name='download_database'),
    path('api/ebirds/<str:scientific_name>/', views.get_ebirds, name='get_ebirds'),
    path('api/ebirds/', views.get_all_ebirds, name='get_all_ebirds'),
    path('api/ebirds_config/', views.read_ebirds_config, name='read_ebirds_config'),
    path('stats/', views.display_ebirds, name='display_ebirds'),
    path('api/observation_history_days/', views.get_observation_history_days, name='get_observation_history_days'),
    path('api/update_available/', views.get_update_available, name='get_update_available'),
    path('ws/birds/', BirdConsumer.as_asgi(), name='get_birds_ws'),
    path('api/ebirds/all/', views.get_all_from_ebirds, name='get_all_from_ebirds'),
    path('api/compile_ebirds/', views.compile_ebirds, name='compile_ebirds'),
    path('settings/', views.settings_view, name='settings'),
    path('update_config/', views.update_config, name='update_config'),
    path('api/settingFile/', views.get_config, name='get_config'),
    path('api/hourly_counts/<str:scientific_name>/', views.get_hourly_counts, name='get_hourly_counts'),
    path('api/weekly_counts/<str:scientific_name>/', views.get_weekly_counts, name='get_weekly_counts'),
    path('api/new_birds/', views.get_new_birds, name='get_new_birds'),
    path('api/birds_config/', views.get_birds_config, name='get_birds_config'),
    path('api/update_birds_config/', views.update_birds_config, name='update_birds_config'),
    path('api/observation_stats/', views.get_observation_stats, name='get_observation_stats'),
]