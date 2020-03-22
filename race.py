#! /usr/bin/env python3

import json
import os
import requests
from datetime import datetime
import time

def getTournamentData(tournamentcode):
    tournpath = f'{tournamentcode}.json'
    if os.path.exists(tournpath):
        with open(tournpath, 'r') as f:
            gamelist = json.load(f)
        return gamelist
    else:
        headers = {'Accept': 'application/x-ndjson', 'Content-Type': 'application/x-ndjson'}
        if os.path.exists('token'):
            with open('token', 'r') as f:
                tokendata = f.read()[:-2]
            headers['Authorization'] = f'Bearer {tokendata}'
        r = requests.get(f'https://lichess.org/api/tournament/{tournamentcode}/games', headers=headers)
        gamelist = r.text.split('\n')[:-1]
        with open(tournpath, 'w') as f:
            json.dump(gamelist, f)
        return gamelist

def getTournamentTimes(tournamentcode):
    r = requests.get(f'https://lichess.org/api/tournament/{tournamentcode}').json()
    start = int(time.mktime(time.strptime(r['startsAt'], '%Y-%m-%dT%H:%M:%S.000Z')))*1000
    duration = r['minutes']
    end = start + (duration * 60 * 1000) + 1
    return start, end

#start with JSON
#generate list for each player with (game end time, result, berserk)
#convert to player: (time, points) for graphing

def generateRaceData(gamelist):
    players = {}

    def appendOrCreate(player, gamedata):
        if players.get(player):
            players[player].append(gamedata)
        else:
            players[player] = [gamedata]

    def getResult(game):
        winner = game.get('winner')
        if winner:
            if winner == 'white':
                return {'white': 'w', 'black': 'l'}
            if winner == 'black':
                return {'white': 'l', 'black': 'w'}
        return {'white': 'd', 'black': 'd'}

    def getBerserk(game):
        if len(game['moves'].split()) < 14: #at least 7 moves must be played by each player for berserk points to count
            return {'white': False, 'black': False}
        white = game['players']['white'].get('berserk')
        black = game['players']['black'].get('berserk')
        return {'white': white, 'black': black}

    def scoreConvert(results):
        chronoresults = sorted(results, key=lambda results: results['time'])
        scores = []
        score = 0
        streak = 0
        for game in chronoresults:
            if game['result'] == 'w':
                score += 2
                if streak >= 2:
                    score += 2
                if game['berserk']:
                    score += 1
                scores.append((game['time'], score))
                streak += 1
            elif game['result'] == 'd':
                if streak >= 2:
                    score += 2
                else:
                    score += 1
                scores.append((game['time'], score))
                streak = 0
            elif game['result'] == 'l':
                scores.append((game['time'], score))
                streak = 0
        return scores

    for g in gamelist:
        game = json.loads(g)
        result = getResult(game)
        berserk = getBerserk(game)
        appendOrCreate(game['players']['white']['user']['title'] + " " + game['players']['white']['user']['name'], {'time': game['lastMoveAt'], 'result': result['white'], 'berserk': berserk['white']})
        appendOrCreate(game['players']['black']['user']['title'] + " " + game['players']['black']['user']['name'], {'time': game['lastMoveAt'], 'result': result['black'], 'berserk': berserk['black']})

    graphdata = {}

    for player, results in players.items():
        graphdata[player] = scoreConvert(results)

    return graphdata
