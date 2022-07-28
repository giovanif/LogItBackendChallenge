import random
import string
import json
from tabnanny import verbose
from urllib import response
from django.http import JsonResponse
import requests as rq

from django.db import models

# Gera uma string aleatória para ser utilizada como identificador
def random_string():
    return ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(12))
# Gera um novo deck de baralho
def generate_deck():
    return json.loads(rq.post(url='https://deckofcardsapi.com/api/deck/new/shuffle/?deck_count=1').text)['deck_id']
# Classe referente à rodada do jogo
class Match(models.Model):
    match_id = models.CharField(primary_key=True, default=random_string, max_length=15, editable=False)
    deck_id = models.CharField(max_length=15, default=generate_deck, editable=False)
    player_name = models.CharField(max_length=50)

    class Meta:
        verbose_name_plural = 'Matches'

    def save(self, *args, **kwargs):
        super(Match, self).save(*args, **kwargs)

    def __str__(self) -> str:
        return self.match_id
    # Função que exibe o JSON com as informações do jogo
    def show(self, dealer_reveal=False):
        hands = Hand.objects.filter(match=self).order_by('-hand_number')
        player_hands = {}
        dealer_hand = {}

        for hand in hands:
            hand_status = 'stopped' if hand.hand_stopped else 'active'
            if hand.hand_number != 99:
                player_hands[f'{self.player_name}_hand_{hand.hand_number}'] = {
                    'hand_id' : hand.hand_id,
                    'hand_points' : hand.hand_points,
                    'hand_status' : hand_status,
                    'hand_cards' : json.loads(rq.get(url=f'{hand.hand_address}/list').text)['piles'][f'{self.player_name}_hand_{hand.hand_number}']['cards']
                }
            else:
                if dealer_reveal:
                    dealer_hand['dealer_hand_1'] = {
                        'hand_points' : hand.hand_points,
                        'hand_status' : hand_status,
                        'hand_cards' : json.loads(rq.get(url=f'{hand.hand_address}/list').text)['piles']['dealer_hand_1']['cards']
                    }
                else:
                    dealer_hand['dealer_hand_1'] = {
                        'hand_points' : hand.hand_points,
                        'hand_status' : hand_status,
                        'hand_cards' : json.loads(rq.get(url=f'{hand.hand_address}/list').text)['piles']['dealer_hand_1']['cards'][0]
                    }

        response = {
            'match_id' : self.match_id,
            'player_hands' : player_hands,
            'dealer_hand' : dealer_hand,
        }

        return JsonResponse(response)
# classe referente à cada mão de cartas utilizada no jogo
class Hand(models.Model):
    hand_id = models.CharField(primary_key=True, default=random_string, max_length=15, editable=False)
    hand_number = models.IntegerField()
    hand_bet = models.DecimalField(max_digits=10, decimal_places=2)
    hand_address = models.CharField(max_length=150)
    hand_stopped = models.BooleanField(default=False)
    hand_points = models.IntegerField()
    match = models.ForeignKey(to=Match, on_delete=models.CASCADE)

    class Meta:
        verbose_name_plural = 'Hands'

    def save(self, *args, **kwargs):
        super(Hand, self).save(*args, **kwargs)

    def __str__(self) -> str:
        return self.hand_id
    # Função que faz a contagem dos pontos de cada mão
    def count_points(self, dealer_turn = False):
        points = 0
        # Função que verifica o valor das cartas
        def verify_card(card):
            if card['value'] not in ['KING','QUEEN','JACK','ACE']:
                return int(card['value'])
            else:
                if card['value'] != 'ACE':
                    return 10
                else:
                    return 11 if points <= 10 else 1
        
        if not dealer_turn and self.hand_number == 99:
            dealer_card = json.loads(rq.post(url=f'{self.hand_address}/list').text)['piles']['dealer_hand_1']['cards'][0]
            points = verify_card(dealer_card)
            self.hand_points = points
            self.save()
            return
        else:
            cards = json.loads(rq.post(url=f'{self.hand_address}/list').text)['piles'][f'{self.match.player_name}_hand_{self.hand_number}']['cards']
        if dealer_turn and self.hand_number == 99:
            cards = json.loads(rq.post(url=f'{self.hand_address}/list').text)['piles']['dealer_hand_1']['cards']
        for card in cards:
                points += verify_card(card)
            
        if points >= 21:
            self.stop()

        self.hand_points = points
        self.save()
    # Função que distribui as cartas para a mão
    def draw(self, card_count=1):
        if not self.hand_stopped:
            cards = json.loads(rq.get(url=f'https://deckofcardsapi.com/api/deck/{self.match.deck_id}/draw/?count={card_count}').text)['cards']
            cards_codes = []

            for card in cards:
                cards_codes.append(card['code'])

            rq.get(url=f'{self.hand_address}/add/?cards={",".join(cards_codes)}')

            self.count_points()

        return self.match.show()
    # Função que permite dividir uma mão em duas, caso tenha duas cartas do mesmo valor
    def split(self):
        cards = json.loads(rq.post(url=f'{self.hand_address}/list').text)['piles'][self.match.player_name]['cards']
        hands_count = len(Hand.objects.get(match = self.match))

        if not self.hand_stoped:
            if len(cards) == 2 and cards[0]['value'] == cards[1]['value']:
                new_hand = Hand()
                new_hand.match = self.match
                new_hand.hand_number = hands_count
                new_hand.hand_address = self.hand_address[:-1] + hands_count
                new_hand.hand_bet = self.hand_bet
                card_code = cards[1]['code']
                rq.get(url=f'{self.hand_address}/add/?cards={card_code}')
                new_hand.count_points()
                new_hand.save()

        self.count_points()

        return self.match.show()
    # Função de parada, finaliza o turno do jogador e inicia o turno da banca
    def stop(self):
        hands = Hand.objects.filter(match=self.match)
        stopped_hands = 0
        hands_count = len(hands) - 1 

        if self.hand_id != 99:
            self.hand_stopped = True
            self.save()
            for hand in hands:
                if hand.hand_stopped == True:
                    stopped_hands += 1 

        if stopped_hands == hands_count:
            print('teste')
        
        if self.hand_id == 99 and stopped_hands == hands_count:
            while self.hand_points < 17:
                self.draw()