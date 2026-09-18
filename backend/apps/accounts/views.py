from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .models import User
from .serializers import ProyectadurIATokenObtainPairSerializer, SignupSerializer, UserSerializer


class SignupView(generics.CreateAPIView):
    """POST /api/auth/signup/ {nombre, username, password} -> crea el usuario."""

    queryset = User.objects.all()
    serializer_class = SignupSerializer
    permission_classes = [permissions.AllowAny]


class LoginView(TokenObtainPairView):
    """POST /api/auth/login/ {username, password} -> access/refresh JWT + datos del usuario."""

    permission_classes = [permissions.AllowAny]
    serializer_class = ProyectadurIATokenObtainPairSerializer


class RefreshView(TokenRefreshView):
    permission_classes = [permissions.AllowAny]


class MeView(APIView):
    """GET /api/auth/me/ -> usuario autenticado actual."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data)
