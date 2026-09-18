from django.test import SimpleTestCase

from .serializers import GenerateHabeasDataSerializer
from .services.text_generator import build_document_text


class BuildDocumentTextTests(SimpleTestCase):
    def _campos_base(self) -> dict:
        return {
            "nombre_completo": "Juana Pérez",
            "tipo_documento_identidad": "Cédula de ciudadanía",
            "numero_documento": "1020304050",
            "correo_notificacion": "juana@example.com",
            "telefono": "3001234567",
            "ciudad": "Bogotá D.C.",
            "entidad_destinataria": "Banco Ejemplo S.A.",
            "entidad_direccion_o_correo": "datos@bancoejemplo.com",
            "hechos": "Solicité mi información hace un mes y no he recibido respuesta.",
        }

    def test_consulta_includes_legal_grounding_and_deadline(self):
        texto = build_document_text("consulta", self._campos_base())
        self.assertIn("Juana Pérez", texto)
        self.assertIn("FUNDAMENTO LEGAL", texto)
        self.assertIn("Ley 1581 de 2012", texto)
        self.assertIn("PETICIÓN", texto)

    def test_rectificacion_includes_specific_fields(self):
        campos = self._campos_base()
        campos.update(
            {
                "dato_incorrecto": "Mi dirección aparece en otra ciudad",
                "informacion_correcta": "Vivo en Medellín desde 2023",
                "razon": "Me mudé hace dos años",
            }
        )
        texto = build_document_text("rectificacion", campos)
        self.assertIn("Mi dirección aparece en otra ciudad", texto)
        self.assertIn("Vivo en Medellín desde 2023", texto)


class GenerateHabeasDataSerializerTests(SimpleTestCase):
    def test_missing_required_field_is_rejected(self):
        serializer = GenerateHabeasDataSerializer(data={"tipo": "rectificacion", "campos": {"nombre_completo": "Ana"}})
        self.assertFalse(serializer.is_valid())
        self.assertIn("campos", serializer.errors)

    def test_valid_payload_passes(self):
        campos = {
            "nombre_completo": "Ana",
            "tipo_documento_identidad": "Cédula de ciudadanía",
            "numero_documento": "123",
            "correo_notificacion": "ana@example.com",
            "ciudad": "Cali",
            "entidad_destinataria": "Empresa X",
            "hechos": "Hechos de prueba",
            "dato_a_suprimir": "Mi antigua dirección",
            "razon_supresion": "Ya no vivo allí y no es necesaria",
        }
        serializer = GenerateHabeasDataSerializer(data={"tipo": "supresion", "campos": campos})
        self.assertTrue(serializer.is_valid(), serializer.errors)
