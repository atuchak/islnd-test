from django import forms


class PartnerGetBalanceForm(forms.Form):
    date = forms.DateTimeField(required=False)


class PartnerChangeBalanceForm(forms.Form):
    date = forms.DateTimeField(required=False)
    amount = forms.DecimalField(max_digits=32)
