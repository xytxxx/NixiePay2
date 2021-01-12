from re import sub
from sys import setrecursionlimit
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
st = Sheet()

PROJECT_ID = '1' 
NO_PROOFREAD_USER_IDS= ('0', '236', '22')
JOB_TYPE_TO_RATE = {
    'D': 'I3',
    'DD': 'I4',
    'P': 'I5',
    'S': 'I6',
}
STARTING_ROW = 1
CNY_PAYMENT_CELLS = 'D2:E'
USD_PAYMENT_CELLS = 'F2:G'
VIDEO_CELLS = 'A2:B'

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

def secondsToTime(seconds):
    return '{hour}:{minute}:{sec}'.format(
        hour=str((seconds//3600)).zfill(2),
        minute=str(((seconds%3600)//60)).zfill(2), 
        sec=str((seconds%60)).zfill(2)
    )

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
                createdAt=int(task['date_creation'])
            )
    return allVideos

def getWorkDoneForEachUser(videos: Dict[str, Video]) -> Dict[str, Dict]:
    usersToWork = defaultdict(lambda: {'D': [], 'P': [], 'S': [], 'DD':[]}) 
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
            if subtask['title'].strip().startswith('D'):
                numD += 1
                D.append(subtask)
            elif subtask['title'].strip().startswith('P'):
                numP += 1
                P.append(subtask)
            elif subtask['title'].strip().startswith('S'):
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
                time = video.segments[i] if numD != 1 else sum(video.segments)
                subtask = subtasks[i]
                if subtask['user_id'] in NO_PROOFREAD_USER_IDS:
                    subtask['name'] = '无人认领（无校对'
                    subtask['user_id'] = '_'
                if not subtask.get('user_id'):
                    print('There are segments without assignee: {}'.format(video.title))
                # change to no-proof read if it should
                if subtaskType == 'D':
                    correspondingP = P[i] if numP == numD else P[0]
                    if correspondingP['user_id'] in NO_PROOFREAD_USER_IDS:
                        subtaskType = 'DD'
                usersToWork[subtask['user_id']][subtaskType].append({
                    'taskId': taskId,
                    'time': time if numOfSubtaskType != 1 else video.totalTime
                })
    return usersToWork

def getUsers() -> Dict[str, Dict]:
    allUsers = kb.getAllUsers()
    usersById = {}
    for user in allUsers:
        usersById[user['id']] = user
    return usersById

def writeVideosToSheet(sheet, videos: Dict[str, Video]):
    range = VIDEO_CELLS + str(len(videos)+STARTING_ROW)
    rows = []
    for taskId, video in videos.items():
        urlForVideo = 'https://kb.nixiesubs.xyz/?controller=TaskViewController&action=show&task_id={id}&project_id={p_id}'.format(id=taskId, p_id=PROJECT_ID)
        rows.append([
            '=HYPERLINK("{}","{}")'.format(urlForVideo, video.title.replace('"', '')),
            secondsToTime(video.totalTime)
        ])
    st.writeValues(sheet, range, rows)

def writePaymentsToSheet(sheet, videos, userIdsToWork, usersById, cnyUserIds):
    def getPaymentFormulaAndNotesForUserId(id):
        worksDone = userIdsToWork[id]
        formulas = []
        notes = ''
        jobTypeToWords = {
            'D': '你翻译了',
            'DD': '你翻译了(无校对)',
            'P': '你校对了',
            'S': '你打了轴',
        }
        for jobType in ('D', 'DD', 'P', 'S'):
            notes += jobTypeToWords[jobType] + '\n'
            totalTime = 0    
            for job in worksDone.get(jobType):
                title = videos.get(job['taskId']).title
                notes += '{title}, {time}\n'.format(title=title, time=secondsToTime(job['time']))
                totalTime += job['time']
            notes += '总计: ' + secondsToTime(totalTime) + '\n===========================\n'
            formulas.append('({rate} * {timeInMinutes})'.format(
                rate=JOB_TYPE_TO_RATE[jobType],
                timeInMinutes = round(totalTime / 60, 2)
            ))
        return '= ' + ' + '.join(formulas), notes

    def helper(rangeStartsAt, userIds):
        range = rangeStartsAt + str(len(userIds) + STARTING_ROW)
        rows = []
        notes = []
        for userId in userIds:
            formula, note = getPaymentFormulaAndNotesForUserId(userId)
            userName = usersById[userId]['name'] if userId != '_' else '无人认领（无校对'
            if userName == '':
                userName = usersById[userId]['username']
            rows.append([userName, formula]) 
            notes.append(['', note])
        st.writeValues(sheet, range, rows)
        st.writeNotes(sheet, range, notes)
    usdUserIds = set(userIdsToWork.keys()) - cnyUserIds
    cnyUserIds = cnyUserIds.intersection(userIdsToWork.keys())
    helper(CNY_PAYMENT_CELLS, cnyUserIds)
    helper(USD_PAYMENT_CELLS, usdUserIds)

def main():
    columnTitlesToPay = sys.argv[1:]
    print('getting user ids')
    cnyUserIds = getCNYUserIds()
    print('getting videos')
    videos = getAllCompletedVideos(columnTitlesToPay)
    print('calculating')
    userIdsToWork = getWorkDoneForEachUser(videos)
    usersById = getUsers()
    print('creating sheets')
    sheet = st.createNewSheetFromTemplate('LMGNS'+','.join(columnTitlesToPay))
    print('writing to sheet')
    writeVideosToSheet(sheet, videos)
    writePaymentsToSheet(sheet, videos, userIdsToWork, usersById, cnyUserIds)

if __name__ == '__main__':
    main()