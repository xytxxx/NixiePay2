from re import sub
from typing import Dict, List, Set, Tuple
from collections import defaultdict
import kanboard
import json
import sys
import re
from googleSheet import Sheet

secret = {}
with open('credentials.json') as f:
    secret = json.load(f)
sheet = Sheet()

PROJECT_ID = '1' 

# read boards
kb = kanboard.Client("https://kb.nixiesubs.xyz/jsonrpc.php", secret['kanboard']['username'], secret['kanboard']['api'])
# ltt, tq, sc = kb.getBoard(project_id=PROJECT_ID)
# if ltt['name'] != 'LTT' or tq['name'] != 'TQ' or sc['name'] != 'SC':
#     print("Boards should be strictly in order: LTT, TQ, SC")
#     exit(1)
class Video:
    def __init__(self, **kwargs):
        self.title = kwargs.get('title')
        self.segments = kwargs.get('segments')
        self.totalTime = kwargs.get('totalTime') 

def getChannelIds() -> Dict[str, str]:
    allChannels = kb.getAllSwimlanes(project_id=PROJECT_ID)
    channelIdToTitle = {}
    for channel in allChannels:
        channelIdToTitle[channel['id']] = channel['name']
    return channelIdToTitle

def getCNYUserIds() -> Set[str]:
    cnyTask = kb.searchTasks(project_id=PROJECT_ID, query='title:CNY')
    if len(cnyTask) != 1:
        print("Cannot find CNY task or found multiple CNY tasks")
        exit(1)
    cnySubtasks = kb.getAllSubtasks(task_id=int(cnyTask[0]['id']))
    return set(map(lambda subtask: subtask['user_id'], cnySubtasks))

def parseVideoDescription(task: Dict) -> Tuple[List[int], int]:
    try: 
        allTimes = re.findall(r'\d{1,2}:\d{1,2}', task['description'])
        if len(allTimes) % 2 == 0 and len(allTimes) >= 2:
            segments = []
            totalTime = 0
            for i in range(0, len(allTimes), 2):
                min = int(allTimes[i+1][:2]) - int(allTimes[i][:2])
                sec = int(allTimes[i+1][3:]) - int(allTimes[i][3:])
                time = min * 60 + sec
                if time <= 0:
                    print("Segments has negative duration: {}".format(task['title']))
                    exit(1)
                segments.append(time)
                totalTime += time
            return segments, totalTime
        else:
            print("Error parsing descrition of: {}".format(task['title']))
            exit(1)
    except ValueError:
        print("Error parsing descrition of: {}".format(task['title']))
        exit(1)

def getAllCompletedVideos(columnNamesToPay: List[str]) -> Dict[str, Video]:
    channelIdToTitle = getChannelIds()
    allTasks = kb.getAllTasks(project_id=PROJECT_ID)
    allColumns = kb.getColumns(project_id=PROJECT_ID)
    columnIdsToPay = []
    for column in allColumns:
        for title in columnNamesToPay:
            if title in column['title']:
                columnIdsToPay.append(column['id'])
    allVideos = {}
    for task in allTasks:
        if task['column_id'] in columnIdsToPay:
            segments, totalTime = parseVideoDescription(task)
            allVideos[task['id']] = Video(
                title='{channel}:{title}'.format(
                    channel=channelIdToTitle[task['swimlane_id']], 
                    title=task['title']
                ),
                segments=segments,
                totalTime=totalTime,
            )
    return allVideos

def getWorkDoneForEachUser(videos: Dict[str, Video]) -> Dict[str, Dict]:
    usersToWork = defaultdict(lambda: {'D': [], 'P': [], 'S': []}) 
    for taskId, video in videos.items():
        subtasks = kb.getAllSubtasks(task_id=taskId)
        subtasks = sorted(subtasks, key=lambda subtask: int(subtask['position']))
        numD = 0
        numP = 0
        numS = 0
        D = []
        P = []
        S = []
        for subtask in subtasks:
            if subtask['title'].strip() == 'D':
                numD += 1
                D.append(subtask)
            elif subtask['title'].strip() == 'P':
                numP += 1
                P.append(subtask)
            elif subtask['title'].strip() == 'S':
                numS += 1
                S.append(subtask)
            else:
                print('There are subtasks other than D, P, S in {}'.format(video.title))
        if (numD != len(video.segments) and numD != 1) or \
           (numP != len(video.segments) and numP != 1) or \
           (numS != len(video.segments) and numS != 1):
            print('Number of subtasks does not match with segments: {}'.format(video.title))
            exit(1)
        for numOfSubtaskType, subtaskType, subtasks in [
            (numD, 'D', D), (numP, 'P', P), (numS, 'S', S)
        ]:
            for i in range(numOfSubtaskType):
                time = video.segments[i]
                subtask = subtasks[i]
                if subtask['user_id'] in ('0', '236', '22'):
                    subtask['name'] = '无人认领（无校对）'
                    subtask['user_id'] = '_'
                if not subtask.get('user_id'):
                    print('There are segments without assignee: {}'.format(video.title))
                usersToWork[subtask['user_id']][subtaskType].append({
                    'taskId': taskId,
                    'time': time if numOfSubtaskType != 1 else video.totalTime
                })
                usersToWork[subtask['user_id']]['name'] = subtask['name']
    return usersToWork

def getUsers() -> Dict[str, Dict]:
    allUsers = kb.getAllUsers()
    usersById = {}
    for user in allUsers:
        usersById[user['id']] = user
    return usersById

def writeVideosToSheet(videos: Dict[str, Video])

def main():
    columnTitlesToPay = sys.argv[1:]
    cnyUserIds = getCNYUserIds()
    videos = getAllCompletedVideos(columnTitlesToPay)
    userIdsToWork = getWorkDoneForEachUser(videos)
    usersById = getUsers()



    with open('cny.json', 'w+') as f:
        json.dump(list(cnyUserIds), f)
    with open('videos.json', 'w+') as f:
        json.dump(videos, f)
    with open('work.json', 'w+') as f:
        json.dump(dict(userIdsToWork), f)
    with open('users.json', 'w+') as f:
        json.dump(usersById, f)
    

if __name__ == '__main__':
    main()