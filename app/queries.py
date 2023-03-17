from db.db import async_session
from app.models import MyProduct
from db.queries import BaseQueries
import sqlalchemy as sa


class MyProductQueries(BaseQueries):

    model = MyProduct

    async def fetch_all(self):
        async with async_session() as session:
            result = await session.execute(
                sa.select(self.model)
            )
            return result.scalars().all()

    async def save_or_update(self, instances):
        saved_instances = await self.fetch_all()
        all_nms = [price.nm_id for price in saved_instances]
        new_instances = [item for item in instances if item.nm_id not in all_nms]
        db_instances = []

        for instance in instances:
            for saved_instance in saved_instances:
                if instance.nm_id == saved_instance.nm_id:
                    saved_instance.rrc = instance.rrc
                    db_instances.append(saved_instance)

        await self.save_in_db(instances=new_instances + db_instances, many=True)
