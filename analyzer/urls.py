from django.urls import path
from . import views

urlpatterns = [
    path('', views.health_check, name='health'), 
    path('api/info/', views.index, name='api_info'),
    path('api/analyze/', views.analyze, name='analyze'),
    path('api/analysis/<uuid:pk>/', views.analysis_detail, name='analysis_detail'),
    path('api/history/', views.history, name='history'),
    path('api/delete/<uuid:pk>/', views.delete_analysis, name='delete_analysis'),
    path('health/', views.health_check, name='health_check'), 
]