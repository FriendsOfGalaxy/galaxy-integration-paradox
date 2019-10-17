import sys
if sys.platform == 'win32':
    import winreg

import os
import logging as log
import asyncio
from consts import REGISTRY_LAUNCHER_PATH, PARADOX_LAUNCHER_EXE
from dataclasses import dataclass
from galaxy.proc_tools import process_iter, ProcessInfo

@dataclass
class RunningGame:
    name: str
    process: ProcessInfo


class LocalClient(object):
    def __init__(self):
        self._local_client_path = None
        self._local_client_exe = None
        self._local_games_path = None


    @property
    def installed(self):
        if self._local_client_exe and os.access(self._local_client_exe, os.F_OK):
            return True
        else:
            self.refresh_local_client_state()
            return self._local_client_exe and os.access(self._local_client_exe, os.F_OK)

    @property
    def local_client_exe(self):
        if self.installed:
            return self._local_client_exe

    @property
    def local_client_path(self):
        if self.installed:
            return self._local_client_path

    @property
    def bootstraper_exe(self):
        if self.installed:
            paradox_root = self._local_client_path[:-len('\\launcher')]
            bootstrapper = os.path.join(paradox_root, 'bootstrapper')
            return os.path.join(bootstrapper,'Bootstrapper.exe')

    @property
    def games_path(self):
        if self.installed:
            if self._local_games_path:
                return self._local_games_path
            else:
                paradox_root = self._local_client_path[:-len('\\launcher')]
                paradox_games = os.path.join(paradox_root, 'games')
                if not os.access(paradox_games, os.F_OK):
                    return None
                self._local_games_path = paradox_games
                return paradox_games

    def refresh_local_client_state(self):
        if sys.platform == 'win32':
            try:
                with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,REGISTRY_LAUNCHER_PATH, 0, winreg.KEY_READ) as key:
                    local_client_path = winreg.QueryValueEx(key, "Path")[0]
                    local_client_exe = os.path.join(local_client_path, PARADOX_LAUNCHER_EXE)
                    self._local_client_path = local_client_path
                    self._local_client_exe = local_client_exe
            except OSError:
                self._local_client_exe = self._local_client_path = self._local_games_path = None

    async def get_running_game(self, games, proc_iter_interval=0.05):
        if not games:
            return
        for process_info in process_iter():
            try:
                await asyncio.sleep(proc_iter_interval)
                for game in games:
                    if process_info.binary_path.lower() == games[game].lower():
                        log.info(f"Found a running game! {game}")
                        return RunningGame(name=game, process=process_info)
            except:
                continue
