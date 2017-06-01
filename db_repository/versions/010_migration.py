from sqlalchemy import *
from migrate import *


from migrate.changeset import schema
pre_meta = MetaData()
post_meta = MetaData()
alert = Table('alert', post_meta,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('phone', String(length=8)),
    Column('time_issued', DateTime),
    Column('message', String(length=1024)),
    Column('media', String(length=1024)),
)


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    post_meta.tables['alert'].create()


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    post_meta.tables['alert'].drop()
