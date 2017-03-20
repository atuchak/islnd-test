from django.conf.urls import url, include
from partner_balance.views import PartnerTransactionView, PartnerBalanceView

urlpatterns = [
    url(r'^partner/transaction/(?P<partner_id>[0-9]+)/$', PartnerTransactionView.as_view(), name='transaction_view'),
    url(r'^partner/balance/(?P<partner_id>[0-9]+)/$', PartnerBalanceView.as_view(), name='balance_view'),

]
