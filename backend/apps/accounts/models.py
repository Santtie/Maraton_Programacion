from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Usuario de ProyectadurIA. Reutiliza username/password de AbstractUser y añade el
    nombre completo que se pide explícitamente en el registro (signup: nombre, usuario,
    contraseña)."""

    nombre = models.CharField("nombre completo", max_length=150)

    def __str__(self) -> str:
        return self.username
