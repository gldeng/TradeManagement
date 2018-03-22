from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime


db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(200), unique=True)

    @property
    def is_authenticated(self):
        return True

    @property
    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return unicode(self.username)

    def __repr__(self):
        return '<User %r>' % self.username


class Trade(db.Model):
    exchange = db.Column(db.String(20), primary_key=True)
    trade_id = db.Column(db.Integer, primary_key=True)
    timestampms = db.Column(db.Integer)
    pair = db.Column(db.String(100))
    price = db.Column(db.Float)
    quantity = db.Column(db.Float)
    fee = db.Column(db.Float)
    fee_currency = db.Column(db.String(20))
    trade_type = db.Column(db.String(20))
    notes = db.Column(db.Text)
    raw = db.Column(db.Text)
    downstreams = db.relationship(
        'Trade', secondary='trade_association',
        primaryjoin='and_(Trade.exchange == TradeAssociation.upstream_exchange, Trade.trade_id == TradeAssociation.upstream_trade_id)',
        secondaryjoin='and_(Trade.exchange == TradeAssociation.downstream_exchange, Trade.trade_id == TradeAssociation.downstream_trade_id)',
        backref=db.backref('upstreams', lazy='dynamic')
    )

    __table_args__ = (
        db.UniqueConstraint('exchange', 'trade_id', name='_exchange_trade_id'),
    )

    @property
    def trade_date(self):
        return datetime.fromtimestamp(float(self.timestampms) / 1e3)

    def __repr__(self):
        return self.exchange + ' ' + str(self.trade_id)

    def to_json(self):
        fields = [
            'exchange', 'trade_id', 'timestampms',
            'pair', 'price', 'quantity', 'fee',
            'fee_currency', 'trade_type', 'notes',
            'raw'
        ]
        out = {f: getattr(self, f) for f in fields}
        out['trade_date'] = str(self.trade_date)
        return out


class TradeAssociation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    upstream_exchange = db.Column(db.Integer)
    upstream_trade_id = db.Column(db.String(20))
    downstream_exchange = db.Column(db.Integer)
    downstream_trade_id = db.Column(db.String(20))
    upstream = db.relationship('Trade', primaryjoin='and_(Trade.exchange == TradeAssociation.upstream_exchange, Trade.trade_id == TradeAssociation.upstream_trade_id)')
    downstream = db.relationship('Trade', primaryjoin='and_(Trade.exchange == TradeAssociation.downstream_exchange, Trade.trade_id == TradeAssociation.downstream_trade_id)')
    notes = db.Column(db.Text)
    __table_args__ = (
        db.ForeignKeyConstraint(
            [upstream_exchange, upstream_trade_id],
            [Trade.exchange, Trade.trade_id]
        ),
        db.ForeignKeyConstraint(
            [downstream_exchange, downstream_trade_id],
            [Trade.exchange, Trade.trade_id]
        ),
        {}
    )


class TradeSummary(db.Model):
    exchange = db.Column(db.String(20), primary_key=True)
    asset = db.Column(db.String(20), primary_key=True)
    credit = db.Column(db.Float)
    debit = db.Column(db.Float)
    updated = db.Column(db.DateTime)

    @property
    def net(self):
        return self.credit - self.debit

    def to_json(self):
        fields = [
            'exchange', 'asset', 'credit',
            'debit', 'net'
        ]
        out = {f: getattr(self, f) for f in fields}
        out['updated'] = str(self.updated)
        return out
