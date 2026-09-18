from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import User


class SignupLoginTests(APITestCase):
    def test_signup_creates_user_and_login_returns_tokens(self):
        signup_url = reverse("accounts:signup")
        payload = {"nombre": "Juana Pérez", "username": "juana", "password": "Str0ngPassw0rd!"}

        response = self.client.post(signup_url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(username="juana").exists())

        login_url = reverse("accounts:login")
        login_response = self.client.post(login_url, {"username": "juana", "password": "Str0ngPassw0rd!"}, format="json")

        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
        self.assertIn("access", login_response.data)
        self.assertIn("refresh", login_response.data)
        self.assertEqual(login_response.data["user"]["nombre"], "Juana Pérez")

    def test_duplicate_username_is_rejected(self):
        User.objects.create_user(username="juana", password="Str0ngPassw0rd!", nombre="Juana")
        signup_url = reverse("accounts:signup")

        response = self.client.post(
            signup_url, {"nombre": "Otra Juana", "username": "juana", "password": "Str0ngPassw0rd!"}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_me_requires_authentication(self):
        response = self.client.get(reverse("accounts:me"))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
