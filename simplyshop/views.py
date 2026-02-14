from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from rest_framework import generics, permissions, status
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError

from .models import CartItem
from .serializers import UserSerializer, CartItemSerializer
from google.oauth2 import id_token
from google.auth.transport import requests
from django.conf import settings



# ---------- AUTH ----------

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.AllowAny]


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def login_view(request):
    username = request.data.get('username')
    password = request.data.get('password')

    if not username or not password:
        return Response({'detail': 'Username and password required.'},
                        status=status.HTTP_400_BAD_REQUEST)
    
    password = request.data.get("password")

    try:
        validate_password(password)
    except DjangoValidationError as e:
        return Response({"password": e.messages}, status=status.HTTP_400_BAD_REQUEST)


    user = authenticate(username=username, password=password)
    if not user:
        return Response({'detail': 'Invalid credentials.'},
                        status=status.HTTP_400_BAD_REQUEST)

    token, created = Token.objects.get_or_create(user=user)
    return Response({
        'token': token.key,
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
        }
    })


# ---------- CART ----------

@api_view(['GET'])
def get_cart(request):
    cart_items = CartItem.objects.filter(user=request.user)
    serializer = CartItemSerializer(cart_items, many=True)
    return Response(serializer.data)


@api_view(['POST'])
def add_to_cart(request):
    user = request.user
    data = request.data

    product_id = data.get('product_id')
    title = data.get('title')
    price = data.get('price')
    image = data.get('image')
    quantity = int(data.get('quantity', 1))

    if not product_id or not title or not price:
        return Response({'detail': 'Missing fields'},
                        status=status.HTTP_400_BAD_REQUEST)

    cart_item, created = CartItem.objects.get_or_create(
        user=user,
        product_id=product_id,
        defaults={
            'title': title,
            'price': price,
            'image': image,
            'quantity': quantity,
        }
    )
    if not created:
        cart_item.quantity += quantity
        cart_item.save()

    return Response(CartItemSerializer(cart_item).data,
                    status=status.HTTP_201_CREATED)


@api_view(['PATCH', 'DELETE'])
def update_cart_item(request, pk):
    try:
        cart_item = CartItem.objects.get(pk=pk, user=request.user)
    except CartItem.DoesNotExist:
        return Response({'detail': 'Item not found'},
                        status=status.HTTP_404_NOT_FOUND)

    if request.method == 'PATCH':
        quantity = request.data.get('quantity')
        if quantity is not None:
            cart_item.quantity = int(quantity)
            cart_item.save()
        return Response(CartItemSerializer(cart_item).data)

    if request.method == 'DELETE':
        cart_item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    
@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def google_login(request):
    id_token_str = request.data.get("id_token")

    if not id_token_str:
        return Response(
            {"detail": "Missing id_token"},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        # Verify token with Google
        idinfo = id_token.verify_oauth2_token(
            id_token_str,
            requests.Request(),
            settings.GOOGLE_CLIENT_ID,
        )

        email = idinfo.get("email")
        name = idinfo.get("name")

        if not email:
            return Response(
                {"detail": "Email not available"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get or create user
        user, created = User.objects.get_or_create(
            username=email,
            defaults={
                "email": email,
                "first_name": name or "",
            }
        )

        # Create DRF token
        token, _ = Token.objects.get_or_create(user=user)

        return Response({
            "token": token.key,
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
            }
        })

    except ValueError:
        return Response(
            {"detail": "Invalid Google token"},
            status=status.HTTP_401_UNAUTHORIZED
        )

