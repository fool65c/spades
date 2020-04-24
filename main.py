import os
import sys
import uuid
import json as JSON
import asyncio 

from typing import List, Dict

from sanic import Sanic
from sanic.response import json
from sanic.websocket import WebSocketProtocol

from game.player import Player
from game.gameplay import Game
from game.deck import Card

app = Sanic(name="Spades")

class Stream:
    __name__ = "game"
    def __init__(self):
        self.players: Dict[str, Player] = {}
        self.games: Dict[str, Game] = {}

    async def __call__(self, *args, **kwargs):
        await self.stream(*args, **kwargs)

    async def __notify_all(self, data: Dict[any, any]):
        await asyncio.wait([p.ws.send(JSON.dumps(data)) for p in self.players.values()])

    async def __game_definition_updates(self):
        await self.__notify_all({
            "type": "avail-games",
            "data": [g.to_json() for g in self.games.values() if not g.in_progress ]
        })

    # PLAYER METHODS
    async def __register_player(self, ws):
        p_id = str(uuid.uuid1())
        await ws.send(JSON.dumps({'type': 'update-player-id', 'id': p_id}))

    async def __create_player(self, p_id, name, ws):
        self.players[p_id] = Player(p_id, name, ws)
        await self.__game_definition_updates()

    async def __player_rejoin(self, p_id, name, ws):
        if p_id in self.players:
            print('playter fouund, updating')
            self.players[p_id].ws = ws
            self.players[p_id].name = name
        else:
            print('creating new player eventhough they are joining')
            self.players[p_id] = Player(p_id, name, ws)

        for g in self.games.values():
            if p_id in [p.id for p in g.players]:
                if g.in_progress and not g.winner:
                    print('player was in an inprogress game, rejoining')
                    await self.players[p_id].ws.send(JSON.dumps({
                        'type': 'set-game-id',
                        'gameId': g.id
                    }))

                    g.reconnect_player(self.players[p_id])
                    await self.__send_team_updates(g.id)
                    await self.__update_player_cards(self.players[p_id])
                    await self.__send_score_updates(g.id)
                    await self.__update_round_stats(g.id)
                    current_bidder = self.games[g.id].current_round.current_bidder
                    if current_bidder and current_bidder.id == p_id:
                        await self.__notify_next_bidder(g.id)
                    elif self.games[g.id].current_round.current_hand.winner:
                        await self.__notify_hand_result(g.id)
                    else:
                        await self.__notify_active_hand(g.id)
                    return
                elif not g.in_progress:
                    print('player was in a game that hadn\'t started, rejoining')
                    await self.players[p_id].ws.send(JSON.dumps({
                        'type': 'set-game-id',
                        'gameId': g.id
                    }))
                    await self.__game_definition_updates()
                    return
        
        # If nothing else happens send them the games
        print('no games for the rejoiner, sending them the list of games')
        await self.__game_definition_updates()
            

    # GAME CREATION / ENROLLMENT METHODS

    async def __create_game(self, name):
        g = Game(name)
        self.games[str(g.id)] = g
        await self.__game_definition_updates()

    async def __join_game(self, g_id, p_id, team):
        if p_id in [p.id for p in self.games[g_id].players]:
            raise Exception(f'Player {self.players[p_id].name} already in game')
        if team == "team1":
            self.games[g_id].team1.append(self.players[p_id])
        else:
            self.games[g_id].team2.append(self.players[p_id])
        await self.__game_definition_updates()

    async def __start_game(self, g_id):
        self.games[g_id].start()
        for p in self.games[g_id].players:
            await self.__update_player_cards(p)
            if p.ws:
                await p.ws.send(JSON.dumps({
                    'type': 'game-started',
                    'data': g_id
                }))
        await self.__send_team_updates(g_id)
        await self.__notify_next_bidder(g_id)
        await self.__update_round_stats(g_id)
        await self.__send_score_updates(g_id)

    # GAME PLAY CARD ACTIOND AND BIDDING

    async def __update_player_cards(self, player: Player):
        try:
            await player.ws.send(JSON.dumps({
                'type': 'player-cards',
                'cards': player.to_json()['cards']
            }))
        except:
            print("Cound not contact player")

    async def __notify_next_bidder(self, g_id: str):
        next_bidder = self.games[g_id].current_round.current_bidder
        if next_bidder:
            await next_bidder.ws.send(JSON.dumps({
                'type': 'request-player-bid'
            }))
        else:
            self.games[g_id].current_round.start()
            await self.__notify_active_hand(g_id)

    async def __record_player_bid(self, g_id, p_id, bid):
        self.games[g_id].current_round.set_player_bid(p_id, int(bid))
        await self.__update_round_stats(g_id)
        await self.__notify_next_bidder(g_id)

    # PLAYING HAND AN UPDATING RESULTS
    async def __notify_active_hand(self, g_id: str):
        await self.__notify_players_in_game(
            g_id,
            {
                'type': 'active-hand',
                'data': self.games[g_id].current_round.current_hand.active_hand_json()
            }
        )

    async def __notify_hand_result(self, g_id: str):
        await self.__notify_players_in_game(
            g_id,
            {
                'type': 'hand-result',
                'data': self.games[g_id].current_round.current_hand.result_json()
            }
        )

    async def __play_card(self, g_id: str, p_id: str, card: Dict[str, str]):
        player = self.players[p_id]
        c = Card.from_str(value=card['value'], suit=card['suit'])
        if self.games[g_id].current_round.current_hand:
            self.games[g_id].current_round.current_hand.play_card(player,c)
        else:
            return
            
        await self.__update_player_cards(player)
        if self.games[g_id].winner:
            await self.__notify_players_in_game(
                g_id,
                {
                    'type': 'winner',
                    'winner': self.games[g_id].winner
                } 
            )
        elif self.games[g_id].current_round.current_hand.winner:
            await self.__notify_active_hand(g_id)
            await self.__notify_hand_result(g_id)
            await self.__update_round_stats(g_id)
            await self.__start_new_round(g_id)
        else:
            await self.__notify_active_hand(g_id)

    async def __update_round_stats(self, g_id):
        for p in self.games[g_id].players:
            await self.__update_player_cards(p)
        await self.__notify_players_in_game(
            g_id,
            {
                'type': 'update-round-stats',
                'stats': self.games[g_id].current_round.stats
            }
        )

    async def __start_new_round(self, g_id):
        self.__notify_players_in_game(g_id,
        {
            'type': 'start-new-round'
        })

    async def __send_score_updates(self, g_id):
        await self.__notify_players_in_game(
            g_id,
            {
                'type': 'score-update',
                'score': self.games[g_id].get_round_scores()
            }
        )

    async def __send_team_updates(self, g_id):
        await self.__notify_players_in_game(
            g_id,
            {
                'type': 'team-definitions',
                'team1': [p.to_safeson() for p in self.games[g_id].team1],
                'team2': [p.to_safeson() for p in self.games[g_id].team2]
            }

        )

    async def __start_new_hand(self, g_id):
        if self.games[g_id].current_round.complete:
            self.games[g_id].start_next_round()
            await self.__send_score_updates(g_id)
            await self.__notify_players_in_game(
                g_id,
                {
                    'type': 'start-new-round'
                }
            )
            await self.__update_round_stats(g_id)
            await self.__notify_next_bidder(g_id)
        else:
            self.games[g_id].current_round.start_new_hand()
            await self.__notify_active_hand(g_id)

    
    async def __notify_players_in_game(self, g_id, message):
        for p in self.games[g_id].players:
            if p.ws:
                try:
                    await p.ws.send(JSON.dumps(message))
                except:
                    print(f'count not contact {p.name}')

    async def type_router(self, data, ws):
        dt = str(data['type'])
        p_id = data['id']
        g_id = data['game_id']

        message = None
        if 'message' in data:
            message = data['message']
        print(JSON.dumps(data))
        # Router
        try:
            if 'register-player' == dt:
                await self.__register_player(ws)
            elif 'create-game' == dt:
                await self.__create_game(message)
            elif 'create-player' == dt:
                await self.__create_player(message['id'], message['name'], ws)
            elif 'join-game' == dt:
                await self.__join_game(g_id, p_id, message['team'])
            elif 'start-game' == dt:
                await self.__start_game(message)
            elif 'record-player-bid' == dt:
                await self.__record_player_bid(g_id, p_id, message)
            elif 'play-card' == dt:
                await self.__play_card(g_id, p_id, message)
            elif 'start-next-hand' == dt:
                await self.__start_new_hand(g_id)
            elif 'player-rejoin' == dt:
                await self.__player_rejoin(p_id, message, ws)
            else:
                print(f'unknown type: {data["type"]}')
        except Exception as e:
            print("Unexpected error:", str(e))
            await self.players[p_id].ws.send(JSON.dumps({
                'type': 'error',
                'data':  str(e)
            }))
        except:
            print("Unexpected error:", sys.exc_info())
            # raise sys.exc_info()
            await self.players[p_id].ws.send(JSON.dumps({
                'type': 'error',
                'data':  str(sys.exc_info()[0])
            }))

    async def stream(self, request, ws):
        while True:
            data = await ws.recv()
            data = JSON.loads(data)

            if 'type' in data:
              await self.type_router(data, ws)
            else:
                print(f'unknown data: {data}')
            

app.static('/', './web-app/index.html')
app.static('/web-app/', './web-app/')
app.add_websocket_route(Stream(), "/game")

if __name__ == "__main__":
    port = os.getenv('PORT')
    if port:
        app.run(host="0.0.0.0", port=port, protocol=WebSocketProtocol)
    else:
        app.run(host="0.0.0.0", port=8080, protocol=WebSocketProtocol)
    