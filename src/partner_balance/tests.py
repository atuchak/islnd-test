import json
from datetime import timedelta

import django
from django.db.models import Sum
from django.urls import reverse
from django.utils import timezone
import factory
from decimal import Decimal

import pytest

# Create your tests here.
from partner_balance.models import Partner, Transaction, AggregatedTransactions
from partner_balance.views import get_partner_balance, change_partner_balance, update_aggregated_transaction, \
    change_partner_balance_ag, get_partner_balance_ag


class PartnerFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = 'partner_balance.Partner'
        # django_get_or_create = ('balance',)

    # id = factory.sequence(lambda n: n, )
    # balance = factory.sequence(lambda n: Decimal('0.99') + n)
    balance = Decimal("0.00")


class TransactionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = 'partner_balance.Transaction'

    amount = Decimal('-0.99')
    date = factory.LazyFunction(timezone.now)
    partner = factory.LazyFunction(PartnerFactory)


@pytest.mark.django_db(transaction=True)
def test_change_partner_balance():
    # partner does not exits
    with pytest.raises(django.http.response.Http404):
        change_partner_balance(999, Decimal('0.1'))

    partner = PartnerFactory()
    change_partner_balance(partner.id, Decimal('0.1'))

    assert Partner.objects.get(pk=partner.id).balance == Decimal('0.1')

    # now balance should be 0
    change_partner_balance(partner.id, Decimal('-0.1'), date=timezone.now() - timedelta(days=1))
    partner = Partner.objects.get(pk=partner.id)
    assert partner.balance == Decimal('0')
    assert partner.partner_transaction.values('amount').aggregate(Sum('amount'))['amount__sum'] == 0

    # yesterday balance should be -0.1
    yesterday_transactions = partner.partner_transaction.filter(date__lte=timezone.now() - timedelta(days=1))
    assert yesterday_transactions.values('amount').aggregate(Sum('amount'))['amount__sum'] == Decimal('-0.1')


@pytest.mark.django_db(transaction=True)
def test_get_partner_balance():
    with pytest.raises(django.http.response.Http404):
        assert get_partner_balance(999)

    partner = PartnerFactory()
    assert partner.balance == get_partner_balance(partner.id)

    change_partner_balance(partner_id=partner.id, amount=Decimal('0.1'))
    assert get_partner_balance(partner.id) == Decimal('0.1')

    change_partner_balance(partner_id=partner.id, amount=Decimal('-0.2'))
    assert get_partner_balance(partner.id) == Decimal('-0.1')

    transactions_sum = sum([t.amount for t in Transaction.objects.filter(partner_id=partner.id)])
    assert get_partner_balance(partner.id) == transactions_sum

    # yesterday transactions
    change_partner_balance(partner.id, Decimal('-0.1'), date=timezone.now() - timedelta(days=1))
    assert get_partner_balance(partner.id) != Decimal('-0.1')
    assert get_partner_balance(partner.id, date=timezone.now() - timedelta(days=1)) == Decimal('-0.1')


########################################## db optimization ##########################################

@pytest.mark.django_db(transaction=True)
def test_update_aggregated_transaction():
    partner = PartnerFactory()

    # do not create aggregate transaction for today
    date = timezone.now()
    assert not update_aggregated_transaction(partner.id, Decimal('9.99'), date)

    date = timezone.now() - timedelta(hours=24)
    begining_of_the_day = date.replace(hour=0, minute=0, second=0, microsecond=0)
    assert update_aggregated_transaction(partner.id, Decimal('19.99'), date)
    assert Partner.objects.get(pk=partner.id).aggregated_transaction.filter(
        date=begining_of_the_day).first().amount == Decimal('19.99')

    date = timezone.now() - timedelta(hours=24)
    begining_of_the_day = date.replace(hour=0, minute=0, second=0, microsecond=0)
    assert update_aggregated_transaction(partner.id, Decimal('19.99'), date)
    assert Partner.objects.get(pk=partner.id).aggregated_transaction.filter(
        date=begining_of_the_day).first().amount == Decimal('19.99')*2


