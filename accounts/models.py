from django.contrib.auth.models import User
from django.db import models
from products.models import Product
from django.db.models.signals import post_save
from django.dispatch import receiver

# ------------------------
# Profile
# ------------------------
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    profile_picture = models.ImageField(
        upload_to='profile_pics/', default='profile_pics/default.jpg'
    )
    favorite_shops = models.TextField(blank=True)
    favorite_items = models.TextField(blank=True)
    CURRENCY_CHOICES = [
        ('USD', 'USD'),
        ('LBP', 'LBP'),
    ]
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='USD')

    cart = models.ManyToManyField(Product, blank=True, related_name='in_carts')

    def __str__(self):
        return self.user.username


# Automatically create/update profile when user is created/updated
@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
    else:
        instance.profile.save()