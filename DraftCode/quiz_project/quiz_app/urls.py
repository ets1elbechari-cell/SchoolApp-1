from django.urls import path
from . import views

# URLConf
urlpatterns = [
    path('', views.home, name='home'),  # Add this line for the root path
    path('hello/', views.say_hello),
    path('add_subject/', views.add_subject, name='add_subject'),
    path('subject_list/', views.subject_list, name='subject_list'),
    path('modify_subject/<int:subject_id>/', views.modify_subject, name='modify_subject'),
    path('delete_subject/<int:subject_id>/', views.delete_subject, name='delete_subject'),
]
