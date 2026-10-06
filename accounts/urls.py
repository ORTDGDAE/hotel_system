from django.urls import path
from . import views

app_name = "accounts"

urlpatterns = [
    path("login/", views.login_view, name="login"),
    path("signup/", views.signup_view, name="signup"),
    path("logout/", views.logout_view, name="logout"),
    path("staff/", views.staff_directory, name="staff_directory"),
    path("dev-login/<str:username>/", views.dev_login_view, name="dev_login"),
]
