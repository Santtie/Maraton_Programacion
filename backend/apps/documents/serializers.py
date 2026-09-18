from rest_framework import serializers

from .models import HabeasDataRequest
from .types import TIPOS_HABEAS_DATA, get_campos_requeridos


class HabeasDataRequestSerializer(serializers.ModelSerializer):
    tipo_label = serializers.CharField(source="get_tipo_display", read_only=True)

    class Meta:
        model = HabeasDataRequest
        fields = ("id", "tipo", "tipo_label", "campos", "texto_generado", "pdf", "created_at")
        read_only_fields = fields


class GenerateHabeasDataSerializer(serializers.Serializer):
    tipo = serializers.ChoiceField(choices=list(TIPOS_HABEAS_DATA.keys()))
    campos = serializers.DictField()

    def validate(self, attrs: dict) -> dict:
        tipo = attrs["tipo"]
        campos = attrs["campos"]
        faltantes = []
        for campo in get_campos_requeridos(tipo):
            if campo["required"] and not str(campos.get(campo["name"], "")).strip():
                faltantes.append(campo["name"])
        if faltantes:
            raise serializers.ValidationError({"campos": f"Faltan campos requeridos: {', '.join(faltantes)}"})
        return attrs
