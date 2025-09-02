import itertools


def generate_num_list(start, end, step=1.0):
    start = float(start)
    step = float(step)
    return [int(x) if x.is_integer() else x for x in [i * step for i in range(int(start / step), int(end / step) + 1)]]


def generate_num_combinations(range1, range2):
    """
    给定两个范围的整数，然后生成所有组合， 比如0-360， 0-100两个范围, 生成组合： [[0, 0], ..., [360, 10]]
    range1: (0, 360)
    range2: (0, 100)
    """
    # 定义范围
    range1 = range(range1[0], range1[1] + 1)  # 0 到 360，包括 360
    range2 = range(range2[0], range2[1] + 1)  # 0 到 100，包括 100
    # 生成所有组合
    combinations = list(itertools.product(range1, range2))
    # 将每个组合从 tuple 转换为 list
    combinations = [list(combo) for combo in combinations]
    return combinations


# 场景触发条件空间设备参数，用于生成场景触发条件数据
SCENE_TRIGGER_SPACE_PARAM = {
    'temperature': {'status': ['above', 'below'], 'value': list(range(-10, 56))},
    'humidity': {'status': ['above', 'below'], 'value': list(range(0, 101))},
    'energy': {'status': ['above', 'below'], 'value': list(range(1001)), 'energy_type': list(range(1, 5))},
    'motion': {'status': ['on', 'off'], 'value': ['any', 'all']},
    'light': {'status': ['on', 'off'], 'value': ['any', 'all']},
    'switch': {'status': ['on', 'off'], 'value': ['any', 'all']},
    'curtain': {'status': ['on', 'off'], 'value': ['any', 'all']},
    'door': {'status': ['on', 'off'], 'value': ['any', 'all']},
    'music': {'status': ['on', 'off'], 'value': ['any', 'all']},
    'siren': {'status': ['on', 'off'], 'value': ['any', 'all']},
    'occupancy': {'status_value': [['on', 'any'], ['off', 'all']]}
}

# 场景触发条件设备参数，用于生成场景触发条件数据
SCENE_TRIGGER_DEVICE_PARAM = {
    'battery_level': {'status': ['above', 'below'], 'value': list(range(0, 101))},
    'energy': {'status': ['above', 'below'], 'value': list(range(1, 1001)), 'energy_type': [1, 2, 3, 4]},
    'temperature': {'status': ['above', 'below'], 'value': generate_num_list(-10, 55, 0.5)},
    'humidity': {'status': ['above', 'below'], 'value': list(range(0, 101))},
    'illuminance': {'status': ['above', 'below'], 'value': list(range(0, 32001))},
    'carbon_dioxide': {'status': ['above', 'below'], 'value': list(range(0, 4001))},
    'pm25': {'status': ['above', 'below'], 'value': list(range(0, 1000))},
    'pm10': {'status': ['above', 'below'], 'value': list(range(0, 1000))},
    'pm1': {'status': ['above', 'below'], 'value': list(range(0, 1000))},
    'hcho': {'status': ['above', 'below'], 'value': list(range(0, 1001))},
    'tvoc': {'status': ['above', 'below'], 'value': list(range(0, 2001))},
    'current_temperature_changed': {'status': ['above', 'below'], 'value': generate_num_list(5, 35, 0.5)},
    'preset_temperature': {'status': ['above', 'below'], 'value': list(range(0, 101))},
    'hvac_mode_changed': {'status': ['to'], 'value': ["fan_only", "cool", "heat"]},
    'fan_mode_changed': {'status': ['to'], 'value': ["low", "medium", "high", "auto"]},
    'opened_for': {'for': {'hours': list(range(0, 23)), 'minutes': list(range(0, 59)), 'seconds': list(range(0, 59))}},
    'position': {'status': ['above', 'below'], 'value': list(range(0, 101))},
    'tilt_position': {'status': ['above', 'below'], 'value': list(range(0, 101))},
    'color_temp_changed': {'status': ['above', 'below'], 'value': list(range(0, 101))},
    'brightness_changed': {'status': ['above', 'below'], 'value': list(range(0, 101))}
}

