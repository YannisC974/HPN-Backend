from django.shortcuts import render
from django.http import JsonResponse
from django.views.generic import View
from .models import *

class HeroDataJsonView(View):
    def get(self, request, *args, **kwargs):
        hero_data = list(HeroData.objects.values('title', 'subtitle')) 
        return JsonResponse(hero_data, safe=False)
    
class HomePageDataView(View):
    def get(self, request, *args, **kwargs):
        hero_data = list(LoginPageData.objects.values('description')) 
        return JsonResponse(hero_data, safe=False)
    
class TicketDataJsonView(View):
    def get(self, request, *args, **kwargs):
        ticket_data = list(TicketData.objects.values('title', 'description')) 
        return JsonResponse(ticket_data, safe=False)
    
class VideoSectionDataView(View):
    def get(self, request, *args, **kwargs):
        data = list(VideoSectionData.objects.values('title', 'description', 'thumbnail', 'link')) 
        return JsonResponse(data, safe=False)
    
class OnBoardingToTheWalletDataView(View):
    def get(self, request, *args, **kwargs):
        data = list(OnBoardingToTheWalletData.objects.values('description')) 
        return JsonResponse(data, safe=False)
    
class ImageOnboardingView(View):
    def get(self, request, *args, **kwargs):
        data = list(ImageOnboarding.objects.values('onboarding_data', 'image')) 
        return JsonResponse(data, safe=False)
    
class AboutTheTicketDataView(View):
    def get(self, request, *args, **kwargs):
        data = list(AboutTheTicketData.objects.values('description1', 'description2')) 
        return JsonResponse(data, safe=False)
    
class FAQView(View):
    def get(self, request, *args, **kwargs):
        data = list(FAQ.objects.values('question', 'answer')) 
        return JsonResponse(data, safe=False)
