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
    Column('picture', String(length=200), default=ColumnDefault('')),
)


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    post_meta.tables['pet'].columns['picture'].create()


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    post_meta.tables['pet'].columns['picture'].drop()
