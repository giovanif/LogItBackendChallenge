import random
import string
import json
import requests as rq

from tabnanny import verbose
from urllib import response
from django.http import JsonResponse
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
    status = models.CharField(max_length=20)

    class Meta:
        verbose_name_plural = 'Matches'

    def save(self, *args, **kwargs):
        super(Match, self).save(*args, **kwargs)

    def __str__(self) -> str:
        return self.match_id
        
    # Função que exibe o JSON com as informações do jogo
    def show(self):
        remaining_cards = json.loads(rq.get(url=f'https://deckofcardsapi.com/api/deck/{self.deck_id}').text)['remaining']
        hands = Hand.objects.filter(match=self) 
        player_hands = {}
        dealer_hand = {}

        for hand in hands:
            if self.status == 'created':
                player_cards = [{}]
                dealer_cards = [{}]
            else:
                if hand.number != -1:
                    player_cards = json.loads(rq.get(url=f'{hand.address}/list').text)['piles'][f'{self.player_name}_hand_{hand.number}']['cards']
                else:
                    dealer_cards = json.loads(rq.get(url=f'{hand.address}/list').text)['piles']['dealer_hand_1']['cards']

            if hand.number != -1:
                player_hands[f'{self.player_name}_hand_{hand.number}'] = {
                    'bet' : hand.bet,
                    'prize' : hand.prize,
                    'points' : hand.points,
                    'status' : hand.status,
                    'cards' : player_cards
                }
            else:
                if hand.status != 'waiting':
                    dealer_hand['dealer_hand_1'] = {
                        'points' : hand.points,
                        'cards' : dealer_cards
                    }
                else:
                    dealer_hand['dealer_hand_1'] = {
                        'points' : hand.points,
                        'cards' : dealer_cards[0]
                    }

        response = {
            'match_id' : self.match_id,
            'deck_id' : self.deck_id,
            'status' : self.status,
            'remaining_cards' : remaining_cards,
            'player_hands' : player_hands,
            'dealer_hand' : dealer_hand,
        }
        return JsonResponse(response)

    def finish(self):
        player_hands = Hand.objects.filter(match=self).exclude(number=-1)
        dealer_hand = Hand.objects.filter(match=self, number=-1)[0]

        for hand in player_hands:
            if hand.points <= 21:
                if dealer_hand.points <= 21:
                    if hand.points < dealer_hand.points:
                        hand.prize = 0
                        hand.status = 'lose'
                    elif hand.points == dealer_hand.points:
                        hand.prize = hand.bet
                        hand.status = 'tie'
                    else:
                        hand.prize = float(hand.bet) * 2 if hand.points == 21 else float(hand.bet) * 1.5
                        hand.status = 'win'
                else:
                    hand.prize = float(hand.bet) * 2 if hand.points == 21 else float(hand.bet) * 1.5
                    hand.status = 'win'
            else:
                hand.prize = 0
                hand.status = 'lose'
        self.status = 'finished'
        hand.save()
        self.show()

# classe referente à cada mão de cartas utilizada no jogo
class Hand(models.Model):
    id = models.CharField(primary_key=True, default=random_string, max_length=15, editable=False)
    number = models.IntegerField()
    bet = models.DecimalField(max_digits=10, decimal_places=2)
    prize = models.DecimalField(max_digits=10, decimal_places=2)
    address = models.CharField(max_length=150)
    status = models.CharField(max_length=15)
    points = models.IntegerField()
    match = models.ForeignKey(to=Match, on_delete=models.CASCADE)

    class Meta:
        verbose_name_plural = 'Hands'

    def save(self, *args, **kwargs):
        super(Hand, self).save(*args, **kwargs)

    def __str__(self) -> str:
        return self.id

    # Função que faz a contagem dos pontos de cada mão
    def count_points(self):
        points = 0
        
        if self.number == -1:
            if self.status != 'turn':
                dealer_card = json.loads(rq.post(url=f'{self.address}/list').text)['piles']['dealer_hand_1']['cards'][0]
                points = card_value(dealer_card, points)
                self.points = points
                self.save()
                return
            else:
                cards = json.loads(rq.post(url=f'{self.address}/list').text)['piles']['dealer_hand_1']['cards']
        else:
            cards = json.loads(rq.post(url=f'{self.address}/list').text)['piles'][f'{self.match.player_name}_hand_{self.number}']['cards']
        
        for card in cards:
                points += card_value(card, points)
        
        self.points = points
        self.save()

        if points == 21:
            self.status = 'blackjack'
            self.save()
            self.stop()
        elif points > 21:
            self.status = 'burst'
            self.bet = 0
            self.save()
            self.stop()

    # Função que distribui as cartas para a mão
    def draw(self, show=True, card_count=1):
        cards = json.loads(rq.get(url=f'https://deckofcardsapi.com/api/deck/{self.match.deck_id}/draw/?count={card_count}').text)['cards']
        cards_codes = []

        for card in cards:
            cards_codes.append(card['code'])
    
        rq.get(url=f'{self.address}/add/?cards={",".join(cards_codes)}')

        self.count_points()

        if show:
            return self.match.show()

    # Função que permite dividir uma mão em duas, caso tenha duas cartas do mesmo valor
    def split(self):
        cards = json.loads(rq.post(url=f'{self.address}/list').text)['piles'][f'{self.match.player_name}_hand_{self.number}']['cards']
        hands_count = len(Hand.objects.filter(match = self.match))

        if len(cards) == 2 and card_value(cards[0]) == card_value(cards[1]):
            new_hand = Hand()
            new_hand.match = self.match
            new_hand.number = self.number + 1
            new_hand.address = f'{self.address[:-1]}{hands_count}'
            new_hand.bet = self.bet
            new_hand.prize = 0
            new_hand.status = 'waiting'
            card_code = cards[1]['code']
            rq.get(url=f'{self.address}/draw/?cards={card_code}')
            rq.get(url=f'{new_hand.address}/add/?cards={card_code}')
            new_hand.count_points()
            new_hand.save()

        self.count_points()
        return self.match.show()

    # Função de parada, finaliza o turno de uma mão e inicia a próxima
    def stop(self):
        self.status = 'stopped' if self.status == 'turn' else self.status
        self.save()

        dealer_hand = Hand.objects.filter(match=self.match, number=-1)[0]
        next_hand_search = Hand.objects.filter(match=self.match, number=self.number + 1)

        if next_hand_search.exists():
            next_hand = Hand.objects.get(id = next_hand_search[0].id)
            next_hand.status = 'turn'
            next_hand.save(update_fields=['status'])
            self.match.status = f'{self.match.player_name}_hand_{next_hand.number}_turn'
        else:
            self.match.status = f'dealer_hand_1_turn'
            dealer_hand.status = 'turn'
            dealer_hand.count_points
            while dealer_hand.points < 17:
                dealer_hand.draw()
            self.match.finish()

        return self.match.show()

# Função que verifica o valor das cartas
def card_value(card, hand_points=0):
    if card['value'] not in ['KING','QUEEN','JACK','ACE']:
        return int(card['value'])
    else:
        if card['value'] != 'ACE':
            return 10
        else:
            return 11 if hand_points <= 10 else 1