"""empty message

Revision ID: d449c6f323bd
Revises: 4d26f6a9b096
Create Date: 2022-05-10 17:37:21.054520

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd449c6f323bd'
down_revision = '4d26f6a9b096'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('recipe', sa.Column('ingredients', sa.String(length=1000), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('recipe', 'ingredients')
    # ### end Alembic commands ###
