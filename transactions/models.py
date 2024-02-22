from django.db import models
from accounts.models import UserBankAccount
# Create your models here.
from .constants import TRANSACTION_TYPE
from django.contrib.auth.models import User

class Bank(models.Model):
    name = models.CharField(max_length=100,default='mamar_bank')
    is_bankrupt = models.BooleanField(default=False)
class Transaction(models.Model):
    account = models.ForeignKey(UserBankAccount, related_name = 'transactions', on_delete = models.CASCADE) # ekjon user er multiple transactions hote pare
    
    amount = models.DecimalField(decimal_places=2, max_digits = 12)
    balance_after_transaction = models.DecimalField(decimal_places=2, max_digits = 12)
    transaction_type = models.IntegerField(choices=TRANSACTION_TYPE, null = True)
    timestamp = models.DateTimeField(auto_now_add=True)
    loan_approve = models.BooleanField(default=False)
    sender = models.ForeignKey(UserBankAccount, related_name='sended_transfers', on_delete=models.CASCADE, null=True, blank=True)
    receiver = models.ForeignKey(UserBankAccount, related_name='received_transfers', on_delete=models.CASCADE, null=True, blank=True)

    class Meta:
        ordering = ['timestamp'] 
        
        
class Transfer(models.Model):
    receiver = models.ForeignKey(User, related_name="receiver", on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    amount = models.DecimalField(decimal_places=2, max_digits=12)
    
    class Meta:
        ordering = ['timestamp']