import dataclasses
from itertools import product
from queue import PriorityQueue
from django.shortcuts import render, redirect
from .models import *
from django.http import JsonResponse
from django.contrib.auth.forms import UserCreationForm
import json
from django.http import HttpResponse
from django.forms import inlineformset_factory
import datetime
from .forms import OrderForm, CreateUserForm
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required

# Views
def registerPage(request):
     if request.user.is_authenticated:
          return redirect('store')
     else:
          form = CreateUserForm()

     if request.method == "POST":
          form = CreateUserForm(request.POST)
          if form.is_valid():
               form.save()
               user = form.cleaned_data.get('username')
               messages.success(request, 'Account was created for' + user)

               return redirect('login')

     context = {'form': form}
     return render(request, 'store/register.html', context)

def loginPage(request):
     if request.method == 'POST':
          username = request.POST.get('username')
          password = request.POST.get('password')
          
          user= authenticate(request, username=username, password=password)

          if user is not None:
               login(request, user)
               return redirect('store')
          else:
               messages.info(request, 'Username OR password is incorrect')
               
     context={}
     return render(request, 'store/login.html', context)

def logoutUser(request):
     logout(request)
     return redirect('login')

login_required(login_url='login')
def mainpage(request):
     if request.user.is_authenticated:
          customer=request.user.customer
          order, created = Order.objects.get_or_create(customer=customer, complete=False)
          items = order.orderitem_set.all()
          cartItems = order.get_cart_items

     else:
          items = []
          order={'get_cart_total':0, 'get_cart_items':0, 'shipping':False}
          cartItems = order['get_cart_items']
     context = {'cartItems':cartItems}
     return render(request, 'store/mainpage.html', context)


login_required(login_url='login')
def store(request):

     if request.user.is_authenticated:
          customer=request.user.customer
          order, created = Order.objects.get_or_create(customer=customer, complete=False)
          items = order.orderitem_set.all()
          cartItems = order.get_cart_items
     else:
          items = []
          order={'get_cart_total':0, 'get_cart_items':0, 'shipping':False}
          cartItems = order['get_cart_items']
     products = Product.objects.all()
     context = {'products': products, 'cartItems':cartItems}
     return render(request, 'store/store.html', context)

login_required(login_url='login')
def cart(request):

     if request.user.is_authenticated:
          customer=request.user.customer
          order, created = Order.objects.get_or_create(customer=customer, complete=False)
          items = order.orderitem_set.all()
          cartItems = order.get_cart_items
          
     else:
          try:
               cart = json.loads(request.COOKIES['cart'])
          except:
               cart = {}
          print('Cart:', cart)
          items = []
          order={'get_cart_total':0, 'get_cart_items':0, 'shipping':False}
          cartItems = order['get_cart_items']

          for i in cart:
               cartItems += cart[i]["quantity"]

               product = Product.objects.get(id=i)
               total = (product.price * cart[i]["quantity"])

               order['get_cart_total'] += total
               order['get_cart_total'] += cart[i]["quantity"]

               item = {
                    'product':{
                         'id':product.id,
                         'name':product.name,
                         'price':product.price,
                         'imageURL':product.imageURL,
                         },
                    'quantity':cart[i]["quantity"],
                    'get_total':total
               }
               items.append(item)

               if product.digital == False:
                    order['shipping'] = True

     context = {'items':items, 'order':order, 'cartItems':cartItems}
     return render(request, 'store/cart.html', context)

login_required(login_url='login')
def checkout(request):
      if request.user.is_authenticated:
          customer=request.user.customer
          order, created = Order.objects.get_or_create(customer=customer, complete=False)
          items = order.orderitem_set.all()
          cartItems = order.get_cart_items

      else:
          items = []
          order={'get_cart_total':0, 'get_cart_items':0, 'shipping':False}
          cartItems = order['get_cart_items']
      context = {'items':items, 'order':order, 'cartItems':cartItems}
      return render(request, 'store/checkout.html', context)
      

login_required(login_url='login')     
def updateItem(request):
     data = json.loads(request.body)
     productId = data['productId']
     action = data['action']

     print('action:', action)
     print('productId:', productId)

     customer = request.user.customer
     product = Product.objects.get(id=productId)
     order, created = Order.objects.get_or_create(customer=customer, complete=False)

     orderItem, created = OrderItem.objects.get_or_create(order=order, product=product)

     if action == 'add':
          orderItem.quantity=(orderItem.quantity + 1)
     elif action == 'remove':
           orderItem.quantity=(orderItem.quantity - 1)

     orderItem.save()

     if orderItem.quantity <= 0:
          orderItem.delete()

     return JsonResponse('Item was added', safe=False)

login_required(login_url='login')
def processOrder(request):
     transaction_id = datetime.datetime.now().timestamp()
     data =json.loads(request.body)

     if request.user.is_authenticated:
          customer = request.user.customer
          order, created = Order.objects.get_or_create(customer=customer, complete=False)
          total = float(data['form']['total'])
          order.transaction_id = transaction_id

          if total == order.get_cart_total:
               order.complete = True
          order.save()

          if order.shipping == True:
               ShippingAddress.objects.create(
                    customer=customer,
                    order=order,
                    address=data['shipping']['address'],
                    city=data['shipping']['city'],
                    state=data['shipping']['state'],
                    zipcode=data['shipping']['zipcode'],
               )

     else:
          print('User is not logged in...')
     return JsonResponse('Payment complete!', safe=False)