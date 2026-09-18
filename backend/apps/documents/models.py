from django.conf import settings
from django.db import models

from .types import TIPOS_HABEAS_DATA

TIPO_CHOICES = [(key, cfg["label"]) for key, cfg in TIPOS_HABEAS_DATA.items()]


class HabeasDataRequest(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="habeas_data_requests")
    tipo = models.CharField(max_length=32, choices=TIPO_CHOICES)
    campos = models.JSONField()
    texto_generado = models.TextField()
    pdf = models.FileField(upload_to="habeas_data_pdfs/")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.get_tipo_display()} - {self.user} ({self.created_at:%Y-%m-%d})"
