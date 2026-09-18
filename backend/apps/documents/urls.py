from django.urls import path

from .views import (
    GenerateView,
    HabeasDataPDFDownloadView,
    HabeasDataRequestDetailView,
    HabeasDataRequestListView,
    TiposView,
)

app_name = "documents"

urlpatterns = [
    path("tipos/", TiposView.as_view(), name="tipos"),
    path("generate/", GenerateView.as_view(), name="generate"),
    path("", HabeasDataRequestListView.as_view(), name="list"),
    path("<int:pk>/", HabeasDataRequestDetailView.as_view(), name="detail"),
    path("<int:pk>/pdf/", HabeasDataPDFDownloadView.as_view(), name="pdf"),
]
