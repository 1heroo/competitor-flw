import aiohttp
import pandas as pd

from app.queries import MyProductQueries
from app.utils import WbAPIUtils, AppUtils, MatchAPIUtils
from core.settings import settings


class AppServices:

    def __init__(self):
        self.my_product_queries = MyProductQueries()
        self.wb_api_utils = WbAPIUtils()
        self.app_utils = AppUtils()
        self.match_api_utils = MatchAPIUtils()

    async def cr_follow_management(self):
        my_products = await self.my_product_queries.fetch_all()
        my_products_df = pd.DataFrame(
            [{'nm_id': product.nm_id, 'rrc': product.rrc} for product in my_products]
        )
        child_matched_product = await self.match_api_utils.get_children_bunch_nms(nms=[product.nm_id for product in my_products])
        child_matched_product_df = pd.DataFrame(child_matched_product)

        df = pd.merge(my_products_df, child_matched_product_df, how='inner', left_on='nm_id', right_on='product_nm_id')

        output_data = []
        for index in df.index:
            child_details = await self.app_utils.get_details_by_nms(nms=df.children[index])
            print(df['product_nm_id'][index])
            for child in child_details:
                price = child['detail'].get('salePriceU')
                extended = child['detail'].get('extended', {})
                if not price:
                    continue
                else:
                    price = int(price) / 100
                    clientSale = extended.get('clientSale', 0)
                    price = price / (100 - clientSale) * 100

                if price < df.rrc[index]:
                    output_data.append({
                        'parent_nm_id': df.product_nm_id[index],
                        'nm_id': child.get('id'),
                        'product_price': price,
                        'rrc': df.rrc[index],
                        'разница': df.rrc[index] - price,
                        '% разница': round(((df.rrc[index] - price) / df.rrc[index]) * 100, 1),
                        'Продвавец': child['seller'].get('supplierName'),
                        'link': f'https://www.wildberries.ru/catalog/{child["detail"].get("id")}/detail.aspx'
                    })
        return output_data

    async def import_products(self, df: pd.DataFrame, article_column: str, price_column: str) -> None:
        auth = self.wb_api_utils.auth(token=settings.WB_STANDARD_API_TOKEN)
        api_products = await self.wb_api_utils.get_products(token_auth=auth)
        products_df = pd.DataFrame(api_products)
        no_bland_vendor_codes = products_df.vendorCode.apply(lambda item: item.split('bland')[-1])
        products_df['no_bland_vendor_codes'] = no_bland_vendor_codes

        df = pd.merge(df, products_df, how='inner', left_on=article_column, right_on='no_bland_vendor_codes')

        products_to_be_saved = []
        for index in df.index:
            products_to_be_saved.append(self.app_utils.prepare_for_saving(
                nm_id=int(df['nmID'][index]),
                vendor_code=df['vendorCode'][index],
                rrc=int(df[price_column][index])
            ))

        await self.my_product_queries.save_or_update(instances=products_to_be_saved)
