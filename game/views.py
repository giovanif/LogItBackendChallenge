from ast import For
import json
import requests as rq

from django.http import JsonResponse
from django.shortcuts import render
from game.models import Hand, Match
# View de inicio do jogo, cria os objetos, rodada, mão do jogador e mão da banca, faz a distribuição inicial e exibe o primeiro JSON
def start(request, player_name, bet):
    if request.method == 'GET':
        player_name = player_name.lower()
        game_match = Match()
        game_match.player_name = player_name
        game_match.save()

        player_hand = Hand()
        player_hand.match = game_match
        player_hand.hand_number = 1
        player_hand.hand_address = f'https://deckofcardsapi.com/api/deck/{game_match.deck_id}/pile/{player_name}_hand_1'
        player_hand.hand_bet = bet
        player_hand.hand_points = 0
        player_hand.save()
        
        player_hand.draw(card_count=2)

        dealer_hand = Hand()
        dealer_hand.match = game_match
        dealer_hand.hand_number = 99
        dealer_hand.hand_address = f'https://deckofcardsapi.com/api/deck/{game_match.deck_id}/pile/dealer_hand_1'
        dealer_hand.hand_bet = bet
        dealer_hand.hand_points = 0
        dealer_hand.save()

        
        dealer_hand.draw(card_count=2)

        return game_match.show()
        #draw_old(match_id=game_match.match_id, player_hand=1, card_count=2)
        #draw_old(match_id=game_match.match_id, player_hand=1, dealer_hand=True,card_count=2)

# View que chama a função para distibuição das cartas
def draw(request, hand_id):
    hand = Hand.objects.get(hand_id = hand_id)
    return hand.draw()
# View que chama a função de divisão da mão
def split(request, hand_id):
    hand = Hand.objects.get(hand_id = hand_id)
    return hand.split()
# View que chama a função de parada e troca de rodada
def stop(request, hand_id):
    hand = Hand.objects.get(hand_id = hand_id)
    return hand.stop()