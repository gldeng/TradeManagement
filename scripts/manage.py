import os
import sys
from flask import jsonify
from flask_script import Manager
import hashlib

dirname = os.path.abspath(os.path.dirname(__file__))

sys.path.insert(0, os.path.join(dirname, '..'))

from trademan import create_app, db, User

configfile = os.path.join(dirname, 'app.cfg')

app = create_app(configfile)


manager = Manager(app)


@manager.command
def add_user(username, password):
    if User.query.filter_by(username=username).first():
        print 'User already exists.'
        return
    m = hashlib.md5()
    m.update(password)
    with app.app_context():
        db.create_all()
        user = User(
            username=username,
            password=m.hexdigest()
        )
        db.session.add(user)
        db.session.commit()


if __name__ == "__main__":
    manager.run()
