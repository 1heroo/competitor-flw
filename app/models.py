from db.db import Base
import sqlalchemy as sa


class MyProduct(Base):
    __tablename__ = 'my_product'

    id = sa.Column(sa.Integer, primary_key=True)
    nm_id = sa.Column(sa.Integer)
    vendor_code = sa.Column(sa.String)
    rrc = sa.Column(sa.Integer)

    def __str__(self):
        return str(self.nm_id)

    def __repr__(self):
        return str(self.nm_id)
