from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            "class": "mt-1 block w-full rounded-xl border-gray-300 p-2 focus:ring-2 focus:ring-blue-600 focus:border-blue-600",
            "placeholder": "Correo electrónico"
        })
    )

    class Meta:
        model = User
        fields = ("username", "email", "first_name", "last_name", "password1", "password2")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Aplica Tailwind a todos los campos
        for field_name, field in self.fields.items():
            field.widget.attrs.update({
                "class": "mt-1 block w-full rounded-xl border-gray-300 p-2 focus:ring-2 focus:ring-blue-600 focus:border-blue-600",
                "placeholder": field.label
            })