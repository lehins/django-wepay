from django.core.urlresolvers import reverse
from django.http import Http404, HttpResponseNotAllowed, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404

from django_wepay import DjangoWePay
from django_wepay.models import WPUser, WPAccount, WPCheckout, WPPreapproval
from django_wepay.signals import *

from wepay.exceptions import WePayError


@csrf_exempt
def ipn_user(request):
    if request.method != "POST":
        return HttpResponseNotAllowed(['POST',])
    if 'user_id' in request.POST:
        user = get_object_or_404(WPUser, pk=request.POST['user_id'])
        ipn_received.send(sender=WPUser, request=request, instance=user)
        d_wepay = DjangoWePay(user=user)
        try:
            response = d_wepay.user_get()
            user.update(**response)
            return HttpResponse("Update successfull.")
        except WePayError, e:
            if e.type == 'access_denied' or e.type == 'invalid_client':
                user_deleted.send(sender=WPUser, instance=user)
                user.delete()
                return HttpResponse("Removal successfull.")
            return HttpResponse("Something went wrong. %s" % e, status=500)
    return HttpResponse("Not recognized or not implemented object IPN.", status=501)

@csrf_exempt
def ipn_account(request):
    if request.method != "POST":
        return HttpResponseNotAllowed(['POST',])
    if 'account_id' in request.POST:
        account = get_object_or_404(WPAccount, pk=request.POST['account_id'])
        ipn_received.send(sender=WPAccount, request=request, instance=account)
        d_wepay = DjangoWePay(account=account)
        try: 
            response = d_wepay.account_update_local(account)
        except WePayError, e:
            if e.type == 'access_denied':
                account.delete()
        return HttpResponse("Updated successfully.")
    return HttpResponse("Not recognized or not implemented object IPN.", status=501)

@csrf_exempt
def ipn_checkout(request):
    if request.method != "POST":
        return HttpResponseNotAllowed(['POST',])
    if 'checkout_id' in request.POST:
        checkout = get_object_or_404(WPCheckout, pk=request.POST['checkout_id'])
        ipn_received.send(sender=WPCheckout, request=request, instance=checkout)
        d_wepay = DjangoWePay(account=checkout.account)
        d_wepay.checkout_update_local(checkout)
        return HttpResponse("Updated successfully.")
    return HttpResponse("Not recognized or not implemented object IPN.", status=501)


@csrf_exempt
def ipn_preapproval(request):
    if request.method != "POST":
        return HttpResponseNotAllowed(['POST',])
    if 'preapproval_id' in request.POST:
        preapproval = get_object_or_404(
            WPPreapproval, pk=request.POST['preapproval_id'])
        ipn_received.send(
            sender=WPPreapproval, request=request, instance=preapproval)
        d_wepay = DjangoWePay(account=preapproval.account)
        d_wepay.preapproval_update_local(preapproval)
        return HttpResponse("Updated successfully.")
    return HttpResponse("Not recognized or not implemented object IPN.", status=501)


@csrf_exempt
def ipn_withdrawal(request):
    if request.method != "POST":
        return HttpResponseNotAllowed(['POST',])
    if 'withdrawal_id' in request.POST:
        withdrawal = get_object_or_404(
            WPWithdrawal, pk=request.POST['withdrawal_id'])
        ipn_received.send(sender=WPWithdrawal, request=request, instance=withdrawal)
        d_wepay = DjangoWePay(account=withdrawal.account)
        d_wepay.withdrawal_update_local(withdrawal)
        return HttpResponse("Updated successfully.")
    return HttpResponse("Not recognized or not implemented object IPN.", status=501)

def testing_callback(request):
    return HttpResponse("Success")
