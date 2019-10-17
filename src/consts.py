
import re


AUTH_URL = r"https://accounts.paradoxplaza.com/login"
AUTH_REDIRECT_URL = r"api/accounts/connections/"

REGISTRY_LAUNCHER_PATH = r"SOFTWARE\WOW6432Node\Paradox Interactive\Paradox Launcher\LauncherPath"
PARADOX_LAUNCHER_EXE = "Paradox Launcher.exe"


def regex_pattern(regex):
    return ".*" + re.escape(regex) + ".*"

AUTH_PARAMS = {
    "window_title": "Login to Paradox\u2122",
    "window_width": 700,
    "window_height": 800,
    "start_uri": AUTH_URL,
    "end_uri_regex": regex_pattern(AUTH_REDIRECT_URL)
}


