from django.db import models
from django.contrib.auth.models import User


class CartItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='cart_items')
    product_id = models.IntegerField()  # fakestore product id
    title = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.URLField(blank=True, null=True)
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = ('user', 'product_id')

    def __str__(self):
        return f"{self.user.username} - {self.title} x{self.quantity}"
