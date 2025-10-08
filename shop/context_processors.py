from .models import Cart

def cart_items_count(request):
    if request.user.is_authenticated:
        try:
            cart = Cart.objects.get(user=request.user)
            count = cart.items.count()
        except Cart.DoesNotExist:
            count = 0
    else:
        session_key = request.session.session_key
        if session_key:
            try:
                cart = Cart.objects.get(session_key=session_key)
                count = cart.items.count()
            except Cart.DoesNotExist:
                count = 0
        else:
            count = 0
    
    return {'cart_items_count': count}