import logging as log


class ParadoxClient:
    def __init__(self, http_client):
        self.http_client = http_client
        self._skus = {}

    async def get_skus(self):
        if not self._skus:
            skus = await self.http_client.do_request('GET', 'https://accounts.paradoxplaza.com/api/skus',
                                                     headers={'content-type': 'application/json'})
            self._skus = await skus.json()
        return self._skus

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
        skus = await self.get_skus()

        owned_products = []
        if 'products' in response:
            for platforms in response['products']:
                for platform in platforms:
                    for game in platforms[platform]:
                        log.info(game)
                        if game['sku'] and game['title'] and game['product_type']:
                            if (game['sku'] in skus and 'paradoxLauncher' in skus[game['sku']]['platform']) \
                                    or "paradox builds" in game['platforms']:
                                owned_products.append({'sku': game['sku'],
                                                       'title': game['title'],
                                                       'type': game['product_type']})

        log.info(owned_products)
        return owned_products
