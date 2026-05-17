from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import authenticate, get_user_model

UserModel = get_user_model()

class InscriptionForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ['email', 'password1', 'password2']

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not email:
            return email
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Cet email existe déjà.")
        return email.lower()

    def save(self, commit=True):
        user = super().save(commit=False)
        email = self.cleaned_data.get('email')
        if email:
            email_norm = email.lower()[:150]  # limite username à 150 chars
            user.username = email_norm
            user.email = email_norm
        if commit:
            user.save()
        return user

class EmailAuthenticationForm(AuthenticationForm):
    username = forms.EmailField(label="Email")

    error_messages = {
        'email_not_found': "Cet email n'existe pas.",
        'invalid_login': "Email ou mot de passe incorrect.",
        'inactive': "Ce compte est inactif.",
    }

    def clean(self):
        email = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')

        if not email:
            return super().clean()

        # vérifier existence de l'email
        try:
            user_obj = UserModel.objects.get(email__iexact=email)
        except UserModel.DoesNotExist:
            raise forms.ValidationError(self.error_messages['email_not_found'])

        # authentifier en utilisant username (votre signup met username = email)
        self.user_cache = authenticate(self.request, username=user_obj.username, password=password)
        if self.user_cache is None:
            raise forms.ValidationError(self.error_messages['invalid_login'])

        self.confirm_login_allowed(self.user_cache)
        return self.cleaned_data
