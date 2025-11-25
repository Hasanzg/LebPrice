from django import forms
from .models import Profile
from django.contrib.auth.models import User

class ProfileForm(forms.ModelForm):
    first_name = forms.CharField(required=False)
    last_name = forms.CharField(required=False)
    
    class Meta:
        model = Profile
        fields = ['profile_picture', 'favorite_shops', 'favorite_items', 'first_name', 'last_name']

class SettingsForm(forms.ModelForm):
    username = forms.CharField(max_length=150, required=True, label="Username")
    currency_preference = forms.ChoiceField(choices=[('USD','USD'), ('LBP','LBP')], label="Currency Preference")

    class Meta:
        model = Profile
        fields = ['currency_preference']

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user')
        super(SettingsForm, self).__init__(*args, **kwargs)
        self.fields['username'].initial = user.username
        self.user = user

    def save(self, commit=True):
        user = self.user
        user.username = self.cleaned_data['username']
        if commit:
            user.save()
            super(SettingsForm, self).save(commit=commit)
        return user


class UsernameUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username']
        
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Username'
        })
    
    def clean_username(self):
        username = self.cleaned_data.get('username')
        
        # Check if username is taken by another user
        if User.objects.filter(username=username).exclude(pk=self.user.pk).exists():
            raise forms.ValidationError("This username is already taken. Please choose another one.")
        
        # Additional validation (optional - similar to allauth)
        if len(username) < 3:
            raise forms.ValidationError("Username must be at least 3 characters long.")
        
        if not username.replace('_', '').replace('-', '').isalnum():
            raise forms.ValidationError("Username can only contain letters, numbers, hyphens, and underscores.")
        
        return username


class CurrencyUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['currency']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['currency'].widget.attrs.update({
            'class': 'form-control'
        })