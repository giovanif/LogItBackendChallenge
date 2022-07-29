from ast import For
import json
import requests as rq

from django.http import JsonResponse
from django.shortcuts import render
from game.models import Hand, Match

def new(request, player_name, bet):
    if request.method == 'GET' or request.method == 'POST':
        game_match = Match()
        game_match.player_name = player_name.lower()
        game_match.status = 'created'
        game_match.save()

        player_hand = Hand()
        player_hand.match = game_match
        player_hand.number = 1
        player_hand.address = f'https://deckofcardsapi.com/api/deck/{game_match.deck_id}/pile/{player_name}_hand_1'
        player_hand.bet = bet
        player_hand.prize = 0
        player_hand.points = 0
        player_hand.status = 'turn'
        player_hand.save()

        dealer_hand = Hand()
        dealer_hand.match = game_match
        dealer_hand.number = -1
        dealer_hand.address = f'https://deckofcardsapi.com/api/deck/{game_match.deck_id}/pile/dealer_hand_1'
        dealer_hand.bet = 0
        dealer_hand.prize = 0
        dealer_hand.points = 0
        dealer_hand.status = 'waiting'
        dealer_hand.save()

        return game_match.show()

# View de inicio do jogo, cria os objetos, rodada, mão do jogador e mão da banca, faz a distribuição inicial e exibe o primeiro JSON
def start(request, match_id):
    if request.method == 'GET' or request.method == 'POST':
        game_match = Match.objects.get(match_id=match_id)

        if game_match.status == 'created':
            player_hand = Hand.objects.filter(number = 1, match_id= match_id)[0]
            dealer_hand = Hand.objects.filter(number = -1, match_id= match_id)[0]

            player_hand.draw(show=False, card_count=2)
            dealer_hand.draw(show=False, card_count=2)

            game_match.status = f'{game_match.player_name}_hand_1_turn'

            game_match.save()

        return game_match.show()

# View que chama a função para distibuição das cartas
def draw(request, match_id):
    if request.method == 'GET' or request.method == 'POST':
        hand = Hand.objects.filter(status = 'turn', match_id= match_id)[0]
        return hand.draw()
# View que chama a função de divisão da mão
def split(request, match_id):
    if request.method == 'GET' or request.method == 'POST':
        hand = Hand.objects.filter(status = 'turn', match_id= match_id)[0]
        return hand.split()
# View que chama a função de parada e troca de rodada
def stop(request, match_id):
    if request.method == 'GET' or request.method == 'POST':
        hand = Hand.objects.filter(status = 'turn', match_id= match_id)[0]
        return hand.stop()