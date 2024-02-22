# Generated by Django 5.0.1 on 2024-02-22 11:24

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
        ('transactions', '0003_remove_transfer_reciever_transfer_receiver'),
    ]

    operations = [
        migrations.AlterField(
            model_name='transfer',
            name='receiver',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='receiver', to='accounts.userbankaccount'),
        ),
    ]
