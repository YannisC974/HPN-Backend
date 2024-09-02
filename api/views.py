from django.core.cache import cache

import json
import secrets
from django.http import HttpResponse, Http404, JsonResponse
from django.core.mail import send_mail
from django.conf import settings
from rest_framework.exceptions import PermissionDenied
from django.contrib.auth.models import User
from django.utils import timezone
import random
import string
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from .models import Ticket, FAQ, Challenge
from .serializers import TicketDisplaySerializer, FAQSerializer, CustomTokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from .web3_utils import claimTicket, isAlreadyClaimed, getTicketsIds
from backend.settings import BASE_URI
import cv2
from eth_account.messages import encode_defunct
from web3.auto import w3

## --------------------------------------------------------------------------------------------- ##
## -----------------------------------     LOGIN     ------------------------------------------- ##
## --------------------------------------------------------------------------------------------- ##


# Get pair access/refresh token linked to user (based on the username and password given)
# The tokens have the username in their payload for generalisation with the wallet login process
class CustomTokenObtainPairView(TokenObtainPairView):
    permission_classes=[AllowAny]
    serializer_class = CustomTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        access_token = serializer.validated_data['access']
        refresh_token = serializer.validated_data['refresh']

        response = Response({"detail": "Login successful"})

        response.set_cookie(
            'access_token',
            access_token,
            httponly=False,
            # domain='localhost',
            secure=False,
            samesite='None',
            max_age=settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'].total_seconds(),
            path='/'
        )

        response.set_cookie(
            'refresh_token',
            refresh_token,
            httponly=False,
            # domain='localhost',
            secure=False,
            samesite='None',
            max_age=settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'].total_seconds(),
            path='/'
        ) 
        return response
    
class CustomTokenRefreshView(TokenRefreshView):
    def post(self, request, *args, **kwargs):
        refresh_token = request.COOKIES.get('refresh_token')
        if not refresh_token:
            raise InvalidToken('No refresh token found in cookies')

        serializer = self.get_serializer(data={'refresh': refresh_token})
        serializer.is_valid(raise_exception=True)

        access_token = serializer.validated_data['access']

        response = Response({"detail": "Token refreshed successfully"})
        response.set_cookie(
            'access_token',
            access_token,
            httponly=True,
            secure=False, # For production only
            samesite='Lax',
            max_age=settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'].total_seconds(),
            path='/'
        )
        return response

