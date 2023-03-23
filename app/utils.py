import asyncio
import json

import aiohttp

from app.models import MyProduct


class BaseUtils:

    @staticmethod
    async def make_post_request(url, headers, payload, no_json=False):
        async with aiohttp.ClientSession(trust_env=True, headers=headers) as session:
            async with session.post(url=url, json=payload) as response:
                print(response.status)

                if response.status == 200:
                    return True if no_json else json.loads(await response.text())

    @staticmethod
    async def make_get_request(url, headers, no_json=False):
        async with aiohttp.ClientSession(trust_env=True, headers=headers) as session:
            async with session.get(url=url) as response:
                # print(response.status)

                if response.status == 200:
                    return True if no_json else json.loads(await response.text())


class AppUtils(BaseUtils):

    @staticmethod
    def prepare_for_saving(nm_id, vendor_code, rrc):
        return MyProduct(
            nm_id=nm_id,
            vendor_code=vendor_code,
            rrc=rrc
        )

    @staticmethod
    def check_stocks(products):
        output_data = []
        for the_product in products:
            qty = 0
            sizes = the_product['detail'].get('sizes')
            if not sizes:
                continue

            for size in sizes:
                stocks = size.get('stocks')
                if not stocks:
                    continue

                for stock in stocks:
                    qty += stock.get('qty')

            if qty > 0:
                output_data.append(the_product)

        return output_data

    async def get_product_data(self, article):
        obj = dict()
        detail_url_with_no_clientSale = f'https://card.wb.ru/cards/detail?spp=27&regions=80,64,38,4,83,33,68,70,69,30,86,75,40,1,22,66,31,48,110,71&pricemarginCoeff=1.0&reg=1&appType=1&emp=0&locale=ru&lang=ru&curr=rub&couponsGeo=12,3,18,15,21&sppFixGeo=4&dest=-455203&nm={article}'
        detail_url_with_clientSale = f'https://card.wb.ru/cards/detail?spp=22&regions=80,64,38,4,115,83,33,68,70,69,30,86,75,40,1,66,48,110,22,31,71,114,111&pricemarginCoeff=1.0&reg=1&appType=1&emp=0&locale=ru&lang=ru&curr=rub&couponsGeo=12,3,18,15,21&sppFixGeo=4&dest=-1257786&nm={article}'
        detail = await self.make_get_request(detail_url_with_clientSale, headers={})

        if detail:
            detail = detail['data']['products']
        else:
            detail = {}

        seller_url = make_head(int(article)) + make_tail(str(article), 'sellers.json')
        seller_data = await self.make_get_request(seller_url, headers={})

        obj.update({
            'detail': detail[0] if detail else {},
            'seller': seller_data if seller_data else {}
        })
        return obj

    async def get_details_by_nms(self, nms):
        output_data = []
        tasks = []
        count = 1

        for nm in nms:
            task = asyncio.create_task(self.get_product_data(article=nm))
            tasks.append(task)
            count += 1

            if count % 50 == 0:
                print(count, 'product data')
                output_data += await asyncio.gather(*tasks, return_exceptions=True)
                tasks = []

        output_data += await asyncio.gather(*tasks, return_exceptions=True)
        output_data = [item for item in output_data if not isinstance(item, Exception) and item]
        return output_data


class MatchAPIUtils(BaseUtils):

    host = 'http://94.228.120.15:8000'

    async def get_child_matched_products(self, nm_id):
        url = self.host + f'/api/v1/matched-product/{nm_id}/get-matches/'
        data = await self.make_get_request(url=url, headers={})
        return data

    async def get_children_bunch_nms(self, nms):
        output_data = []
        tasks = []
        count = 0

        for nm in nms:
            task = asyncio.create_task(self.get_child_matched_products(nm_id=nm))
            tasks.append(task)
            count += 1

            if count % 50 == 0:
                print(count)
                output_data += await asyncio.gather(*tasks, return_exceptions=True)
                tasks = []
        output_data += await asyncio.gather(*tasks, return_exceptions=True)
        output_data = [item for item in output_data if not isinstance(item, Exception) and item]
        return output_data


class WbAPIUtils(BaseUtils):

    @staticmethod
    def auth(token):
        return {
            'Authorization': token
        }

    async def get_products(self, token_auth):
        data = []
        url = 'https://suppliers-api.wildberries.ru/content/v1/cards/cursor/list'
        payload = {
            "sort": {
                "cursor": {
                    "limit": 1000
                },
                "filter": {
                    "withPhoto": -1
                }
            }
        }
        total = 1
        while total != 0:
            partial_data = await self.make_post_request(url=url, payload=payload, headers=token_auth)
            data += partial_data['data']['cards']
            cursor = partial_data['data']['cursor']
            payload['sort']['cursor'].update(cursor)
            total = cursor['total']
        return data


def make_head(article: int):
    head = 'https://basket-{i}.wb.ru'

    if article < 14400000:
        number = '01'
    elif article < 28800000:
        number = '02'
    elif article < 43500000:
        number = '03'
    elif article < 72000000:
        number = '04'
    elif article < 100800000:
        number = '05'
    elif article < 106300000:
        number = '06'
    elif article < 111600000:
        number = '07'
    elif article < 117000000:
        number = '08'
    elif article < 131400000:
        number = '09'
    else:
        number = '10'
    return head.format(i=number)


def make_tail(article: str, item: str):
    length = len(str(article))
    if length <= 3:
        return f'/vol{0}/part{0}/{article}/info/' + item
    elif length == 4:
        return f'/vol{0}/part{article[0]}/{article}/info/' + item
    elif length == 5:
        return f'/vol{0}/part{article[:2]}/{article}/info/' + item
    elif length == 6:
        return f'/vol{article[0]}/part{article[:3]}/{article}/info/' + item
    elif length == 7:
        return f'/vol{article[:2]}/part{article[:4]}/{article}/info/' + item
    elif length == 8:
        return f'/vol{article[:3]}/part{article[:5]}/{article}/info/' + item
    else:
        return f'/vol{article[:4]}/part{article[:6]}/{article}/info/' + item

