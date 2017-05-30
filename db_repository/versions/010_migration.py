from sqlalchemy import *
from migrate import *


from migrate.changeset import schema
pre_meta = MetaData()
post_meta = MetaData()
user = Table('user', post_meta,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('name', String(length=64)),
    Column('email', String(length=120)),
    Column('password_hash', String(length=128)),
    Column('authenticated', Boolean, default=ColumnDefault(False)),
    Column('primary_address', String(length=255)),
    Column('primary_lat_coord', Float(precision=8)),
    Column('primary_long_coord', Float(precision=8)),
    Column('secondary_address', String(length=255)),
    Column('secondary_lat_coord', Float(precision=8)),
    Column('secondary_long_coord', Float(precision=8)),
    Column('primary_phone', String(length=11)),
    Column('secondary_phone', String(length=11)),
    Column('allow_mms', Boolean, default=ColumnDefault(False)),
    Column('allow_sms', Boolean, default=ColumnDefault(False)),
    Column('allow_voice', Boolean, default=ColumnDefault(False)),
    Column('pet_watch', Boolean, default=ColumnDefault(False)),
    Column('last_mms', DateTime),
    Column('last_sms', DateTime),
    Column('last_call', DateTime),
)


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    post_meta.tables['user'].columns['pet_watch'].create()


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    post_meta.tables['user'].columns['pet_watch'].drop()
