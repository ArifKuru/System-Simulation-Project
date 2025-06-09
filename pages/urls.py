from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('create/', views.create_project, name='create_project'),
    path('project/<int:project_id>/', views.project_detail, name='project_detail'),
    path('api/stocks/create/', views.create_stock_api, name='create_stock_api'),
    path('api/stocks/list/', views.list_stocks_api, name='list_stocks_api'),
    path('api/stocks/read/<int:stock_id>/', views.read_stock, name='read_stock_api'),
    path('api/events/list/', views.list_events, name='list_events_api'),
    path('api/events/create/', views.create_event, name='create_event_api'),

    path('api/stocks/variables/', views.stock_variables, name='stock_variables_api'),
    path('api/stocks/delete/<int:stock_id>/', views.delete_stock, name='delete_stock_api'),
    path('api/events/delete/<int:event_id>/', views.delete_event, name='delete_event_api'),

    path('api/simulate/<int:project_id>/', views.simulate_project, name='simulate_project_api'),
    path('api/simulate/bulk/<int:project_id>/', views.simulate_multiple, name='simulate_multiple_api'),

    path('api/stocks/reset/<int:project_id>/', views.reset_project_stocks, name='reset_stocks_api'),

    path('api/effects/create/', views.create_effect, name='create_effect_api'),
    path('api/effects/list/', views.list_effects, name='list_effects_api'),
    path('api/effects/read/<int:effect_id>/', views.read_effect, name='read_effect_api'),
    path('api/effects/delete/<int:effect_id>/', views.delete_effect, name='delete_effect_api'),
    path('api/generate/', views.generate_simulation_from_prompt, name='generate_simulation'),

]
