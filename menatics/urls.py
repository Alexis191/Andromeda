from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    #Esto conecta todas las URLs que creemos en la carpeta gestion/urls.py
    path('', include('gestion.urls')),
]
