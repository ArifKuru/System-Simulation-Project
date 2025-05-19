from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('create/', views.create_project, name='create_project'),
    path('project/<int:project_id>/', views.project_detail, name='project_detail'),
    path('api/stocks/create/', views.create_stock_api, name='create_stock_api'),
    path('api/stocks/list/', views.list_stocks_api, name='list_stocks_api'),
]
