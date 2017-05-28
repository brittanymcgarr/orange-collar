from sqlalchemy import *
from migrate import *


from migrate.changeset import schema
pre_meta = MetaData()
post_meta = MetaData()
pet = Table('pet', post_meta,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('name', String(length=120)),
    Column('species', String(length=32)),
    Column('color', String(length=32)),
    Column('breed', String(length=32)),
    Column('gender', String(length=32)),
    Column('description', Text),
    Column('indoor_pet', Boolean, default=ColumnDefault(True)),
    Column('status', String(length=32)),
    Column('additional_info', Text),
    Column('owner_notified_last', DateTime),
    Column('user_id', Integer),
    Column('home_address', String(length=255)),
    Column('home_lat_coord', Float(precision=8)),
    Column('home_long_coord', Float(precision=8)),
    Column('secondary_address', String(length=255)),
    Column('sighting_coords', Text),
)

users = Table('users', post_meta,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('name', String(length=64)),
    Column('email', String(length=120)),
    Column('password_hash', String(length=128)),
    Column('primary_address', String(length=255)),
    Column('primary_lat_coord', Float(precision=8)),
    Column('primary_long_coord', Float(precision=8)),
    Column('secondary_address', String(length=255)),
    Column('secondary_lat_coord', Float),
    Column('secondary_long_coord', Float(precision=8)),
    Column('primary_phone', String(length=11)),
    Column('secondary_phone', String(length=11)),
    Column('allow_mms', Boolean, default=ColumnDefault(False)),
    Column('allow_sms', Boolean, default=ColumnDefault(False)),
    Column('allow_voice', Boolean, default=ColumnDefault(False)),
    Column('last_mms', DateTime),
    Column('last_sms', DateTime),
    Column('last_call', DateTime),
)


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    post_meta.tables['pet'].create()
    post_meta.tables['users'].columns['last_call'].create()
    post_meta.tables['users'].columns['last_mms'].create()
    post_meta.tables['users'].columns['last_sms'].create()
    post_meta.tables['users'].columns['primary_lat_coord'].create()
    post_meta.tables['users'].columns['primary_long_coord'].create()
    post_meta.tables['users'].columns['secondary_lat_coord'].create()
    post_meta.tables['users'].columns['secondary_long_coord'].create()


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    post_meta.tables['pet'].drop()
    post_meta.tables['users'].columns['last_call'].drop()
    post_meta.tables['users'].columns['last_mms'].drop()
    post_meta.tables['users'].columns['last_sms'].drop()
    post_meta.tables['users'].columns['primary_lat_coord'].drop()
    post_meta.tables['users'].columns['primary_long_coord'].drop()
    post_meta.tables['users'].columns['secondary_lat_coord'].drop()
    post_meta.tables['users'].columns['secondary_long_coord'].drop()
