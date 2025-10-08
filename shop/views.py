# from django.shortcuts import render

# # Create your views here.


from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.db.models import Q
from .models import Product, Category, Brand, Cart, CartItem, Order, OrderItem
import uuid

def get_cart(request):
    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user)
    else:
        session_key = request.session.session_key
        if not session_key:
            request.session.create()
            session_key = request.session.session_key
        cart, created = Cart.objects.get_or_create(session_key=session_key)
    return cart

def index(request):
    featured_products = Product.objects.filter(in_stock=True)[:8]
    men_products = Product.objects.filter(gender='M', in_stock=True)[:4]
    women_products = Product.objects.filter(gender='W', in_stock=True)[:4]
    
    context = {
        'featured_products': [],
        'men_products': [],
        'women_products': [],
    }
    return render(request, 'index.html', context)

def product_list(request):
    category_slug = request.GET.get('category')
    brand_slug = request.GET.get('brand')
    gender = request.GET.get('gender')
    query = request.GET.get('q')
    
    products = Product.objects.filter(in_stock=True)
    
    if category_slug:
        products = products.filter(category__slug=category_slug)
    
    if brand_slug:
        products = products.filter(brand__slug=brand_slug)
    
    if gender:
        products = products.filter(gender=gender)
    
    if query:
        products = products.filter(
            Q(name__icontains=query) | 
            Q(description__icontains=query) |
            Q(brand__name__icontains=query)
        )
    
    categories = Category.objects.all()
    brands = Brand.objects.all()
    
    context = {
        'products': products,
        'categories': categories,
        'brands': brands,
        'selected_category': category_slug,
        'selected_brand': brand_slug,
        'selected_gender': gender,
        'query': query,
    }
    return render(request, 'product_list.html', context)

def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug)
    related_products = Product.objects.filter(
        category=product.category
    ).exclude(id=product.id)[:4]
    
    context = {
        'product': product,
        'related_products': related_products,
    }
    return render(request, 'product_detail.html', context)

def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart = get_cart(request)
    
    cart_item, created = CartItem.objects.get_or_create(
        cart=cart,
        product=product,
        defaults={'quantity': 1}
    )
    
    if not created:
        cart_item.quantity += 1
        cart_item.save()
    
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'success': True, 'message': 'Product added to cart'})
    
    return redirect('cart')

def remove_from_cart(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id)
    cart_item.delete()
    
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'success': True, 'message': 'Product removed from cart'})
    
    return redirect('cart')

def update_cart(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id)
    quantity = int(request.POST.get('quantity', 1))
    
    if quantity > 0:
        cart_item.quantity = quantity
        cart_item.save()
    else:
        cart_item.delete()
    
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'success': True, 'message': 'Cart updated'})
    
    return redirect('cart')

def cart_view(request):
    cart = get_cart(request)
    
    context = {
        'cart': cart,
    }
    return render(request, 'cart.html', context)

def checkout(request):
    cart = get_cart(request)
    
    if request.method == 'POST':
        # Process the order
        order = Order.objects.create(
            user=request.user if request.user.is_authenticated else None,
            first_name=request.POST.get('first_name'),
            last_name=request.POST.get('last_name'),
            email=request.POST.get('email'),
            address=request.POST.get('address'),
            city=request.POST.get('city'),
            postal_code=request.POST.get('postal_code'),
            country=request.POST.get('country'),
            total_amount=cart.total_price
        )
        
        for item in cart.items.all():
            OrderItem.objects.create(
                order=order,
                product=item.product,
                price=item.product.discount_price if item.product.is_on_sale else item.product.price,
                quantity=item.quantity
            )
        
        # Clear the cart
        cart.items.all().delete()
        
        return render(request, 'order_confirmation.html', {'order': order})
    
    context = {
        'cart': cart,
    }
    return render(request, 'checkout.html', context)