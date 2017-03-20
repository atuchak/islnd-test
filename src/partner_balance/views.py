from dateutil.parser import parse
from django.core import serializers
from django.db import IntegrityError
from django.db import transaction
from django.db.models import F
from django.http import HttpResponse
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.utils import timezone

# Create your views here.
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View

from partner_balance.forms import PartnerGetBalanceForm, PartnerChangeBalanceForm
from partner_balance.models import Partner, Transaction, AggregatedTransactions


@method_decorator(csrf_exempt, name='dispatch')
class PartnerBalanceView(View):
    http_method_names = ['get', 'post']

    # get balance
    def get(self, request, partner_id):
        form = PartnerGetBalanceForm(request.GET)

        if form.is_valid():
            date = form.cleaned_data['date']
            balance = get_partner_balance_ag(partner_id, date)
            return JsonResponse({'partner_id': partner_id, 'balance': balance})
        elif 'date' not in request.GET:
            balance = get_partner_balance_ag(partner_id)
            return JsonResponse({'partner_id': partner_id, 'balance': balance})
        else:
            return JsonResponse({'errors': str(form.errors)})

    # change balance
    def post(self, request, partner_id):
        form = PartnerChangeBalanceForm(request.POST)

        if form.is_valid():
            amount = form.cleaned_data['amount']
            date = form.cleaned_data['date']

            change_partner_balance_ag(partner_id, amount=amount, date=date)
            return JsonResponse({'status': 'ok'})

        else:
            return JsonResponse({'errors': str(form.errors)})


class PartnerTransactionView(View):
    http_method_names = ['get']

    def serializer(self):
        return serializers.serialize('json', self.data)

    def get(self, request, partner_id):
        self.data = get_object_or_404(Partner, pk=partner_id).partner_transaction.all()

        return HttpResponse(self.serializer(), content_type='application/json')



def get_partner_balance(partner_id, date=None):
    if not date:
        partner = get_object_or_404(Partner, pk=partner_id)
        return partner.balance
    else:
        queryset = get_object_or_404(Partner, pk=partner_id).partner_transaction

        # naive implementation (python or db sum)
        queryset = queryset.filter(date__lte=date).values('amount')
        transactions = [t['amount'] for t in queryset]
        return sum(transactions)


@transaction.atomic
def change_partner_balance(partner_id, amount, date=None):
    if not date:
        date = timezone.now()
    partner = get_object_or_404(Partner, pk=partner_id)

    try:
        with transaction.atomic():
            Transaction.objects.create(partner=partner, amount=amount, date=date)
            partner.balance = F('balance') + amount
            partner.save()
    except IntegrityError:
        raise


########################################## db optimization ##########################################

# update only prev days aggregate
def update_aggregated_transaction(partner_id, amount, date):
    today = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)

    # do not perform update for current day
    if date < today:
        begining_of_the_day = date.replace(hour=0, minute=0, second=0, microsecond=0)

        transaction = AggregatedTransactions.objects.filter(partner_id=partner_id, date=begining_of_the_day).first()

        if transaction:
            # update if exists
            transaction.amount = F('amount') + amount
            transaction.save()
        else:
            # create if not exists
            transaction = AggregatedTransactions.objects
            transaction = transaction.create(partner_id=partner_id, amount=amount, date=begining_of_the_day)

        return transaction


@transaction.atomic
def change_partner_balance_ag(partner_id, amount, date=None):
    if not date:
        date = timezone.now()
    partner = get_object_or_404(Partner, pk=partner_id)

    try:
        with transaction.atomic():
            Transaction.objects.create(partner=partner, amount=amount, date=date)
            partner.balance = F('balance') + amount
            partner.save()

            update_aggregated_transaction(partner_id, amount, date=date)
    except IntegrityError:
        raise


def get_partner_balance_ag(partner_id, date=None):
    if not date:
        partner = get_object_or_404(Partner, pk=partner_id)
        return partner.balance
    else:
        queryset = get_object_or_404(Partner, pk=partner_id).partner_transaction

        # aggrerated implementation
        today = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        begining_of_the_day = date.replace(hour=0, minute=0, second=0, microsecond=0)

        queryset = queryset.filter(date__gte=begining_of_the_day, date__lte=date).values('amount')
        transactions = [t['amount'] for t in queryset]
        today_sum = sum(transactions)

        queryset_ag = get_object_or_404(Partner, pk=partner_id).aggregated_transaction
        queryset_ag = queryset_ag.filter(date__lt=begining_of_the_day).values('amount')
        transactions = [t['amount'] for t in queryset_ag]
        ag_sum = sum(transactions)

        return today_sum + ag_sum

