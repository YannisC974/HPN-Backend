from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, AuthenticationFailed
from django.contrib.auth.models import User

# class CustomJWTAuthentication(JWTAuthentication):
#     def authenticate(self, request):
#         access_token = request.COOKIES.get('access_token')
#         if not access_token:
#             return None

#         try:
#             validated_token = self.get_validated_token(access_token)
#             user = self.get_user(validated_token)
#             return (user, validated_token)
#         except InvalidToken:
#             raise AuthenticationFailed('Invalid token')

class CustomJWTAuthentication(JWTAuthentication):

    def authenticate(self, request):
        access_token = request.COOKIES.get('access_token')
        acces_token_wallet = request.COOKIES.get('access_token_wallet')
        
        if not acces_token_wallet:
            pass
        if not access_token:
            return None
        
        try:
            return self.get_users(request, access_token)
        except InvalidToken:
            pass

        try:
            return self.get_users(request, access_token)
        except InvalidToken:
            raise AuthenticationFailed('Invalid token')

    def get_users(self, request, access_token):
        # Validate and decode the access token
        validated_token = self.get_validated_token(access_token)
        
        # Extract associated users from the token payload
        payload = validated_token.payload
        associated_usernames = payload.get('associated_users', [])
        users = User.objects.filter(username__in=associated_usernames)
        
        # Handle empty list or handle other cases as needed
        if not users.exists():
            raise AuthenticationFailed('No valid users found for this token.')

        # Attach the primary user and associated users to the request object
        primary_user = users.first() if users else None
        request.user = primary_user
        request.associated_users = users

        return (primary_user, validated_token) 