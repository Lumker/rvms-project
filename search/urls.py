from django.urls import path
from . import views

app_name = 'search'

urlpatterns = [
    path('', views.global_search, name='results'),
    path('autocomplete/', views.search_autocomplete, name='autocomplete'),
]