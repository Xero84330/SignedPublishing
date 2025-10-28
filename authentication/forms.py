from django import forms
from django.contrib.auth.forms import UserCreationForm as BaseUserCreationForm, UserChangeForm as BaseUserChangeForm
from .models import User

class UserUpdateForm(BaseUserChangeForm):
    email_verified = forms.BooleanField(
        required=False,
        widget=forms.HiddenInput(),
        initial=False
    )

    class Meta:
        model = User
        fields = [
            'username',
            'email',
            'bio',
            'age',
            'gender',
            'country',
            'date_of_birth',
            'profile_picture',
        ]
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 3}),
            'age': forms.NumberInput(attrs={'min': 0}),
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
            'gender': forms.Select(attrs={'class': 'rounded-lg border border-amber-900'}),
        }


class UserCreationForm(BaseUserCreationForm):
    class Meta:
        model = User
        fields = (
            'username',
            'email',
            'bio',
            'age',
            'gender',
            'country',
            'date_of_birth',
            'profile_picture',
            'password1',
            'password2',
        )
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 3}),
            'age': forms.NumberInput(attrs={'min': 0}),
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
            'gender': forms.Select(attrs={'class': 'rounded-lg border border-amber-900'}),
        }

# -----------------------
# PASSWORD RESET FLOW
# -----------------------

base_input_class = (
    "w-full px-4 py-3 mt-1 border rounded-xl border-amber-900 "
    "focus:outline-none focus:ring-2 focus:ring-orange-500 "
    "shadow-sm placeholder-amber-900"
)


class ForgotPasswordForm(forms.Form):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': base_input_class,
            'placeholder': 'Enter your registered email',
        })
    )


class OTPVerificationForm(forms.Form):
    otp = forms.CharField(
        max_length=6,
        widget=forms.TextInput(attrs={
            'class': base_input_class,
            'placeholder': 'Enter 6-digit OTP',
        })
    )


class ResetPasswordForm(forms.Form):
    new_password = forms.CharField(
        min_length=8,
        widget=forms.PasswordInput(attrs={
            'class': base_input_class,
            'placeholder': 'New password',
        })
    )

    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': base_input_class,
            'placeholder': 'Confirm new password',
        })
    )

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("new_password")
        confirm = cleaned_data.get("confirm_password")

        if password and confirm and password != confirm:
            raise forms.ValidationError("Passwords do not match.")

        return cleaned_data