# 场景判断条件设备参数，用于生成场景判断条件数据
SCENE_CONDITION_DEVICE_PARAM = {
    'is_battery_level': {'status': ['above', 'below'], 'value': list(range(0, 101))},
    'is_energy': {'status': ['above', 'below'], 'value': list(range(1, 1001)), 'energy_type': [1, 2, 3, 4]},
    'is_temperature': {'status': ['above', 'below'], 'value': generate_num_list(-10, 55, 0.5)},
    'is_humidity': {'status': ['above', 'below'], 'value': list(range(0, 101))},
    'is_illuminance': {'status': ['above', 'below'], 'value': list(range(0, 32001))},
    'is_carbon_dioxide': {'status': ['above', 'below'], 'value': list(range(0, 4001))},
    'is_pm25': {'status': ['above', 'below'], 'value': list(range(0, 1000))},
    'is_pm10': {'status': ['above', 'below'], 'value': list(range(0, 1000))},
    'is_pm1': {'status': ['above', 'below'], 'value': list(range(0, 1000))},
    'is_hcho': {'status': ['above', 'below'], 'value': list(range(0, 1001))},
    'is_tvoc': {'status': ['above', 'below'], 'value': list(range(0, 2001))},
    'is_preset_temperature': {'status': ['above', 'below'], 'value': list(range(5, 36))},
    'is_hvac_mode': {'status': ['hvac_mode'], 'value': ["fan_only", "cool", "heat"]},
    'is_fan_mode': {'status': ['fan_mode'], 'value': ["low", "medium", "high", "auto"]},
    'is_play_mode': {'status': ['play_mode'], 'value': [1, 2, 3]},
    'is_volume': {'status': ['above', 'below'], 'value': list(range(0, 101))},
    'is_position': {'status': ['above', 'below'], 'value': list(range(0, 101))},
    'is_tilt_position': {'status': ['above', 'below'], 'value': list(range(0, 101))},
    'is_color_temp': {'status': ['above', 'below'], 'value': list(range(0, 101))},
    'is_brightness': {'status': ['above', 'below'], 'value': list(range(0, 101))}
}

# 场景判断条件天气参数，用于生成场景判断条件数据
SCENE_CONDITION_WEATHER_PARAM = {
    'temperature': {'status': ['above', 'below'], 'value': list(range(-40, 41))},
    'humidity': {'status': ['above', 'below'], 'value': list(range(0, 101))},
    'aqi': {'status': ['above', 'below'], 'value': list(range(0, 501))},
}

# 场景判断条件空间设备参数，用于生成场景判断条件数据
SCENE_CONDITION_SPACE_MAP = {
    'temperature': {'status': ['above', 'below'], 'value': list(range(-10, 56))},
    'humidity': {'status': ['above', 'below'], 'value': list(range(0, 101))},
    'energy': {'status': ['above', 'below'], 'value': list(range(1001)), 'energy_type': list(range(1, 5))},
    'motion': {'status': ['on', 'off'], 'value': ['any', 'all']},
    'light': {'status': ['on', 'off'], 'value': ['any', 'all']},
    'switch': {'status': ['on', 'off'], 'value': ['any', 'all']},
    'curtain': {'status': ['on', 'off'], 'value': ['any', 'all']},
    'door': {'status': ['on', 'off'], 'value': ['any', 'all']},
    'music': {'status': ['on', 'off'], 'value': ['any', 'all']},
    'occupancy': {'status': ['on', 'off'], 'value': ['any', 'all']},
    'siren': {'status': ['on', 'off'], 'value': ['any', 'all']},
}

