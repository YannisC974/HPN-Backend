from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from rest_framework import status
from .models import Ticket, Layer
from django.core.files.uploadedfile import SimpleUploadedFile

class CustomJWTAuthenticationTest(TestCase):
    
    def setUp(self):
        self.username = 'testuser'
        self.password = 'Haching1'
        self.user = User.objects.create_user(username=self.username, password=self.password)
        
        self.token_url = reverse('get-token')
        self.refresh_url = reverse('refresh')
        
        response = self.client.post(self.token_url, {
            'username': self.username,
            'password': self.password
        })
        
        self.assertEqual(response.status_code, 200)
        self.access_token = response.cookies['access_token'].value
        self.refresh_token = response.cookies['refresh_token'].value

    def test_login_sets_cookies(self):
        response = self.client.post(self.token_url, {
            'username': self.username,
            'password': self.password
        })
        
        self.assertEqual(response.status_code, 200)

        self.assertIn('access_token', response.cookies)
        self.assertIn('refresh_token', response.cookies)
        
        access_token = response.cookies['access_token'].value
        refresh_token = response.cookies['refresh_token'].value
        
        self.assertTrue(access_token)
        self.assertTrue(refresh_token)
        
        print("Access Token:", access_token)
        print("Refresh Token:", refresh_token)

    def test_refresh_token_sets_new_access_token_cookie(self):
        response = self.client.post(self.refresh_url, {}, cookies={'refresh_token': self.refresh_token})
        
        print("Response Content:", response.content.decode('utf-8'))
        
        self.assertEqual(response.status_code, 200)
        
        self.assertIn('access_token', response.cookies)
        
        new_access_token = response.cookies['access_token'].value
        self.assertTrue(new_access_token)
        self.assertNotEqual(new_access_token, self.access_token)
        
        print("Old Access Token:", self.access_token)
        print("New Access Token:", new_access_token)



class DisplayTicketViewTest(TestCase):
    def setUp(self):
        # Créer deux utilisateurs
        self.user1 = User.objects.create_user(username='1', password='password1')
        self.user2 = User.objects.create_user(username='2', password='password2')

        # Créer des layers
        self.foreground = Layer.objects.create(
            name="Foreground Layer",
            image=SimpleUploadedFile("foreground.jpg", b"file_content", content_type="image/jpeg"),
            author="Author 1"
        )
        self.background = Layer.objects.create(
            name="Background Layer",
            image=SimpleUploadedFile("background.jpg", b"file_content", content_type="image/jpeg"),
            author="Author 2"
        )

        # Créer un ticket pour user1
        self.ticket = Ticket.objects.create(
            owner=self.user1,
            full_ticket_front=SimpleUploadedFile("front.jpg", b"file_content", content_type="image/jpeg"),
            full_ticket_back=SimpleUploadedFile("back.jpg", b"file_content", content_type="image/jpeg"),
            foreground=self.foreground,
            background=self.background
        )

        # URL pour la vue DisplayTicketView
        self.display_ticket_url = reverse('display-ticket')

        # Obtenir les tokens pour user1
        response = self.client.post(reverse('get-token'), {
            'username': '1',
            'password': 'password1'
        })
        self.access_token_user1 = response.cookies['access_token'].value

        # Obtenir les tokens pour user2
        response = self.client.post(reverse('get-token'), {
            'username': '2',
            'password': 'password2'
        })
        self.access_token_user2 = response.cookies['access_token'].value

    def test_display_ticket_authorized(self):
        response = self.client.get(
            self.display_ticket_url + f'?ticketNumber={self.user1.username}',
            HTTP_COOKIE=f'access_token={self.access_token_user1}'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['owner'], int(self.user1.username))
        self.assertIn('full_ticket_front', response.data)
        self.assertIn('full_ticket_back', response.data)
        self.assertEqual(response.data['foreground']['name'], "Foreground Layer")
        self.assertEqual(response.data['background']['name'], "Background Layer")

    def test_display_ticket_unauthorized(self):
        response = self.client.get(
            self.display_ticket_url + f'?ticketNumber={self.user1.username}',
            HTTP_COOKIE=f'access_token={self.access_token_user2}'
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_display_ticket_unauthenticated(self):
        response = self.client.get(
            self.display_ticket_url + f'?ticketNumber={self.user1.username}'
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_display_ticket_nonexistent(self):
        response = self.client.get(
            self.display_ticket_url + '?ticketNumber=nonexistent_user',
            HTTP_COOKIE=f'access_token={self.access_token_user1}'
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_display_ticket_missing_number(self):
        response = self.client.get(
            self.display_ticket_url,
            HTTP_COOKIE=f'access_token={self.access_token_user1}'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def tearDown(self):
        # Nettoyer les fichiers créés pendant les tests
        self.foreground.image.delete()
        self.background.image.delete()
        self.ticket.full_ticket_front.delete()
        self.ticket.full_ticket_back.delete()
