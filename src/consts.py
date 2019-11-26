import re
import sys
from enum import EnumMeta


AUTH_URL = r"https://accounts.paradoxplaza.com/login"
AUTH_REDIRECT_URL = r"api/accounts/connections/"

REGISTRY_LAUNCHER_PATH = r"SOFTWARE\WOW6432Node\Paradox Interactive\Paradox Launcher\LauncherPath"
PARADOX_LAUNCHER_EXE = "Paradox Launcher.exe"


class System(EnumMeta):
    WINDOWS = 1
    MACOS = 2
    LINUX = 3


if sys.platform == 'win32':
    SYSTEM = System.WINDOWS
elif sys.platform == 'darwin':
    SYSTEM = System.MACOS


def regex_pattern(regex):
    return ".*" + re.escape(regex) + ".*"


AUTH_PARAMS = {
    "window_title": "Login to Paradox\u2122",
    "window_width": 700,
    "window_height": 800,
    "start_uri": AUTH_URL,
    "end_uri_regex": regex_pattern(AUTH_REDIRECT_URL)
}


