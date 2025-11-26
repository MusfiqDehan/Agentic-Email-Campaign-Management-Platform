from django.urls import path, include

app_name = 'authentication'

urlpatterns = [
    path('api/v1/', include('apps.authentication.api.v1.urls')),
]