import uuid

from django.core.files.base import ContentFile
from django.http import FileResponse
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import HabeasDataRequest
from .serializers import GenerateHabeasDataSerializer, HabeasDataRequestSerializer
from .services.pdf_generator import render_pdf
from .services.text_generator import build_document_text
from .types import serialize_tipos_for_frontend


class TiposView(APIView):
    """GET /api/documents/tipos/ -> configuración de los 5 tipos de Habeas Data, para que el
    frontend construya el formulario dinámicamente."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response(serialize_tipos_for_frontend())


class GenerateView(APIView):
    """POST /api/documents/generate/ {tipo, campos} -> genera el texto + PDF de la solicitud."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = GenerateHabeasDataSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        tipo = serializer.validated_data["tipo"]
        campos = serializer.validated_data["campos"]

        texto = build_document_text(tipo, campos)
        pdf_bytes = render_pdf(tipo, texto)

        instance = HabeasDataRequest(user=request.user, tipo=tipo, campos=campos, texto_generado=texto)
        filename = f"{tipo}_{request.user.id}_{uuid.uuid4().hex[:8]}.pdf"
        instance.pdf.save(filename, ContentFile(pdf_bytes), save=False)
        instance.save()

        return Response(HabeasDataRequestSerializer(instance).data, status=status.HTTP_201_CREATED)


class HabeasDataRequestListView(generics.ListAPIView):
    """GET /api/documents/ -> historial de documentos generados por el usuario."""

    serializer_class = HabeasDataRequestSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return HabeasDataRequest.objects.filter(user=self.request.user)


class HabeasDataRequestDetailView(generics.RetrieveAPIView):
    serializer_class = HabeasDataRequestSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return HabeasDataRequest.objects.filter(user=self.request.user)


class HabeasDataPDFDownloadView(APIView):
    """GET /api/documents/<id>/pdf/ -> descarga el PDF (protegido por autenticación, ya que
    el documento contiene datos personales del usuario: cédula, correo, hechos narrados)."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        instance = HabeasDataRequest.objects.filter(user=request.user, pk=pk).first()
        if not instance:
            return Response(status=status.HTTP_404_NOT_FOUND)
        return FileResponse(instance.pdf.open("rb"), as_attachment=True, filename=instance.pdf.name.split("/")[-1])