# 场景任务操作设备参数，用于生成场景任务数据
SCENE_ACTION_SPACE_MAP = {
    'light': {'action': ['on', 'off', 'brightness'], 'brightness:value': list(range(0, 101))},
    'switch': {'action': ['on', 'off']},
    'curtain': {'action': ['on', 'off']},
    'music': {'action': ['on', 'off']},
    'siren': {'action': ['on', 'off']},
    'multi_climate': {'action': ['on', 'off']},
}

# 场景Task设备动作参数，用于生成场景数据
SCENE_ACTION_DEVICE_PARAM = {
    'set_volume': {'volume_level': generate_num_list(0, 1, 0.01)},
    'play_mode_set': {'play_mode': [1, 2, 3]},
    'brightness': {'brightness_pct': generate_num_list(0, 100)},
    'hs_color': {'hs_color': generate_num_combinations((0, 360), (0, 100))},
    'color_temp': {'color_temp': list(range(153, 501))},
    'set_position': {'position': list(range(0, 101))},
    'set_tilt_position': {'position': list(range(0, 101))},
}

# 场景Task设备动作和状态对应关系，用于根据Task设备动作，生成场景执行后要检查的设备状态数据
SCENE_ACTION_DEVICE_STATE_MAP = {
    'turn_on': {'value': 'on'},
    'turn_off': {'value': 'off'},
    'temperature': {"feature": "target_temperature"},
    'brightness': {"feature": "brightness_pct"},
    'set_volume': {'feature': 'music_volume', 'value_key': 'volume_level'},
    'volume_mute': {'feature': 'music_volume', 'value': 0},
    'set_position': {'feature': 'cover_position', 'value_key': 'position'},
    'set_tilt_position': {'feature': 'cover_tilt', 'value_key': 'position'},
    'clear_playlist': {'feature': 'music_playlist', 'value': []},
    'play_mode_set': {'feature': 'music_play_mode', 'value_key': 'play_mode'},
}

# 场景任务空间操作设备类型对应关系，一般为space_control下的type值首字母转成大写即可，个别不一样的在此维护
SCENE_ACTION_SPACE_DEVICE_TYPE_MAP = {
    'multi_climate': 'Thermostat',
}

# 空间设备状态对应关系，场景任务设置设备状态为on或off时，有些设备的状态不是on/off
SCENE_ACTION_SPACE_DEVICE_STATE_MAP = {
    'music': {'on': 'play', 'off': 'idle'},
    'curtain': {'on': 'open', 'off': 'closed'},
}

# 场景设备触发类型和模拟器的操作类型对应关系
SCENE_DEVICE_SIMULATOR_TRIGGER_TYPE_MAP = {
    'co': {'action': {'trigger': 'on'}, 'reverse_action': {'trigger': 'off'}},
    'no_co': {'action': {'trigger': 'off'}, 'reverse_action': {'trigger': 'on'}},
    'unsafe': {'action': {'trigger': 'on'}, 'reverse_action': {'trigger': 'off'}},
    'not_unsafe': {'action': {'trigger': 'off'}, 'reverse_action': {'trigger': 'on'}},
    'opened': {'action': {'trigger': 'on'}, 'reverse_action': {'trigger': 'off'}},
    'not_opened': {'action': {'trigger': 'off'}, 'reverse_action': {'trigger': 'on'}},
    'moist': {'action': {'trigger': 'on'}, 'reverse_action': {'trigger': 'off'}},
    'not_moist': {'action': {'trigger': 'off'}, 'reverse_action': {'trigger': 'on'}},
    'gas': {'action': {'trigger': 'on'}, 'reverse_action': {'trigger': 'off'}},
    'no_gas': {'action': {'trigger': 'off'}, 'reverse_action': {'trigger': 'on'}},
    'unlocked': {'action': {'switch': 'unlocked'}, 'reverse_action': {'switch': 'locked'}},
    'locked': {'action': {'switch': 'locked'}, 'reverse_action': {'switch': 'unlocked'}},
    'turned_on': {'action': {'switch': 'on'}, 'reverse_action': {'switch': 'off'}},
    'turned_off': {'action': {'switch': 'off'}, 'reverse_action': {'switch': 'on'}},
    'opening': {'action': {'switch': 'open'}, 'reverse_action': {'switch': 'closed'}},
    'closing': {'action': {'switch': 'closed'}, 'reverse_action': {'switch': 'open'}}
}

