from django.shortcuts import render,redirect,get_object_or_404

# Create your views here.
from django.views.generic import CreateView,ListView,View,FormView
from django.contrib.auth.mixins import LoginRequiredMixin 

from .models import Transaction,UserBankAccount
from .forms import DepositForm,LoanRequestForm,WithdrawForm,TransferForm
from .constants import DEPOSIT,WITHDRAWAL,LOAN_PAID,LOAN,SEND,RECEIVE
from django.http import HttpResponse

from django.contrib import messages 
from datetime import datetime
from django.db.models import Sum
from django.urls import reverse_lazy

from .models import Bank

from django.core.mail import EmailMessage,EmailMultiAlternatives
from django.template.loader import render_to_string

# ei view ke inherit kore amra deposite , withdraw,loan request er kaj korbo 

def send_transaction_email(user,amount,subject,template):
        message = render_to_string(template,{
            'user':user,
            'amount':amount, 
        })
        send_email = EmailMultiAlternatives(subject,'',to=[user.email])
        send_email.attach_alternative(message,"text/html")
        send_email.send()
        
class TransactionCreateMixin(LoginRequiredMixin, CreateView):
    template_name = 'transactions/transaction_form.html'
    model = Transaction
    title = ''
    success_url = reverse_lazy('transaction_report')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update({
            'account': self.request.user.account
        })
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs) 
        context.update({
            'title': self.title
        })

        return context

class DepositMoneyView(TransactionCreateMixin):
    form_class = DepositForm
    title = 'Deposit Form'

    def get_initial(self):
        initial = {'transaction_type': DEPOSIT}
        return initial

    def form_valid(self, form):
        amount = form.cleaned_data.get('amount')
        account = self.request.user.account
        account.balance += amount
        
        # Check if the deposit amount is greater than the available balance
        if amount > account.balance:
            messages.error(
                self.request,
                f'Deposit amount ({amount}) is greater than available balance ({account.balance})'
            )
            return self.form_invalid(form)

        account.save(
            update_fields=['balance']
        )

        messages.success(
            self.request,
            f'{"{:,.2f}".format(float(amount))}$ was deposited to your account successfully'
        )
        send_transaction_email(self.request.user,amount,"Deposite Message","transactions/deposit_email.html")
        return super().form_valid(form)


class WithdrawMoneyView(TransactionCreateMixin):
    form_class = WithdrawForm
    title = 'Withdraw Money'

    def get_initial(self):
        initial = {'transaction_type': WITHDRAWAL}
        return initial

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['account'] = self.request.user.account
        return kwargs

    def form_valid(self, form):
        amount = form.cleaned_data.get('amount')

        bank = Bank.objects.get(name="mamar_bank")
        
        if bank.is_bankrupt is True:
            messages.error(self.request, "Bank has gone bankrupt.")
            return redirect("home")

        # Check if the withdrawal amount is greater than the available balance
        
        if amount > self.request.user.account.balance:
            messages.error(
                self.request,
                f'Withdrawal amount ({amount}) is greater than available balance ({self.request.user.account.balance})'
            )
            return self.form_invalid(form)

        self.request.user.account.balance -= amount
        self.request.user.account.save(update_fields=['balance'])

        messages.success(
            self.request,
            f'Successfully withdrawn {"{:,.2f}".format(float(amount))}$ from your account'
        )
        send_transaction_email(self.request.user,amount,"Withdrawal Message","transactions/withdrawal_email.html")
        return super().form_valid(form)

class LoanRequestView(TransactionCreateMixin):
    form_class = LoanRequestForm
    title = 'Request For Loan'

    def get_initial(self):
        initial = {'transaction_type': LOAN}
        return initial

    def form_valid(self, form):
        amount = form.cleaned_data.get('amount')
        current_loan_count = Transaction.objects.filter(
            account=self.request.user.account,transaction_type=3,loan_approve=True).count()
        if current_loan_count >= 3:
            return HttpResponse("You have cross the loan limits")
        
        messages.success(
            self.request,
            f'Loan request for {"{:,.2f}".format(float(amount))}$ submitted successfully'
        )
        send_transaction_email(self.request.user,amount,"Loan Request Message","transactions/loan_email.html")
        return super().form_valid(form)

