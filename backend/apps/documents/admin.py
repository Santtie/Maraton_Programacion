from django.contrib import admin

from .models import HabeasDataRequest


@admin.register(HabeasDataRequest)
class HabeasDataRequestAdmin(admin.ModelAdmin):
    list_display = ("id", "tipo", "user", "created_at")
    list_filter = ("tipo",)
    readonly_fields = ("texto_generado",)
