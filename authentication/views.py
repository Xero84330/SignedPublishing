from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from .models import User, EmailOTP
from .forms import UserUpdateForm, ForgotPasswordForm, OTPVerificationForm, ResetPasswordForm
from django.urls import reverse 
import random
from django.http import JsonResponse
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from django.db import IntegrityError
from datetime import datetime, date


def update_profile(request):
    user = request.user

    if request.method == 'POST':
        form = UserUpdateForm(request.POST, request.FILES, instance=user)

        if form.is_valid():
            new_email = form.cleaned_data.get("email")
            
            # Safety: handle missing email field
            if not new_email:
                messages.error(request, "Email field cannot be empty.")
                return redirect('updateprofile')

            new_email = new_email.strip().lower()
            email_verified = request.POST.get("email_verified") == "1"

            # --- Email change validation ---
            if new_email != user.email:
                if User.objects.filter(email=new_email).exclude(pk=user.pk).exists():
                    messages.error(request, "This email is already registered with another account.")
                    return redirect('updateprofile')

                if not email_verified:
                    messages.error(request, "Please verify your new email before updating.")
                    return redirect('updateprofile')

            try:
                # Save form (updates all editable fields)
                updated_user = form.save(commit=False)

                # Handle safe manual email update
                if new_email != user.email:
                    updated_user.email = new_email

                # Save updated user info
                updated_user.save()

                messages.success(request, "Profile updated successfully!")

                # Logout if email changed
                if new_email != user.email:
                    logout(request)
                    return redirect('login')

                return redirect('home')

            except IntegrityError:
                messages.error(request, "Could not update profile due to a database error.")
                return redirect('updateprofile')

        else:
            # Show validation errors properly
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")

    else:
        form = UserUpdateForm(instance=user)

    return render(request, 'authentication/signup.html', { 
        'form': form,
        'user': user,
    })


def login_view(request):
    if request.method == "POST":
        email = request.POST.get("email")   # email instead of username
        password = request.POST.get("password")

        user_obj = authenticate(request, email=email, password=password)

        if user_obj is not None:
            login(request, user_obj)
            messages.success(request, f"Welcome {user_obj.username}")
            return redirect("/")
        else:
            messages.error(request, "Invalid email or password")
            return redirect("login")

    return render(request, "authentication/login.html")

def signup_view(request):
    if request.method == "POST":
        email = request.POST.get("email", "").strip().lower()
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm-password")
        bio = request.POST.get("bio", "")
        gender = request.POST.get("gender")
        country = request.POST.get("country")
        date_of_birth = request.POST.get("date_of_birth")
        age = request.POST.get("age")
        profile_picture = request.FILES.get("profile_picture")

        # --- Validation ---
        if not email or not username or not password or not confirm_password:
            messages.error(request, "Please fill all required fields.")
            return redirect("signup")

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already exists.")
            return redirect("signup")

        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return redirect("signup")

        # --- Validate Date of Birth ---
        dob_obj = None
        if date_of_birth:
            try:
                dob_obj = datetime.strptime(date_of_birth, "%Y-%m-%d").date()
                today = date.today()

                if dob_obj > today:
                    messages.error(request, "Date of birth cannot be in the future.")
                    return redirect("signup")

                age_calc = today.year - dob_obj.year - ((today.month, today.day) < (dob_obj.month, dob_obj.day))
                if age_calc < 13:
                    messages.error(request, "You must be at least 13 years old to create an account.")
                    return redirect("signup")

                age = age_calc  # Auto-fill calculated age if valid

            except ValueError:
                messages.warning(request, "Invalid date format for Date of Birth. Skipped.")
                dob_obj = None

        # --- Create User ---
        new_user = User.objects.create_user(
            email=email,
            username=username,
            password=password,
            bio=bio,
            gender=gender if gender else None,
            country=country if country else None,
            age=age if age else None,
        )

        # --- Save date_of_birth if valid ---
        if dob_obj:
            new_user.date_of_birth = dob_obj

        # --- Profile Picture ---
        if profile_picture:
            new_user.profile_picture = profile_picture

        new_user.save()

        messages.success(request, "Account created successfully! Please log in.")
        return redirect("login")

    return render(request, "authentication/signup.html")


def logout_view(request):
    if request.method == "POST":
        logout(request)
        messages.success(request, "Logged out successfully!")
    return redirect('home')