# 场景设备触发类型和用户web接口操作对应关系，用于根据场景设备触发条件，生成要操作的用户web接口操作数据
SCENE_DEVICE_TRIGGER_ACTION_MAP = {
    # 'battery_level': {'status': ['above', 'below'], 'value': list(range(0, 101))},
    # 'energy': {'status': ['above', 'below'], 'value': list(range(1, 1001)), 'energy_type': [1, 2, 3, 4]},
    # 'temperature': {'status': ['above', 'below'], 'value': generate_num_list(-10, 55, 0.5)},
    # 'humidity': {'status': ['above', 'below'], 'value': list(range(0, 101))},
    # 'illuminance': {'status': ['above', 'below'], 'value': list(range(0, 32001))},
    # 'carbon_dioxide': {'status': ['above', 'below'], 'value': list(range(0, 4001))},
    # 'pm25': {'status': ['above', 'below'], 'value': list(range(0, 1000))},
    # 'pm10': {'status': ['above', 'below'], 'value': list(range(0, 1000))},
    # 'pm1': {'status': ['above', 'below'], 'value': list(range(0, 1000))},
    # 'hcho': {'status': ['above', 'below'], 'value': list(range(0, 1001))},
    # 'tvoc': {'status': ['above', 'below'], 'value': list(range(0, 2001))},
    # 'current_temperature_changed': {'status': ['above', 'below'], 'value': generate_num_list(5, 35, 0.5)},
    # 'preset_temperature': {'status': ['above', 'below'], 'value': list(range(0, 101))},
    # 'hvac_mode_changed': {'status': ['to'], 'value': ["fan_only", "cool", "heat"]},
    # 'fan_mode_changed': {'status': ['to'], 'value': ["low", "medium", "high", "auto"]},
    # 'opened_for': {'for': {'hours': list(range(0, 23)), 'minutes': list(range(0, 59)), 'seconds': list(range(0, 59))}},
    'color_temp_changed': {'feature': 'color_temp', 'service_type': 'turn_on', 'color_temp': list(range(153, 501))},
    'brightness_changed': {'feature': 'brightness_pct', 'service_type': 'turn_on', 'brightness_pct': list(range(0, 101))},
    'position': {'feature': 'cover_position', 'service_type': 'set_cover_position', 'position': list(range(0, 101))},
    'tilt_position': {'feature': 'cover_tilt', 'service_type': 'set_cover_tilt_position', 'tilt_position': list(range(0, 101))},
    'turned_on': {'service_type': 'turn_on', 'target_state': 'on', 'reverse_service_type': 'turn_off', 'reverse_target_state': 'off'},
    'turned_off': {'service_type': 'turn_off', 'target_state': 'off', 'reverse_service_type': 'turn_on', 'reverse_target_state': 'on'},
    'opening': {'service_type': 'open_cover', 'target_state': 'open', 'reverse_service_type': 'close_cover', 'reverse_target_state': 'closed'},
    'closing': {'service_type': 'close_cover', 'target_state': 'closed', 'reverse_service_type': 'open_cover', 'reverse_target_state': 'open'},
    'locked': {'service_type': 'lock', 'target_state': 'locked', 'reverse_service_type': 'unlock', 'reverse_target_state': 'unlocked'},
    'unlocked': {'service_type': 'unlock', 'target_state': 'unlocked', 'reverse_service_type': 'lock', 'reverse_target_state': 'locked'},
}

