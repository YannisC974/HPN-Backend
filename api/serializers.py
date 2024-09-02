from rest_framework import serializers
from .models import Ticket, Layer, FAQ
from django.contrib.auth.models import User
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        # Verify if attrs (username and password) are correct and update self.user based on that
        data = super().validate(attrs)
        
        refresh = RefreshToken(data['refresh'])
        
        refresh['associated_users'] = [str(self.user)]

        data['refresh'] = str(refresh)
        data['access'] = str(refresh.access_token) 
        
        return data

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "password"]
        extra_kwargs = {"password": {"read_only": True}}

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user

class LayerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Layer
        fields = ['id', 'name']

class TicketDisplaySerializer(serializers.ModelSerializer):
    foreground = LayerSerializer()
    background = LayerSerializer()
    full_ticket_front = serializers.ImageField(use_url=True)
    full_ticket_back = serializers.ImageField(use_url=True)

    class Meta:
        model = Ticket
        fields = ['foreground', 'background', 'full_ticket_front', 'full_ticket_back', 'owner']
    
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        request = self.context.get('request')
        if request:
            representation['full_ticket_front'] = request.build_absolute_uri(instance.full_ticket_front.url)
            representation['full_ticket_back'] = request.build_absolute_uri(instance.full_ticket_back.url)
        return representation

class FAQSerializer(serializers.ModelSerializer):
    class Meta:
        model = FAQ
        fields = ['question', 'answer', 'order']