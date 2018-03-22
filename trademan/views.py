from flask import current_app, url_for, redirect
from flask_admin.contrib import sqla
from flask_admin import expose
from flask_login import current_user
from .models import Trade, TradeAssociation, TradeSummary


class BaseAdminView(sqla.ModelView):
    def is_accessible(self):
        return current_user.is_authenticated


class TradeAdminView(BaseAdminView):
    
    list_template = 'trade_list_with_update.html'

    can_delete = False
    column_list = ['exchange', 'trade_id', 'trade_date', 'pair', 'price', 'quantity', 'trade_type']
    column_sortable_list = ['exchange', 'trade_id', 'price', 'quantity', 'trade_type']
    column_searchable_list = ['exchange', 'trade_id', 'price', 'quantity', 'trade_type']

    def __init__(self, session, **kwargs):
        super(TradeAdminView, self).__init__(Trade, session, **kwargs)

    @expose('/update')
    def update(self, *args, **kwargs):
        current_app.update_trades()
        return redirect(url_for(self.endpoint+'.index_view'))


class TradeAssociationAdminView(BaseAdminView):
    def __init__(self, session, **kwargs):
        super(TradeAssociationAdminView, self).__init__(TradeAssociation, session, **kwargs)


class TradeSummaryAdminView(BaseAdminView):
    list_template = 'trade_summary_list_with_update.html'
    can_delete = False
    can_edit = False
    can_create = False
    column_list = ['exchange', 'asset', 'buy', 'sell', 'fee', 'credit', 'debit', 'total_credit', 'total_debit', 'net', 'updated']
    column_sortable_list = ['exchange', 'asset']
    column_searchable_list = ['exchange', 'asset']

    def __init__(self, session, **kwargs):
        super(TradeSummaryAdminView, self).__init__(TradeSummary, session, **kwargs)

    @expose('/update')
    def update(self, *args, **kwargs):
        current_app.update_trade_summary()
        return redirect(url_for(self.endpoint+'.index_view'))
