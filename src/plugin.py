import logging as log
import sys

from galaxy.api.plugin import Plugin, create_and_run_plugin
from galaxy.api.consts import Platform, OSCompatibility
from galaxy.api.types import NextStep, Authentication, Game, LicenseInfo, LicenseType, LocalGame, LocalGameState
from version import __version__

from backend import ParadoxClient
from http_client import AuthenticatedHttpClient
from consts import AUTH_PARAMS, System, SYSTEM

import pickle
import asyncio
import os
import json
import subprocess
import webbrowser

from typing import Any, List, Optional
from local import LocalClient


class ParadoxPlugin(Plugin):
    def __init__(self, reader, writer, token):
        super().__init__(Platform.ParadoxPlaza, __version__, reader, writer, token)
        self._http_client = AuthenticatedHttpClient(self.store_credentials)
        self.paradox_client = ParadoxClient(self._http_client)
        self.local_client = LocalClient()
        self.owned_games_cache = None

        self.local_games_cache = {}
        self.running_game = None

        self.tick_counter = 0

        self.local_games_called = None
        self.owned_games_called = None

        self.update_installed_games_task = None
        self.update_running_games_task = None
        self.update_owned_games_task = None



    async def authenticate(self, stored_credentials=None):
        if stored_credentials:
            stored_cookies = pickle.loads(bytes.fromhex(stored_credentials['cookie_jar']))
            self._http_client.authenticate_with_cookies(stored_cookies)
            self._http_client.set_auth_lost_callback(self.lost_authentication)
            acc_id = await self.paradox_client.get_account_id()
            return Authentication(str(acc_id), 'Paradox')
        if not stored_credentials:
            return NextStep("web_session", AUTH_PARAMS)

    async def pass_login_credentials(self, step, credentials, cookies):
        self._http_client.authenticate_with_cookies(cookies)
        self._http_client.set_auth_lost_callback(self.lost_authentication)
        acc_id = await self.paradox_client.get_account_id()
        return Authentication(str(acc_id), 'Paradox')

    async def get_owned_games(self):
        games_to_send = []
        try:
            owned_games = await self.paradox_client.get_owned_games()
            sent_titles = set()
            for game in owned_games:
                log.info(game)
                if 'game' in game['type']:
                    title = game['title'].replace(' (Paradox)', '')
                    title = title.split(':')[0]
                    if title in sent_titles:
                        continue
                    sent_titles.add(title)
                    games_to_send.append(Game(title.lower().replace(' ', '_'), title, None, LicenseInfo(LicenseType.SinglePurchase)))
            self.owned_games_cache = games_to_send
            self.owned_games_called = True
        except Exception as e:
            log.error(f"Encountered exception while retriving owned games {repr(e)}")
            self.owned_games_called = True
            raise e
        return games_to_send

    if SYSTEM == System.WINDOWS:
        async def get_local_games(self):
            games_path = self.local_client.games_path
            if not games_path:
                self.local_games_called = True
                return []
            local_games = os.listdir(games_path)

            games_to_send = []
            local_games_cache = {}
            for local_game in local_games:
                game_folder = os.path.join(games_path, local_game)
                game_cpatch = os.path.join(game_folder, '.cpatch', local_game)
                try:
                    with open(os.path.join(game_cpatch, 'version'))as game_cp:
                        version = game_cp.readline()
                    with open(os.path.join(game_cpatch, 'repository.json'), 'r') as js:
                        game_repository = json.load(js)
                    exe_path = game_repository['content']['versions'][version]['exePath']
                except FileNotFoundError:
                    continue
                except Exception as e:
                    log.error(f"Unable to parse local game {local_game} {repr(e)}")
                    continue

                local_games_cache[local_game] = os.path.join(game_folder, exe_path)
                games_to_send.append(LocalGame(local_game, LocalGameState.Installed))
            self.local_games_cache = local_games_cache
            self.local_games_called = True
            return games_to_send

    if SYSTEM == System.WINDOWS:
        async def launch_game(self, game_id):
            exe_path = self.local_games_cache.get(game_id)
            log.info(f"Launching {exe_path}")
            game_dir = os.path.join(self.local_client.games_path, game_id)
            subprocess.Popen(exe_path,cwd=game_dir)

    if SYSTEM == System.WINDOWS:
        async def install_game(self, game_id):
            bootstraper_exe = self.local_client.bootstraper_exe
            if bootstraper_exe:
                subprocess.Popen(bootstraper_exe)
                return
            log.info("Local client not installed")
            webbrowser.open('https://play.paradoxplaza.com')

    if SYSTEM == System.WINDOWS:
        async def uninstall_game(self, game_id):
            bootstraper_exe = self.local_client.bootstraper_exe
            if bootstraper_exe:
                subprocess.call(bootstraper_exe)
                return
            log.info("Local client not installed")
            webbrowser.open('https://play.paradoxplaza.com')

    async def update_installed_games(self):
        games_path = self.local_client.games_path
        if not games_path:
            return []
        local_games = os.listdir(games_path)
        local_games_cache = self.local_games_cache

        if len(local_games_cache) == len(local_games):
            return
        log.info("Number of local games changed, reparsing")
        await self.get_local_games()
        for game in local_games_cache:
            if not self.local_games_cache.get(game):
                self.update_local_game_status(LocalGame(game, LocalGameState.None_))
        for game in self.local_games_cache:
            if not local_games_cache.get(game):
                self.update_local_game_status(LocalGame(game, LocalGameState.Installed))

    async def update_running_games(self):
        await asyncio.sleep(1)
        local_games_cache = self.local_games_cache

        running_game = await self.local_client.get_running_game(local_games_cache)

        if not running_game and not self.running_game:
            pass
        elif not running_game:
            self.update_local_game_status(LocalGame(self.running_game.name, LocalGameState.Installed))
        elif not self.running_game:
            self.update_local_game_status(LocalGame(running_game.name, LocalGameState.Installed | LocalGameState.Running))
        elif self.running_game.name != running_game.name:
            self.update_local_game_status(LocalGame(self.running_game.name, LocalGameState.Installed))
            self.update_local_game_status(LocalGame(running_game.name, LocalGameState.Installed | LocalGameState.Running))

        self.running_game = running_game

    async def update_owned_games(self):
        owned_games_cache = self.owned_games_cache
        owned_games = await self.get_owned_games()
        log.info("Looking for new games")
        for game in owned_games:
            if game not in owned_games_cache:
                log.info(f"Adding game {game}")
                self.add_game(game)


    def tick(self):
        self.tick_counter += 1

        if not self.owned_games_called or (sys.platform == 'win32' and not self.local_games_called):
            return

        if self.tick_counter % 300 == 0:
            if not self.update_owned_games_task or self.update_owned_games_task.done():
                self.update_owned_games_task = asyncio.create_task(self.update_owned_games())

        if sys.platform != 'win32':
            return

        if not self.update_installed_games_task or self.update_installed_games_task.done():
            self.update_installed_games_task = asyncio.create_task(self.update_installed_games())
        if not self.update_running_games_task or self.update_running_games_task.done():
            self.update_running_games_task = asyncio.create_task(self.update_running_games())

    async def shutdown(self):
        await self._http_client.close()

    async def prepare_os_compatibility_context(self, game_ids: List[str]) -> Any:
        return None

    async def get_os_compatibility(self, game_id: str, context: Any) -> Optional[OSCompatibility]:
        return OSCompatibility.Windows


def main():
    create_and_run_plugin(ParadoxPlugin, sys.argv)


if __name__ == "__main__":
    main()
