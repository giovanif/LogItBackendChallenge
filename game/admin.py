from atexit import register
from django.contrib import admin
from .models import Hand, Match
# Registro dos modelos no banco de dados
admin.site.register(Match)
admin.site.register(Hand)