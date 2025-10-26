from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from allauth.socialaccount.models import SocialAccount

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    profile_picture = models.ImageField(upload_to='profile_pics/', default='profile_pics/default.jpg')
    favorite_shops = models.TextField(blank=True)
    favorite_items = models.TextField(blank=True)
    CURRENCY_CHOICES = [
        ('USD', 'USD'),
        ('LBP', 'LBP'),
    ]
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='USD')


@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        profile = Profile.objects.create(user=instance)
        try:
            social_account = SocialAccount.objects.get(user=instance)
            extra_data = social_account.extra_data

            picture = extra_data.get('picture')
            if picture:
                # If you want to handle remote URLs, you need to download the image
                pass  # optional: handle Google picture
        except SocialAccount.DoesNotExist:
            pass
    else:
        instance.profile.save()
        
