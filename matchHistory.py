from pantheon import pantheon
import asyncio
import pandas as pd
import time
import telegram
from collections import deque
from copy import deepcopy

server = "kr"
api_key = "---your_api_key---"
lastSendGameId = deque([0, 0, 0, 0, 0])
playingGameId = 0
multiKillString = {0:'', 1:'', 2:'Multi Kill', 3: 'Triple Kill', 4:'Quadra Kill', 5:'Penta Kill'}
LOLALARMCHANNEL = "---your_telegram_key---"
bot = telegram.Bot(token='---your_telegram_tokken---')

def myqueue(newGameId):
  lastSendGameId.appendleft(newGameId)
  lastSendGameId.pop()

def requestsLog(url, status, headers):
  #print(url)
  print(status)
  #print(headers)

async def test_match(matchId):
  try:
    data = loop.run_until_complete(panth.getMatch(matchId))
  except Exception as e:
    print(e)
  
  assert data["gameId"] == matchId
  assert "participants" in data

async def getSummonerId(name):
  try:
    data = await panth.getSummonerByName(name)
    return (data['id'],data['accountId'])
  except Exception as e:
    print(e)

def getLastMatchInfo(accountId):
  global lastSendGameId
  try:
    data = loop.run_until_complete(panth.getMatchlist(accountId, params={"endIndex":10}))
    latestGameId = (data['matches'][0]['gameId'])
    print(lastSendGameId, latestGameId)
    if latestGameId in lastSendGameId:
      return
    else:
      print("new match detected")
      matchInfoSend(accountId, latestGameId)
      return True, data
  except Exception as e:
    print(e)

def matchInfoSend(accountId, latestGameId):
  try:
    data = loop.run_until_complete(panth.getMatch(latestGameId))
  except Exception as e:
    print(e)
    return

  myqueue(latestGameId)
  
  for eachParticipant in data['participantIdentities']:
    eachParticipantName = eachParticipant['player']['summonerName']
    eachParticipantId = eachParticipant['participantId']
    if eachParticipantName == name:
      break

  teamKills = 0
  if eachParticipantId <= 5:
    for i in range(5):
      teamKills += data['participants'][i]['stats']['kills']
  else:
    for i in range(5, 10):
      teamKills += data['participants'][i]['stats']['kills']

  myInfo = data['participants'][eachParticipantId-1]

  myInfoData = {}
  
  myInfoData['killInvolve'] = str(int((myInfo['stats']['kills'] + myInfo['stats']['assists'])/teamKills * 100))
  myInfoData['time'] = '{}분 {}초'.format(data['gameDuration'] // 60, data['gameDuration'] % 60) 
  myInfoData['champion'] = myInfo['championId']
  myInfoData['kda'] = '{}/{}/{}'.format(myInfo['stats']['kills'], myInfo['stats']['deaths'], myInfo['stats']['assists'])
  if myInfo['stats']['deaths'] == 0:
    ratio = 'Perfect'
  else:
    ratio = str(round((myInfo['stats']['kills'] + myInfo['stats']['assists']) / myInfo['stats']['deaths'], 2))
  myInfoData['ratio'] = ratio
  myInfoData['win'] = '🎖승리🎖' if myInfo['stats']['win'] else '😪패배😪'
  myInfoData['MultiKill'] = multiKillString[myInfo['stats']['largestMultiKill']] if myInfo['stats']['largestMultiKill'] >= 2 else None
  myInfoData['lane'] = myInfo['timeline']['lane']
  myInfoData['totalDamage'] = myInfo['stats']['totalDamageDealtToChampions']
  myInfoData['totalGold'] = myInfo['stats']['goldEarned']

  timeline = []
  timeline.append(sorted(list(myInfo['timeline']['goldPerMinDeltas'].items())))
  timeline.append(sorted(list(myInfo['timeline']['creepsPerMinDeltas'].items())))
  timeline.append(sorted(list(myInfo['timeline']['xpPerMinDeltas'].items())))

  myInfoData['TimeLineColumn'] = ' ' * 7
  myInfoData['goldTimeLine'] = 'Gold'
  myInfoData['csTimeLine'] = '  CS'
  myInfoData['expTimeLine'] = ' EXP'
  
  for goldTuple in timeline[0]:
    myInfoData['TimeLineColumn'] += '%10s' % goldTuple[0]
    gold = round(goldTuple[1], 2)
    myInfoData['goldTimeLine'] += '%10s' % str(gold)
  
  for csTuple in timeline[1]:
    cs = round(csTuple[1], 2)
    myInfoData['csTimeLine'] += '%10s' % str(cs)

  for xpTuple in timeline[2]:
    xp = round(xpTuple[1], 2)
    myInfoData['expTimeLine'] += '%10s' % str(xp)
  
  message = '⚔Match Analysis⚔\n\n'
  message += myInfoData['win'] + '\n'
  message += name + '\n'
  message += myInfoData['time'] + ' 킬관여' + myInfoData['killInvolve'] +'%\n'
  message += '{} {}\n'.format(myInfoData['champion'], myInfoData['lane'])
  message += '{} {}:1 평점\n'.format(myInfoData['kda'], myInfoData['ratio'])
  if myInfoData['MultiKill'] is not None:
    message += '{}\n'.format(myInfoData['MultiKill'])
  message += myInfoData['TimeLineColumn'] + '\n'
  message += myInfoData['goldTimeLine'] + '\n'
  message += myInfoData['expTimeLine'] + '\n'
  message += myInfoData['csTimeLine']

  bot.sendMessage(LOLALARMCHANNEL, message)
  time.sleep(10)


name = "zxcx"
if __name__ == '__main__':

  panth = pantheon.Pantheon(server, api_key, errorHandling=True, requestsLoggingFunction=requestsLog, debug=True)
  loop = asyncio.get_event_loop()  
  summonerId, accountId = loop.run_until_complete(getSummonerId(name))

  while True:
    getLastMatchInfo(accountId)
    
    