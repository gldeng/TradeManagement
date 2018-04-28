from flask import Flask, Blueprint, Response, json, redirect, url_for, jsonify
from flask_login import LoginManager, login_user, current_user, login_required
from flask_admin import Admin
import hashlib
import requests
import re
from collections import defaultdict
from .models import db, User, Trade, TradeSummary
from .views import TradeAdminView, TradeAssociationAdminView, TradeSummaryAdminView
from datetime import datetime


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
        if 'address' not in raw_json:
            # trade
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
        else:
            # transfer
            timestampms = raw_json.get('insertTime') or raw_json.get('applyTime')
            trade_id = timestampms
            return Trade(
                exchange=raw_json['exchange'],
                trade_id = trade_id,
                timestampms = timestampms,
                pair = raw_json['asset'].lower(),
                price = 1.0,
                quantity = float(raw_json['amount']),
                fee = 0.0,
                fee_currency = raw_json['asset'],
                trade_type = 'Credit' if 'deposit' in raw_json['type'].lower() else 'Debit' if 'withdraw' in raw_json['type'].lower() else '',
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

    def update_trade_summary(self):
        summaries = defaultdict(lambda : {'buy': 0.0, 'sell': 0.0, 'fee': 0.0, 'credit': 0.0, 'debit': 0.0})
        for item in Trade.query.all():
            if item.trade_type in ['Buy', 'Sell']:
                first_id = (item.exchange, item.pair.split('_')[0])
                first_amt = item.quantity
                second_id = (item.exchange, item.pair.split('_')[1])
                second_amt = item.quantity * item.price
                if first_id[1] in ('usd', 'usdt'):
                    first_id = (first_id[0], first_id[1] + '_' + second_id[1])
                if second_id[1] in ('usd', 'usdt'):
                    second_id = (second_id[0], second_id[1] + '_' + first_id[1])
                if item.trade_type == 'Buy':
                    summaries[first_id]['buy'] += first_amt
                    summaries[second_id]['sell'] += second_amt
                else:
                    summaries[first_id]['sell'] += first_amt
                    summaries[second_id]['buy'] += second_amt
            else:
                # credit (deposit) or debit (withdraw)
                summaries[(item.exchange, item.pair)][item.trade_type.lower()] += item.quantity
            if item.fee:
                summaries[(item.exchange, item.fee_currency.lower().replace('usdt', 'usd'))]['fee'] += item.fee
        now = datetime.now()
        TradeSummary.query.delete()
        for k in sorted(summaries.keys()):
            v = summaries[k]
            ts = TradeSummary(
                exchange=k[0],
                asset=k[1],
                buy=v['buy'],
                sell=v['sell'],
                fee=v['fee'],
                credit=v['credit'],
                debit=v['debit'],
                updated=now
            )
            db.session.merge(ts)
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
    admin.add_view(
        TradeSummaryAdminView(
            db.session, name='Trade Summaries', endpoint='tradesummaries',
            url='/tradesummaries'
        )
    )

    @app.route('/')
    @login_required
    def index():
        return redirect(url_for('admin.index'))

    @app.route('/api/trades')
    @login_required
    def api_trades():
        out = []
        for item in Trade.query.all():
            out.append(item.to_json())
        return jsonify(out)

    @app.route('/api/tradesummaries')
    @login_required
    def api_tradesummaries():
        out = []
        for item in TradeSummary.query.all():
            out.append(item.to_json())
        return jsonify(out)

    with app.app_context():
        db.create_all()
        # app.update_trades()

    return app