# 场景设备触发类型和用户web接口操作对应关系 - changed_states，key为当前状态值
SCENE_DEVICE_TRIGGER_CHANGED_STATES_ACTION_MAP = {
    'locked': {'service_type': 'unlock', 'target_state': 'unlocked'},
    'unlocked': {'service_type': 'lock', 'target_state': 'locked'},
    'open': {'service_type': 'close_cover', 'target_state': 'closed'},
    'closed': {'service_type': 'open_cover', 'target_state': 'open'},
    'on': {'service_type': 'turn_off', 'target_state': 'off'},
    'off': {'service_type': 'turn_on', 'target_state': 'on'},
}

# 场景TASK设备Action类型和用户web接口反转状态操作对应关系，key为action - type
SCENE_TASK_DEVICE_ACTION_MAP = {
    'set_volume': {'volume_level': generate_num_list(0, 1, 0.01)},
    'play_mode_set': {'play_mode': [1, 2, 3]},
    'brightness': {'feature': 'brightness_pct', 'reverse_service_type': 'turn_on', 'brightness_pct': generate_num_list(0, 100)},
    'hs_color': {'feature': 'hs_color', 'reverse_service_type': 'turn_on', 'hs_color': generate_num_combinations((0, 360), (0, 100))},
    'color_temp': {'feature': 'color_temp', 'reverse_service_type': 'turn_on', 'color_temp': list(range(153, 501))},
    'set_position': {'feature': 'cover_position', 'reverse_service_type': 'set_cover_position', 'position': list(range(0, 101))},
    'set_tilt_position': {'feature': 'cover_tilt', 'reverse_service_type': 'set_cover_tilt_position', 'tilt_position': list(range(0, 101))},
    'turn_on': {'target_state': 'on', 'reverse_service_type': 'turn_off', 'reverse_target_state': 'off'},
    'turn_off': {'target_state': 'off', 'reverse_service_type': 'turn_on', 'reverse_target_state': 'on'},
    'open': {'target_state': 'open', 'reverse_service_type': 'close_cover', 'reverse_target_state': 'closed'},
    'close': {'target_state': 'closed', 'reverse_service_type': 'open_cover', 'reverse_target_state': 'open'},
    'lock': {'target_state': 'locked', 'reverse_service_type': 'unlock', 'reverse_target_state': 'unlocked'},
    'unlock': {'target_state': 'unlocked', 'reverse_service_type': 'lock', 'reverse_target_state': 'locked'},
}

# 场景TASK设备Action类型和用户web接口反转状态操作对应关系 - toggle，key为当前状态值
SCENE_TASK_DEVICE_TOGGLE_ACTION_MAP = {
    'off': {'target_state': 'on'},
    'on': {'target_state': 'off'},
    'open': {'target_state': 'closed'},
    'closed': {'target_state': 'open'},
    'locked': {'target_state': 'unlocked'},
    'unlocked': {'target_state': 'locked'}
}

# 排除的场景触发类型
SCENE_EXCLUDE_TRIGGER_TYPE = [
    'energy'
]

# 排除的设备操作Feature类型
EXCLUDE_FEATURES = [
    'cover_support_stop',
    'cover_full_on_pos',
    'cover_not_support_tilt_value'
]

CLOUD_PUBLIC_KEY = ("-----BEGIN PUBLIC KEY-----\nMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAt6fdPXHeOWxvceewPSZ4ChKrI"
                    "ouXzDObYKZYAAKHaTWpo8y5+TRFnPadsonuL5yQFyI4oQFqQ6Qxni972pnSXw/sRhfDl5mwC8EEAGtxxTqFYUMEiLCtbFbeyr"
                    "xO2um0rLFFwrfrZXNJXMVSyn+Y8hLgk3UnbwtrutTmmbKwL6cQzq3/RVdvbLmPCn9vwN0gAAePOFhbFRcLcNaTwVI3R6nzOXI"
                    "RjOff52eJzFmumT3Tp96owpgXkgdzKDF6mIxHvulDUTokD0vvHoJlRPErXZdG4o9tM5eI4r/73lybTaTqKfxpbfIEFqD4bCzP"
                    "5t+H+5bi/iFWtUrWbV3AvmamzQIDAQAB\n-----END PUBLIC KEY-----")
