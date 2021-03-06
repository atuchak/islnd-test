# -*- coding: utf-8 -*-
# Generated by Django 1.10.6 on 2017-03-20 00:02
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='AggregatedTransactions',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', models.DecimalField(decimal_places=4, max_digits=32)),
                ('date', models.DateTimeField()),
            ],
        ),
        migrations.CreateModel(
            name='Partner',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('balance', models.DecimalField(decimal_places=4, max_digits=32)),
            ],
        ),
        migrations.CreateModel(
            name='Transaction',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', models.DecimalField(decimal_places=4, max_digits=32)),
                ('date', models.DateTimeField()),
                ('partner', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='partner_transaction', to='partner_balance.Partner')),
            ],
        ),
        migrations.AddField(
            model_name='aggregatedtransactions',
            name='partner',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='aggregated_transaction', to='partner_balance.Partner'),
        ),
        migrations.AlterIndexTogether(
            name='aggregatedtransactions',
            index_together=set([('partner', 'date')]),
        ),
    ]
