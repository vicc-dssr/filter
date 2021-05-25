"""filter URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path
from django.contrib.auth import views as auth_views
from filterapp import views
import debug_toolbar

urlpatterns = [
    path('', views.index, name='index'),
    path('login/', auth_views.LoginView.as_view()),
    path("select2/", include("django_select2.urls")),
    path('api/', include('filterapp.urls')),
    path('admin/', admin.site.urls),
    path('api-auth/', include('rest_framework.urls')),
    path('accounts/', include('django.contrib.auth.urls')),
    path('activate/<uidb64>/<token>/', views.activate, name='activate'),
    path('debug/', include(debug_toolbar.urls)),
    path('password-reset/', views.password_reset, name='password_reset'),
    path('reset/<uidb64>/<token>', views.reset, name='reset'),
    path('deactivate/', views.deactivate, name='deactivate'),
    path('deactivate_account/', views.deactivate_account, name='deactivate_account'),
]
