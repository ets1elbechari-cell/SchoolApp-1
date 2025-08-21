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
    path("login/", views.connexion_view, name="login"),
    path("register/", views.register_view, name="register"),
    path("confirm_email/", views.confirm_email_view, name="confirm_email"),
    path("logout/", views.logout_view, name="logout"),
    # Add other paths as needed
]
