import io
import os
import time

import pandas as pd
from fastapi import APIRouter, File
from starlette import status
from starlette.responses import Response, StreamingResponse

from app.services import AppServices
from app.xlsx_utils import XlsxUtils


router = APIRouter(prefix='/app', tags=['competitor monitoring'])
xlsx_utils = XlsxUtils()
app_services = AppServices()


@router.get('/follow-competitor/')
async def follow_competitor():
    arrested = await app_services.cr_follow_management()
    df = pd.DataFrame(arrested)

    output = io.BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    df.to_excel(writer)
    writer.save()

    return StreamingResponse(io.BytesIO(output.getvalue()),
                             media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                             headers={'Content-Disposition': f'attachment; filename="characteristics.xlsx"'})


@router.post('/import-rrc/')
async def import_rrc(sheet_name=None, file: bytes = File()):
    sheet_name = 0 if sheet_name is None else sheet_name

    file_name = str(int(time.time())) + '.csv'

    df = pd.read_excel(file, sheet_name=sheet_name, header=None)
    df = xlsx_utils.handle_xlsx(df=df, file_name=file_name)

    article_column = xlsx_utils.find_article_column(df=df)
    price_column = xlsx_utils.find_price_column(df=df)
    print(article_column, price_column)

    if article_column is None or price_column is None:
        os.remove(file_name)
        return Response(status_code=status.HTTP_404_NOT_FOUND)

    await app_services.import_products(df=df, article_column=article_column, price_column=price_column)
    os.remove(file_name)
    return Response(status_code=status.HTTP_200_OK)