def verify_otp(request):
    if request.method == "POST":
        user = request.user
        code = request.POST.get("otp")
        otp_obj = EmailOTP.objects.filter(user=user, code=code, is_used=False).last()

        if otp_obj and not otp_obj.is_expired():
            otp_obj.is_used = True
            otp_obj.save()
            messages.success(request, "OTP verified successfully ✅")
            # Proceed with the next step (e.g. mark email as verified or allow password reset)
            return redirect("home")
        else:
            messages.error(request, "Invalid or expired OTP ❌")

    return render(request, "accounts/verify_otp.html")

def send_otp(request):
    if request.method == "POST":
        email = request.POST.get("email")
        purpose = request.POST.get("purpose", "verify")

        if not email:
            return JsonResponse({"success": False, "message": "Email is required."})

        otp = str(random.randint(100000, 999999))

        # ✅ Create OTP entry not tied to any user
        EmailOTP.objects.create(
            user=None,  # No user link at all
            code=otp,
            purpose=purpose,
            temp_email=email  # Add this field in your EmailOTP model if not already
        )

        send_mail(
            subject="Your Verification Code",
            message=f"Your OTP is {otp}. It expires in 10 minutes.",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
        )

        return JsonResponse({"success": True, "message": "OTP sent successfully!"})

    return JsonResponse({"success": False, "message": "Invalid request."})



# --- Verify OTP ---
def verify_email_otp(request):
    if request.method == "POST":
        email = request.POST.get("email")
        otp = request.POST.get("otp")

        otp_obj = EmailOTP.objects.filter(
            temp_email=email,  # match to email directly
            code=otp,
            is_used=False
        ).last()

        if otp_obj and not otp_obj.is_expired():
            otp_obj.is_used = True
            otp_obj.save()
            return JsonResponse({"success": True, "message": "OTP verified successfully!"})
        else:
            return JsonResponse({"success": False, "message": "Invalid or expired OTP."})

    return JsonResponse({"success": False, "message": "Invalid request."})


# forgot password

def forgotpassword(request):
    email = request.session.get("reset_email")
    stage = "email"  # default stage

    if request.method == "POST":
        # --- Stage 1: user enters email ---
        if "send_otp" in request.POST:
            form = ForgotPasswordForm(request.POST)
            if form.is_valid():
                email = form.cleaned_data["email"].lower()

                # check if user exists
                if not User.objects.filter(email=email).exists():
                    messages.error(request, "No account found with that email.")
                else:
                    otp = str(random.randint(100000, 999999))
                    EmailOTP.objects.create(temp_email=email, code=otp, purpose="reset")
                    send_mail(
                        subject="Password Reset OTP",
                        message=f"Your OTP is {otp}. It expires in 10 minutes.",
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[email],
                    )
                    request.session["reset_email"] = email
                    messages.success(request, "OTP sent to your email.")
                    stage = "otp"
            else:
                messages.error(request, "Please enter a valid email address.")

        # --- Stage 2: user verifies OTP ---
        elif "verify_otp" in request.POST:
            otp = request.POST.get("otp")
            email = request.session.get("reset_email")

            otp_obj = EmailOTP.objects.filter(temp_email=email, code=otp, is_used=False).last()
            if otp_obj and not otp_obj.is_expired():
                otp_obj.is_used = True
                otp_obj.save()
                request.session["otp_verified"] = True
                messages.success(request, "OTP verified! You can now reset your password.")
                stage = "reset"
            else:
                messages.error(request, "Invalid or expired OTP.")
                stage = "otp"

        # --- Stage 3: user resets password ---
        elif "reset_password" in request.POST:
            if not request.session.get("otp_verified"):
                messages.error(request, "Please verify OTP first.")
                stage = "otp"
            else:
                password = request.POST.get("new_password")
                confirm = request.POST.get("confirm_password")

                if password != confirm:
                    messages.error(request, "Passwords do not match.")
                    stage = "reset"
                else:
                    email = request.session.get("reset_email")
                    user = User.objects.get(email=email)
                    user.set_password(password)
                    user.save()

                    del request.session["reset_email"]
                    del request.session["otp_verified"]

                    messages.success(request, "Password reset successful! You can now log in.")
                    return redirect("login")

    else:
        form = ForgotPasswordForm()

    return render(request, "authentication/forgotpassword.html", {
        "form": ForgotPasswordForm(),
        "stage": stage,
        "email": email,
    })
