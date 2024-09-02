from django.urls import path
from .views import *

from .views import (
    HeroDataJsonView,
    HomePageDataView,
    TicketDataJsonView,
    VideoSectionDataView,
    OnBoardingToTheWalletDataView,
    ImageOnboardingView,
    AboutTheTicketDataView,
    FAQView,
)

urlpatterns = [
    path('hero-data-json/', HeroDataJsonView.as_view(), name='hero_data_json'),
    path('home-data-json/', HomePageDataView.as_view(), name='home_data_json'),
    path('ticket-data-json/', TicketDataJsonView.as_view(), name='ticket_data_json'),
    path('video-section-data-json/', VideoSectionDataView.as_view(), name='video_section_data_json'),
    path('onboarding-data-json/', OnBoardingToTheWalletDataView.as_view(), name='onboarding_data_json'),
    path('image-onboarding-json/', ImageOnboardingView.as_view(), name='image_onboarding_json'),
    path('about-ticket-data-json/', AboutTheTicketDataView.as_view(), name='about_ticket_data_json'),
    path('faq-json/', FAQView.as_view(), name='faq_json'),
]
