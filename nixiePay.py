import kanboard
import json

secret = {}
with open('credentials.json') as f:
    secret = json.load(f)

PROJECT_ID = '1' 

# read boards
kb = kanboard.Client("https://kb.nixiesubs.xyz/jsonrpc.php", secret['kanboard']['username'], secret['kanboard']['api'])
# ltt, tq, sc = kb.getBoard(project_id=PROJECT_ID)
# if ltt['name'] != 'LTT' or tq['name'] != 'TQ' or sc['name'] != 'SC':
#     print("Boards should be strictly in order: LTT, TQ, SC")
#     exit(1)

def getCNYList():
    cnyTask = kb.searchTasks(project_id=PROJECT_ID, query='title:CNY')
    if len(cnyTask) != 1:
        print("Cannot find CNY task or found multiple CNY tasks")
        exit(1)
    cnySubtasks = kb.getAllSubtasks(task_id=int(cnyTask[0]['id']))
    return set(map(lambda subtask: subtask['username'], cnySubtasks))

cnyUsernames = getCNYList()
print('done')