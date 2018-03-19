from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand
import os
import sys

dirname = os.path.abspath(os.path.dirname(__file__))

sys.path.insert(0, os.path.join(dirname, '..'))

from trademan import create_app

configfile = os.path.join(dirname, 'app.cfg')

app = create_app(configfile)
db = app.extensions['sqlalchemy']
migrate = Migrate(app, db)

manager = Manager(app)
manager.add_command('db', MigrateCommand)


if __name__ == '__main__':
    manager.run()
