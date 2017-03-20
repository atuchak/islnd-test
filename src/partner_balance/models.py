from django.db import models


class Partner(models.Model):
    balance = models.DecimalField(decimal_places=4, max_digits=32)

    def __str__(self):
        return 'Partner {0}'.format(str(self.id))


class Transaction(models.Model):
    partner = models.ForeignKey(Partner, related_name='partner_transaction')
    amount = models.DecimalField(decimal_places=4, max_digits=32)
    date = models.DateTimeField()

    class Meta:
        index_together = [('partner', 'date')]

    def __str__(self):
        return '{0} partner: {1}'.format(str(self.id), str(self.partner_id))


class AggregatedTransactions(models.Model):
    partner = models.ForeignKey(Partner, related_name='aggregated_transaction')
    amount = models.DecimalField(decimal_places=4, max_digits=32)
    date = models.DateTimeField()

    class Meta:
        index_together = [('partner', 'date')]

    def __str__(self):
        return '{0} partner: {1} - {2}'.format(str(self.id), str(self.partner_id), str(self.date))
