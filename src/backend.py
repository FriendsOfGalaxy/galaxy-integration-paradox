import logging as log


class ParadoxClient:
    def __init__(self, http_client):
        self.http_client = http_client

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
                        if game['sku'] and game['title'] and game['product_type'] and "paradox builds" in game['platforms']:
                            owned_products.append({'sku': game['sku'],
                                                   'title': game['title'],
                                                   'type': game['product_type']})
        log.info(owned_products)
        return owned_products
