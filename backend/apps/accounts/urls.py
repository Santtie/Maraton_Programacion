from django.urls import path

from .views import LoginView, MeView, RefreshView, SignupView

app_name = "accounts"

urlpatterns = [
    path("signup/", SignupView.as_view(), name="signup"),
    path("login/", LoginView.as_view(), name="login"),
    path("login/refresh/", RefreshView.as_view(), name="login-refresh"),
    path("me/", MeView.as_view(), name="me"),
]
