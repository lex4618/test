# -*- coding: utf-8 -*-

from libconfig.ACCESSDOOR.NORMAL.libconfig_ACCESSDOOR_NORMAL import config_ACCESSDOOR_NORMAL


class config_E16V3_NORMAL(config_ACCESSDOOR_NORMAL):

    def __init__(self, device_name=''):
        super().__init__(device_name)
        # Autop配置文件相关
        self._rename_cfg_file = 'E16V3reset.cfg'
        self._autop_cfg_file = 'r000000000216.cfg'
        self._old_firmware_file = 'E16V3.rom'
        self._firmware_ext = '.rom'
        self._model_name = 'E16V3'
        self._model_id_NORMAL = '316'
        self._oem = 'NORMAL'
        self._remote_connect_type = 'ssh'
        self._tln_ssh_port_list = 22

        # 福州软件部-Bruin-刘文雄 8/4 16:13:41
        # 16的没有va进程
        # 是挂载phone上面的
        self.check_ps_list = [
            '/app/bin/dclient',
            '/app/bin/phone',
            '/app/bin/video.fcgi'
        ]