class LogoutViewAll(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        response = Response({"detail": "Logout successful"})
        
        response.delete_cookie('access_token', path='/')
        response.delete_cookie('refresh_token', path='/')
        response.delete_cookie('access_token_wallet', path='/')
        response.delete_cookie('refresh_token_wallet', path='/')

        return response
    
class LogoutViewWallet(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        response = Response({"detail": "Logout successful"})
        
        response.delete_cookie('access_token_wallet', path='/')
        response.delete_cookie('refresh_token_wallet', path='/')

        return response
    
class LogoutViewLogin(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        response = Response({"detail": "Logout successful"})
        
        response.delete_cookie('access_token', path='/')
        response.delete_cookie('refresh_token', path='/')

        return response
    
# Create a challenge linked to the address and send it to the front end
class GetChallengeView(APIView):
    permission_classes = [AllowAny]
    def post(self, request, *args, **kwargs):
        address = request.data.get('address')
        if not address:
            return JsonResponse({'error': 'Address is required'}, status=400)
        
        challenge = secrets.token_hex(32)
        
        Challenge.objects.create(
            address=address,
            challenge=challenge,
            created_at=timezone.now()
        )
        
        return JsonResponse({'challenge': challenge})
    
class VerifyAndAuthenticateWalletView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        address = request.data.get('address')
        challenge = request.data.get('challenge')
        signature = request.data.get('signature')
        
        if not all([address, challenge, signature]):
            return JsonResponse({'error': 'Missing required fields'}, status=400)
        
        try:
            challenge_obj = Challenge.objects.get(
                address=address,
                challenge=challenge,
                created_at__gte=timezone.now() - timezone.timedelta(minutes=5)
            )
        except Challenge.DoesNotExist:
            return JsonResponse({'error': 'Invalid or expired challenge'}, status=400)
        
        message = encode_defunct(text=challenge)
        recovered_address = w3.eth.account.recover_message(message, signature=signature)
        
        if recovered_address.lower() != address.lower():
            return JsonResponse({'error': 'Invalid signature'}, status=401)
        
        # Return array of tickets ID linked to the possession of the wallet owner
        nfts_possessed = self.check_nft_possession(address)
        print(nfts_possessed)

        if not nfts_possessed:
            return JsonResponse({'hasNFT': False}, status=401)
        
        # Get users associated with each ticket ID
        users = []
        for ticketId in nfts_possessed:
            try:
                user = User.objects.get(username=str(ticketId))
                users.append(user)
            except User.DoesNotExist:
                return JsonResponse({'error': 'User not founded for this ticketId'}, status=404)

        if not users:
            return JsonResponse({'error': 'No valid users found'}, status=404)

        # Tokens contain all the users associated to the wallet in the payload
        refresh = RefreshToken.for_user(users[0])
        refresh['associated_users'] = [str(user.username) for user in users]
        access_token = refresh.access_token

        response = Response({"message": "Login successful", "ticketIds": nfts_possessed})

        response.set_cookie(
            'access_token_wallet',
            str(access_token),
            httponly=False,
            # domain='localhost',
            secure=False,
            samesite='None',
            max_age=settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'].total_seconds(),
            path='/'
        )

        response.set_cookie(
            'refresh_token_wallet',
            str(refresh),
            httponly=False,
            # domain='localhost',
            secure=False,
            samesite='None',
            max_age=settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'].total_seconds(),
            path='/'
        ) 
        
        challenge_obj.delete()
        return response
    
    def check_nft_possession(self, address):
        try:
            ticketIds = getTicketsIds(address)
            return ticketIds
        except Exception:
            return None

class VerifyTokenView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        access_token = request.COOKIES.get('access_token')
        access_token_wallet = request.COOKIES.get('access_token_wallet')

        if not access_token_wallet and not access_token:
            return Response({"error": "No token provided"}, status=status.HTTP_400_BAD_REQUEST)
    
        try:
            AccessToken(access_token)
            return Response({"valid": True}, status=status.HTTP_200_OK)
        except TokenError:
            pass
        
        try:
            AccessToken(access_token_wallet)
            return Response({"valid": True}, status=status.HTTP_200_OK)
        except TokenError:
            return Response({"valid": False}, status=status.HTTP_400_BAD_REQUEST)

## --------------------------------------------------------------------------------------------- ##
## ---------------------------       Ticket components       ----------------------------------- ##
## --------------------------------------------------------------------------------------------- ##


## Display ticket view 
class DisplayTicketView(APIView):
    print("\033[91mBefore auth\033[0m")  
    permission_classes = [AllowAny]
    print("\033[91mAfter auth\033[0m")  

    def get(self, request):
        print("\033[91mBefore ticket number\033[0m")   
        ticketNumber = request.query_params.get('ticketNumber')
        print("\033[91mAfter ticket number\033[0m")   
        if not ticketNumber:
            return Response({"detail": "Ticket number is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        ticket = self.get_object(ticketNumber)
        print("Ticket récupéré", ticket)
        
        # Security
        # if ticket.owner not in request.associated_users:
        #     raise PermissionDenied("You are not authorized to see this ticket.")
        
        serializer = TicketDisplaySerializer(ticket, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    def get_object(self, ticketNumber):
        try:
            owner = User.objects.get(username=ticketNumber)
            return Ticket.objects.filter(owner=owner).first() 
        except User.DoesNotExist:
            raise Http404("User does not exist")
        except Ticket.DoesNotExist:
            raise Http404("Ticket does not exist")
    
## Download ticket view      
class DownloadTicketView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, ticketNumber):
        try:
            owner = User.objects.get(username=ticketNumber)
            return Ticket.objects.filter(owner=owner).first() 
        except User.DoesNotExist:
            raise Http404("User does not exist")
        except Ticket.DoesNotExist:
            raise Http404("Ticket does not exist")

    def get(self, request):
        ticketNumber = request.query_params.get('ticketNumber')
        if not ticketNumber:
            return Response({"detail": "Ticket number is required"}, status=status.HTTP_400_BAD_REQUEST)

        ticket = self.get_object(ticketNumber)
        if ticket.owner not in request.associated_users:
            raise PermissionDenied("You are not authorized to see this ticket.")

        foreground_image_path = ticket.foreground.image.path
        background_image_path = ticket.background.image.path

        # Open the images with OpenCV
        foreground_image = cv2.imread(foreground_image_path, cv2.IMREAD_UNCHANGED)
        background_image = cv2.imread(background_image_path, cv2.IMREAD_UNCHANGED)

        # Convert images to RGBA if necessary
        if foreground_image.shape[2] == 3:
            foreground_image = cv2.cvtColor(foreground_image, cv2.COLOR_BGR2BGRA)
        if background_image.shape[2] == 3:
            background_image = cv2.cvtColor(background_image, cv2.COLOR_BGR2BGRA)

        # Ensure both images have the same size
        foreground_image = cv2.resize(foreground_image, (background_image.shape[1], background_image.shape[0]))

        # Create a mask from the foreground alpha channel
        alpha_foreground = foreground_image[:,:,3] / 255.0

        # Combine images
        for c in range(0, 3):
            background_image[:,:,c] = background_image[:,:,c] * (1 - alpha_foreground) + foreground_image[:,:,c] * alpha_foreground

        # Save the combined image to a temporary file or memory buffer
        _, encoded_image = cv2.imencode(".png", background_image)
        response = HttpResponse(encoded_image.tobytes(), content_type="image/png")
        response["Content-Disposition"] = f'attachment; filename="your_ticket.png"'
        return response
        

## --------------------------------------------------------------------------------------------- ##
## ------------------------------       BLOCK-CHAIN       -------------------------------------- ##
## --------------------------------------------------------------------------------------------- ##
      

class SendSecurityCodeView(APIView):
    def post(self, request, ticketId, userEmail):
        try:
            if not userEmail:
                return Response({'status': 'error', 'message': 'Email is required'}, status=status.HTTP_400_BAD_REQUEST)

            # Générer un code de sécurité
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

            # Stocker le code de sécurité (par exemple, dans la base de données ou le cache)
            # Pour cet exemple, nous utiliserons le cache Django
            cache.set(f'code_{ticketId}', code, timeout=300)  # Expire après 5 minutes

            # Envoyer l'email
            send_mail(
                'Your Security Code for Token Claim',
                f'Your security code is: {code}',
                settings.DEFAULT_FROM_EMAIL,
                [userEmail],
                fail_silently=False,
            )

            return Response({'status': 'success', 'message': 'Security code sent to your email'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'status': 'error', 'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)

## Simulation of claiming a ticket    
class ClaimTokenView(APIView):
    def post(self, request, tokenId, recipientAddress):
        try:
            # Vérifier le code de sécurité
            code = request.data.get('code')
            stored_code = cache.get(f'code_{tokenId}')

            if not code or code != stored_code:
                return Response({'status': 'error', 'message': 'Invalid or expired security code'}, status=status.HTTP_400_BAD_REQUEST)

            # Si le code est valide, procéder à la réclamation
            tx_receipt = claimTicket(tokenId, recipientAddress)
            response_data = {
                'status': 'success',
                'message': 'Token successfully claimed',
                'transaction_hash': tx_receipt.transactionHash.hex(),
                'block_number': tx_receipt.blockNumber,
            }
            
            # Supprimer le code de sécurité utilisé
            cache.delete(f'security_code_{tokenId}')

            return Response(response_data, status=status.HTTP_200_OK)
        except Exception as e:
            error_message = str(e)
            return Response({'status': 'error', 'message': error_message}, status=status.HTTP_400_BAD_REQUEST)

## Simulation 
class IsAlreadyClaimedView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request, tokenId):
        try:
            response = isAlreadyClaimed(tokenId)
            return Response({"is_claimed": response}, status=status.HTTP_200_OK)
        except Exception as e:
            error_message = str(e)
            return Response({'status': 'error', 'message': error_message}, status=status.HTTP_400_BAD_REQUEST)
        