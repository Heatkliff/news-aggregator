from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('news/<slug:slug>/', views.news_detail, name='news_detail'),
    path('sources/', views.source_list, name='source_list'),
]
