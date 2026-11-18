from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('upload/', views.upload, name='upload'),
    path('dataset/<int:pk>/', views.dataset_detail, name='dataset_detail'),
    path('dataset/<int:pk>/eda/', views.dataset_eda, name='dataset_eda'),
    path('dataset/<int:pk>/forecast/', views.forecast, name='forecast'),
    path('dataset/<int:pk>/forecast/run/', views.run_forecast, name='run_forecast'),
    path('dataset/<int:pk>/forecast/download/', views.download_forecast, name='download_forecast'),
]
