"""initial

Revision ID: b584817e44a2
Revises: 
Create Date: 2023-03-17 23:16:01.015252

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b584817e44a2'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('my_product',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('nm_id', sa.Integer(), nullable=True),
    sa.Column('vendor_code', sa.String(), nullable=True),
    sa.Column('rrc', sa.Integer(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('my_product')
    # ### end Alembic commands ###
