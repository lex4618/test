
STATE_MAP = {
    'on': True,
    'off': False,
    True: 'on',
    False: 'off'
}

"""
锁状态和门口机input对应关系，跟插簧开关的接线有关，在上锁状态下，通过API获取门口机的input状态:http://192.168.88.105/api/input/status，
如果input状态=1，那么需要修改LOCK_STATE_INPUT_MAP中的Locked=1，Unlocked=0，反之设置Locked=0，Unlocked=1
{
    "retcode": 0,
    "action": "status",
    "message": "OK",
    "data": {
        "InputA": 1,
        "InputB": 1,
        "InputC": 1
    }
}
"""
LOCK_STATE_INPUT_MAP = {'Unlocked': 0, 'Locked': 1}
