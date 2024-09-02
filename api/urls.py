from django.urls import path
from .views import *

urlpatterns = [
    path('display-ticket/', DisplayTicketView.as_view(), name='display-ticket'),
    path('download-ticket/', DownloadTicketView.as_view(), name='download-ticket'),
    path('verify-token/', VerifyTokenView.as_view(), name='verify-token'),
    path('claim-ticket/<int:tokenId>/<str:recipientAddress>/', ClaimTokenView.as_view(), name='claim-token'),
    path('get-code/<int:ticketId>/<str:userEmail>/', SendSecurityCodeView.as_view(), name='get-code'),
    path('is-already-claimed/<int:tokenId>/', IsAlreadyClaimedView.as_view(), name='is-already-claimed-token'),
    path('get-challenge/', GetChallengeView.as_view(), name='get_challenge'),
    path('verify-and-authenticate-wallet/', VerifyAndAuthenticateWalletView.as_view(), name='verify_and_authenticate-wallet'),
]