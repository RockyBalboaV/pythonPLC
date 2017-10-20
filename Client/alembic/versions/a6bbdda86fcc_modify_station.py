"""modify station

Revision ID: a6bbdda86fcc
Revises: 
Create Date: 2017-10-20 17:19:35.988667

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = 'a6bbdda86fcc'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('yjplcinfo', sa.Column('con_time', sa.Integer(), nullable=True))
    op.add_column('yjstationinfo', sa.Column('check_time', sa.Integer(), nullable=True))
    op.add_column('yjstationinfo', sa.Column('con_time', sa.Integer(), nullable=True))
    op.add_column('yjstationinfo', sa.Column('off_time', sa.Integer(), nullable=True))
    op.add_column('yjstationinfo', sa.Column('power_err', sa.Boolean(), nullable=True))
    op.add_column('yjstationinfo', sa.Column('uptime', sa.Integer(), nullable=True))
    op.drop_column('yjstationinfo', 'con_date')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('yjstationinfo', sa.Column('con_date', mysql.INTEGER(display_width=11), autoincrement=False, nullable=True))
    op.drop_column('yjstationinfo', 'uptime')
    op.drop_column('yjstationinfo', 'power_err')
    op.drop_column('yjstationinfo', 'off_time')
    op.drop_column('yjstationinfo', 'con_time')
    op.drop_column('yjstationinfo', 'check_time')
    op.drop_column('yjplcinfo', 'con_time')
    # ### end Alembic commands ###
