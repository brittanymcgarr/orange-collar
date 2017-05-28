#!flask/bin/python
import os.path
import imp
import sys

from migrate.versioning import api
from config import SQLALCHEMY_DATABASE_URI, SQLALCHEMY_MIGRATE_REPO
from app import db

# Create Database
def create_db():
    db.create_all()
    
    if not os.path.exists(SQLALCHEMY_MIGRATE_REPO):
        api.create(SQLALCHEMY_MIGRATE_REPO, 'database repository')
        api.version_control(SQLALCHEMY_DATABASE_URI, SQLALCHEMY_MIGRATE_REPO)
    else:
        api.version_control(SQLALCHEMY_DATABASE_URI, SQLALCHEMY_MIGRATE_REPO, 
                            api.version(SQLALCHEMY_MIGRATE_REPO))
   
# Migrate the Database                     
def migrate():
    version = api.db_version(SQLALCHEMY_DATABASE_URI, SQLALCHEMY_MIGRATE_REPO)
    migration = SQLALCHEMY_MIGRATE_REPO + ('/versions/%03d_migration.py' % 
                                           (version + 1))
    tmp_module = imp.new_module('old_model')
    old_model = api.create_model(SQLALCHEMY_DATABASE_URI, SQLALCHEMY_MIGRATE_REPO)
    
    exec(old_model, tmp_module.__dict__)
    
    script = api.make_update_script_for_model(SQLALCHEMY_DATABASE_URI, 
                                              SQLALCHEMY_MIGRATE_REPO, 
                                              tmp_module.meta, db.metadata)
                                              
    open(migration, 'wt').write(script)
    
    api.upgrade(SQLALCHEMY_DATABASE_URI, SQLALCHEMY_MIGRATE_REPO)
    version = api.db_version(SQLALCHEMY_DATABASE_URI, SQLALCHEMY_MIGRATE_REPO)
    
    print('New migration saved as' + migration)
    print('Current database version: ' + str(version))
    
# Upgrade a staged version
def upgrade():
    api.upgrade(SQLALCHEMY_DATABASE_URI, SQLALCHEMY_MIGRATE_REPO)
    version = api.db_version(SQLALCHEMY_DATABASE_URI, SQLALCHEMY_MIGRATE_REPO)
    
    print('Current database version: ' + str(version))
    
# Rollback a database version
def downgrade():
    version = api.db_version(SQLALCHEMY_DATABASE_URI, SQLALCHEMY_MIGRATE_REPO)
    api.downgrade(SQLALCHEMY_DATABASE_URI, SQLALCHEMY_MIGRATE_REPO, version - 1)
    version = api.db_version(SQLALCHEMY_DATABASE_URI, SQLALCHEMY_MIGRATE_REPO)
    
    print('Current database version: ' + str(version))
    
if sys.argv[1] is not '':
    if sys.argv[1] == "create":
        create_db()
    elif sys.argv[1] == "migrate":
        migrate()
    elif sys.argv[1] == "upgrade":
        upgrade()
    elif sys.argv[1] == "downgrade":
        downgrade()
    else:
        print "Did not recognize command. Please use \'create,\' \'migrate,\', \'upgrade,\' or \'downgrade\' "