class TransactionReportView(LoginRequiredMixin, ListView):
    template_name = 'transactions/transaction_report.html'
    model = Transaction
    balance = 0 # filter korar pore ba age amar total balance ke show korbe
    context_object_name = 'report_list'
    def get_queryset(self):
        queryset = super().get_queryset().filter(
            account=self.request.user.account
        )
        start_date_str = self.request.GET.get('start_date')
        end_date_str = self.request.GET.get('end_date')
        
        if start_date_str and end_date_str:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            
            queryset = queryset.filter(timestamp__date__gte=start_date, timestamp__date__lte=end_date)
            self.balance = Transaction.objects.filter(
                timestamp__date__gte=start_date, timestamp__date__lte=end_date
            ).aggregate(Sum('amount'))['amount__sum']
        else:
            self.balance = self.request.user.account.balance
       
        return queryset.distinct() # unique queryset hote hobe
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'account': self.request.user.account
        })

        return context
    
    
class PayLoanView(LoginRequiredMixin, View):
    def get(self, request, loan_id):
        loan = get_object_or_404(Transaction, id=loan_id)
        print(loan)
        if loan.loan_approve:
            user_account = loan.account
                # Reduce the loan amount from the user's balance
                # 5000, 500 + 5000 = 5500
                # balance = 3000, loan = 5000
            if loan.amount < user_account.balance:
                user_account.balance -= loan.amount
                loan.balance_after_transaction = user_account.balance
                user_account.save()
                loan.loan_approved = True
                loan.transaction_type = LOAN_PAID
                loan.save()
                return redirect('loan_list')
            else:
                messages.error(
            self.request,
            f'Loan amount is greater than available balance'
        )

        return redirect('loan_list')


class LoanListView(LoginRequiredMixin,ListView):
    model = Transaction
    template_name = 'transactions/loan_request.html'
    context_object_name = 'loans' # loan list ta ei loans context er moddhe thakbe
    
    def get_queryset(self):
        user_account = self.request.user.account
        queryset = Transaction.objects.filter(account=user_account,transaction_type=3)
        return queryset
        
class TransferMoneyView(CreateView, LoginRequiredMixin):
    form_class = TransferForm
    template_name = 'transactions/transfer_money.html'
    success_url = reverse_lazy('transaction_report')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update({
            'account': self.request.user.account
        })
        return kwargs
    
    def form_valid(self, form):
        amount = form.cleaned_data.get('amount')
        receiver = form.cleaned_data.get('receiver')
        
        account = self.request.user.account
        sender = self.request.user  
        
        if receiver.account == account:
            messages.error(self.request, 'You cannot transfer money to your own account')

        if amount < account.balance:
            account.balance -= amount
            receiver.account.balance += amount
            account.save(update_fields=['balance'])
            receiver.account.save(update_fields=['balance'])
            
            
            sender_transaction = Transaction.objects.create(
                account=account,
                amount=amount, 
                balance_after_transaction=account.balance,
                transaction_type=SEND, 
                sender = account,
                receiver = receiver.account
            )

            receiver_transaction = Transaction.objects.create(
                account=receiver.account,
                amount=amount,
                balance_after_transaction=receiver.account.balance,
                transaction_type=RECEIVE,
                sender = account,
                receiver = receiver.account
            )
            sender_transaction.save()
            receiver_transaction.save()
            messages.success(
                self.request,
                f'{"{:,.2f}".format(float(amount))}$ was transferred from your account successfully'  
            )
            print(receiver)
            print(self.request.user)
            send_transaction_email(sender, amount, "Transfer Message", "transactions/transfer_email.html")
            send_transaction_email(receiver, amount, "Transfer Message", "transactions/transfer_email.html")
            return super().form_valid(form)
        else:
            messages.error(self.request, "Transfer amount more than account balance.")
            return redirect("home")
    
        
        
    