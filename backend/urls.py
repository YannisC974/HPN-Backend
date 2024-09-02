from django.contrib import admin
from django.urls import path, include
from django.conf import settings  
from django.urls import path, include  
from django.conf.urls.static import static  
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from api.views import CustomTokenObtainPairView, CustomTokenRefreshView, LogoutViewAll, LogoutViewLogin, LogoutViewWallet


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api-auth", include("rest_framework.urls")),
    path("api/token/", CustomTokenObtainPairView.as_view(), name="get-token"),
    path("api/token/refresh/", CustomTokenRefreshView.as_view(), name="refresh"),
    path('api/logout/', LogoutViewAll.as_view(), name='logout'),
    path('api/logout-wallet/', LogoutViewWallet.as_view(), name='logout-wallet'),
    path('api/logout-login/', LogoutViewLogin.as_view(), name='logout-login'),
    path("api/", include("api.urls")),
    path("data/", include("data.urls")),
]

if settings.DEBUG: 
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