@pytest.mark.django_db(transaction=True)
def test_change_partner_balance_ag():
    # partner does not exits
    with pytest.raises(django.http.response.Http404):
        change_partner_balance_ag(999, Decimal('0.1'))

    partner = PartnerFactory()
    change_partner_balance_ag(partner.id, Decimal('0.1'))

    assert Partner.objects.get(pk=partner.id).balance == Decimal('0.1')

    # now balance should be 0
    change_partner_balance_ag(partner.id, Decimal('-0.1'), date=timezone.now() - timedelta(days=1))
    partner = Partner.objects.get(pk=partner.id)
    assert partner.balance == Decimal('0')
    assert partner.partner_transaction.values('amount').aggregate(Sum('amount'))['amount__sum'] == 0

    # yesterday balance should be -0.1
    yesterday_transactions = partner.partner_transaction.filter(date__lte=timezone.now() - timedelta(days=1))
    assert yesterday_transactions.values('amount').aggregate(Sum('amount'))['amount__sum'] == Decimal('-0.1')


@pytest.mark.django_db(transaction=True)
def test_get_partner_balance_ag():
    with pytest.raises(django.http.response.Http404):
        assert get_partner_balance_ag(999)

    partner = PartnerFactory()
    assert partner.balance == get_partner_balance_ag(partner.id)

    for x in range(5):
        change_partner_balance_ag(partner.id, Decimal('1.0'), date=timezone.now()-timedelta(days=x))
    transactions_sum = sum([t.amount for t in Transaction.objects.filter(partner_id=partner.id)])
    assert get_partner_balance_ag(partner.id) == transactions_sum

    # 2 days ago transactions and 1 day ago balance
    change_partner_balance(partner.id, Decimal('-1'), date=timezone.now() - timedelta(days=2))
    assert get_partner_balance_ag(partner.id, date=timezone.now() - timedelta(days=1)) == \
           sum([t.amount for t in AggregatedTransactions.objects.filter(partner_id=partner.id)])

    # check for time in future
    change_partner_balance_ag(partner.id, Decimal('-11.0'), date=timezone.now() + timedelta(hours=3))
    transactions_sum = sum([t.amount for t in Transaction.objects.filter(partner_id=partner.id)])
    assert get_partner_balance_ag(partner.id) == transactions_sum


@pytest.mark.django_db(transaction=True)
def test_partner_transaction_view(client):
    res = client.get(reverse('transaction_view', kwargs={'partner_id': 1}))
    assert res.status_code == 404

    partner = PartnerFactory()

    res = client.get(reverse('transaction_view', kwargs={'partner_id': partner.id}))
    assert res.status_code == 200
    assert json.loads(res.content.decode()) == []

    transactions = [t for t in TransactionFactory.create_batch(5, partner=partner)]
    res = client.get(reverse('transaction_view', kwargs={'partner_id': partner.id}))
    content = json.loads(res.content.decode())
    assert res.status_code == 200
    assert len(content) == 5


@pytest.mark.django_db(transaction=True)
def test_partner_get_balance_view(client):
    partner = PartnerFactory()
    res = client.get(reverse('balance_view', kwargs={'partner_id': partner.id}))
    content = json.loads(res.content.decode())
    assert res.status_code == 200
    assert 'balance' in content.keys()

    current_balance = content['balance']

    data = {'amount': -10.1}
    res = client.post(reverse('balance_view', kwargs={'partner_id': partner.id}), data=data)
    assert res.status_code == 200
    content = json.loads(res.content.decode())

    res = client.get(reverse('balance_view', kwargs={'partner_id': partner.id}))
    content = json.loads(res.content.decode())
    assert res.status_code == 200
    assert Decimal(content['balance']) == Decimal('-10.1')

@pytest.mark.django_db(transaction=True)
def test_partner_change_balance_view(client):
    partner = PartnerFactory()
    data = {'amount': -5, 'date': '2017-03-16'}
    res = client.post(reverse('balance_view', kwargs={'partner_id': partner.id}), data=data)
    assert res.status_code == 200
    content = json.loads(res.content.decode())
    assert content['status'] == 'ok'

    res = client.get(reverse('balance_view', kwargs={'partner_id': partner.id}))
    content = json.loads(res.content.decode())
    assert res.status_code == 200
    assert Decimal(content['balance']) == Decimal('-5')

    # before 1st transaction
    data = {'date': '2016-03-16'}
    res = client.get(reverse('balance_view', kwargs={'partner_id': partner.id}), data=data)
    content = json.loads(res.content.decode())
    assert res.status_code == 200
    assert Decimal(content['balance']) == Decimal('0')
