"""blackjack URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.0/topics/http/urls/
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
from django.urls import path
from game.views import draw, new, split, start, stop

urlpatterns = [
    # Url predefinida do Django para administração do banco de dados
    path('admin/', admin.site.urls),
    
    # Url que solicita o inicio do jogo
    path('game/new/<str:player_name>/<str:bet>', new),

    # Url que solicita a distribuição inicial
    path('game/start/<str:match_id>', start),

    # Url que solicita a compra de uma carta
    path('game/draw/<str:match_id>', draw),
    
    # Url que solicita a divisão de uma mão
    path('game/split/<str:match_id>', split),
    
    # Url que solicita a parada e troca de turno
    path('game/stop/<str:match_id>', stop),
]
