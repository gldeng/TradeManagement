from flask import Flask, Blueprint, Response, json, redirect, url_for
from flask_login import LoginManager, login_user, current_user, login_required
from flask_admin import Admin
import hashlib
import requests
import re
from .models import db, User, Trade
from .views import TradeAdminView, TradeAssociationAdminView


def _authenticate():
    return Response(
        'Please login', 401,
        {'WWW-Authenticate': 'Basic realm="Login Required"'}
    )


def _load_user(username):
    return User.query.filter_by(username=username).first()


def _load_user_from_request(request):
    auth = request.authorization
    if auth is None:
        return None
    u, p = auth.username, auth.password
    user = User.query.filter_by(username=u).first()
    if user is None:
        return None
    if isinstance(p, unicode):
        p = p.encode('utf8')
    m = hashlib.md5()
    m.update(p)
    digest = m.hexdigest()
    if digest.lower() == user.password.lower():
        login_user(user)
        return user
    return None


def get_trade_entry(raw_json):
    if raw_json['exchange'] == 'gemini':
        if 'tid' in raw_json:
            return Trade(
                exchange=raw_json['exchange'],
                trade_id = raw_json['tid'],
                timestampms = raw_json['timestampms'],
                pair = raw_json['pair'],
                price = raw_json['price'],
                quantity = raw_json['amount'],
                fee = raw_json['fee_amount'],
                fee_currency = raw_json['fee_currency'],
                trade_type = raw_json['type'],
                raw = json.dumps(raw_json),
            )
        else:
            return Trade(
                **raw_json
            )
    if raw_json['exchange'] == 'binance':
        return Trade(
            exchange=raw_json['exchange'],
            trade_id = raw_json['id'],
            timestampms = raw_json['time'],
            pair = raw_json['pair'],
            price = raw_json['price'],
            quantity = float(raw_json['qty']),
            fee = float(raw_json['commission']),
            fee_currency = raw_json['commissionAsset'],
            trade_type = 'Buy' if raw_json['isBuyer'] else 'Sell',
            raw = json.dumps(raw_json),
        )
    if raw_json['exchange'] == 'fyb':
        return Trade(
            **raw_json
        )


class MyFlask(Flask):

    def update_trades(self):
        for url in self.config['TRADES_DATA_URL'].split('|'):
            r = requests.get(url)
            if r.status_code == 200 and r.json():
                for item in r.json():
                    if 'gemini' in url:
                        item['exchange'] = 'gemini'
                    elif 'binance' in url:
                        item['exchange'] = 'binance'
                    if not item.get('pair'):
                        item['pair'] = '_'.join(re.findall('btc|eth|usd|eos|ruff|neo', url.split('/')[-1]))
                    trd = get_trade_entry(item)
                    if trd:
                        db.session.merge(trd)
        db.session.commit()


def create_app(config_pyfile):
    app = MyFlask(__name__, instance_relative_config=False)
    app.config.from_pyfile(config_pyfile)
    db.init_app(app)
    login_manager = LoginManager(app)
    login_manager.user_loader(_load_user)
    login_manager.request_loader(_load_user_from_request)
    login_manager.unauthorized_handler(_authenticate)

    admin = Admin(app)
    admin.add_view(
        TradeAdminView(
            db.session, name='Trades', endpoint='trades',
            url='/trades'
        )
    )
    admin.add_view(
        TradeAssociationAdminView(
            db.session, name='Trade Associations', endpoint='tradeassociations',
            url='/tradeassociations'
        )
    )

    @app.route('/')
    @login_required
    def index():
        return redirect(url_for('admin.index'))

    with app.app_context():
        db.create_all()
        # app.update_trades()

    return app
