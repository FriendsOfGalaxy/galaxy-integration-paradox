
from galaxy.http import HttpClient

import aiohttp
import logging as log
from yarl import URL
import pickle

class CookieJar(aiohttp.CookieJar):
    def __init__(self):
        super().__init__()
        self._cookies_updated_callback = None

    def set_cookies_updated_callback(self, callback):
        self._cookies_updated_callback = callback

    def update_cookies(self, cookies, url=URL()):
        super().update_cookies(cookies, url)
        if cookies and self._cookies_updated_callback:
            self._cookies_updated_callback(list(self))


class AuthenticatedHttpClient(HttpClient):

    def __init__(self, store_credentials):
        self._store_credentials = store_credentials
        self.token = None

        self.bearer = None
        self.user = None
        self._cookie_jar = CookieJar()
        self._auth_lost_callback = None

        super().__init__(cookie_jar=self._cookie_jar)

    def set_cookies_updated_callback(self, callback):
        self._cookie_jar.set_cookies_updated_callback(callback)

    def update_cookies(self, cookies):
        self._cookie_jar.update_cookies(cookies)

    def set_auth_lost_callback(self, callback):
        self._auth_lost_callback = callback


    def get_credentials(self):
        creds = {}
        creds['cookie_jar'] = pickle.dumps([c for c in self._cookie_jar]).hex()
        return creds

    async def do_request(self, method, *args, **kwargs):
        try:
            return await self.request(method, *args, **kwargs)
        except Exception as e:
            log.warning(f"Request failed with {repr(e)}, attempting to refresh credentials")
            #await self.refresh_credentials()
            return await self.request(method, *args, **kwargs)

    def authenticate_with_cookies(self, cookies):
        cookiez = {}
        for cookie in cookies:
            if 'value' in cookie:
                cookiez[cookie['name']] = cookie['value']
            else:
                cookiez[cookie.key] = cookie.value
        self.update_cookies(cookiez)
        self.token = cookiez['SESSION_TOKEN']
        self._store_credentials(self.get_credentials())






