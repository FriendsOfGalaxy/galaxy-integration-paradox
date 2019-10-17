import logging as log
import asyncio


class ParadoxClient:
    def __init__(self, http_client):
        self.http_client = http_client
        self.paradox_launcher_skus = None

    async def prepare_sku(self):
        data = {'token': self.http_client.token}
        log.info('Starting skus retrieve')
        response = await self.http_client.do_request('GET', 'https://accounts.paradoxplaza.com/api/skus', headers=data)
        response = await response.json()
        log.info('Finished skus retrieve')
        paradox_launcher_skus = set()
        for sku in response:
            await asyncio.sleep(0.01)
            if 'paradoxLauncher' in response[sku]['platform']:
                paradox_launcher_skus.add(sku)
        self.paradox_launcher_skus = paradox_launcher_skus

    async def get_account_id(self):
        data = {'Authorization': f'{{"session":{{"token":"{self.http_client.token}"}}}}',
                'content-type': 'application/json'}
        response = await self.http_client.do_request('GET', 'https://api.paradox-interactive.com/accounts', headers=data)
        response = await response.json()
        return response['id']

    async def get_owned_games(self):
        data = {'Authorization': f'{{"session":{{"token":"{self.http_client.token}"}}}}',
                'content-type': 'application/json'}
        response = await self.http_client.do_request('GET', 'https://api.paradox-interactive.com/inventory/products',
                                                     headers=data)

        response = await response.json()
        owned_products = []
        if 'products' in response:
            for platforms in response['products']:
                for platform in platforms:
                    for game in platforms[platform]:
                        log.info(game)
                        if game['sku'] and game['title'] and game['product_type']:
                            owned_products.append({'sku': game['sku'],
                                                   'title': game['title'],
                                                   'type': game['product_type']})
        log.info(owned_products)
        return owned_products
