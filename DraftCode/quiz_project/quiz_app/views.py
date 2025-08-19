from pyexpat.errors import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from .models import Subject
from .forms import SubjectForm  # You'll need to create a SubjectForm
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
import random
from django.core.mail import send_mail
from .models import UserProfile
from django.contrib import messages


def say_hello(request):
    return HttpResponse('Hello world')
def home(request):
    return render(request, 'home.html')  # Create a home.html template in your templates directory

def add_subject(request):
    if request.method == 'POST':
        form = SubjectForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('subject_list')  # Redirect to a subject list page or any other appropriate view
    else:
        form = SubjectForm()

    return render(request, 'add_subject.html', {'form': form})


def subject_list(request):
    subjects = Subject.objects.all()
    return render(request, 'subject_list.html', {'subjects': subjects})


def modify_subject(request, subject_id):
    subject = get_object_or_404(Subject, pk=subject_id)

    if request.method == 'POST':
        form = SubjectForm(request.POST, instance=subject)
        if form.is_valid():
            form.save()
            return redirect('subject_list')
    else:
        form = SubjectForm(instance=subject)

    return render(request, 'modify_subject.html', {'form': form})


def delete_subject(request, subject_id):
    subject = get_object_or_404(Subject, pk=subject_id)

    if request.method == 'POST':
        subject.delete()
        return redirect('subject_list')

    return render(request, 'delete_subject.html', {'subject': subject})

#

def register_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        password = request.POST.get("password")
        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            is_active=False   # ⚠️ le compte reste inactif tant que pas confirmé
        )

        # Code de confirmation
        code = str(random.randint(100000, 999999))
        profile, _ = UserProfile.objects.get_or_create(user=user)
        profile.confirmation_code = code
        profile.save()

        # Envoi email
        send_mail(
            subject="Confirmation d'inscription",
            message=f"Bonjour {first_name},\n\nVotre code de confirmation est : {code}",
            from_email="ets1.elbechari@gmail.com",
            recipient_list=[email],
            fail_silently=False,
        )
        request.session["pending_user_id"] = user.id

        # Redirection vers page de confirmation
        return redirect("confirm_email")  

    return render(request, "register.html")


from django.contrib.auth import login

def confirm_email_view(request):
    if request.method == "POST":
        code = request.POST.get("code")
        user_id = request.session.get("pending_user_id")

        if not user_id:
            messages.error(request, "Session expirée. Veuillez vous réinscrire.")
            return redirect("register")

        try:
            user = User.objects.get(id=user_id)
            profile = UserProfile.objects.get(user=user)

            if profile.confirmation_code == code:
                user.is_active = True
                user.save()
                # nettoyer la session
                del request.session["pending_user_id"]
                
                return redirect("login")
            else:
                messages.error(request, "Code invalide ❌")

        except (User.DoesNotExist, UserProfile.DoesNotExist):
            messages.error(request, "Erreur interne. Veuillez réessayer.")

    return render(request, "confirm_email.html")


def connexion_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)
        print("User:", user)  # Debug: See if user is authenticated

        if user is not None:
            print("User is active:", user.is_active)  # Debug: Check if user is active
            login(request, user)
            return redirect("home")
        else:
            messages.error(request, "Identifiants incorrects ❌")

    return render(request, "login.html")

# def create_quiz(request):
#     if request.method == 'POST':
#         # Handle form submission
#         subject_id = request.POST.get('subject')
#         difficulty_level = request.POST.get('difficulty')
#
#         # Retrieve random questions based on subject and difficulty
#         questions = Question.objects.filter(
#             subject_id=subject_id,
#             difficulty=difficulty_level
#         ).order_by('?')[:5]  # Adjust the number of questions as needed
#
#         # Create a quiz and associate questions
#         # You need to implement your Quiz model and logic here
#
#         # Redirect to the quiz-taking page
#         return redirect('take_quiz', quiz_id=quiz.id)
#
#     # If it's a GET request, simply render the form
#     return render(request, 'quiz/create_quiz.html')
#
# def take_quiz(request, quiz_id):
#     # Logic to take a quiz, calculate scores, and save results
#     return render(request, 'quiz/take_quiz.html', context)
#
# def view_results(request):
#     # Logic to display user's quiz results
#     return render(request, 'quiz/view_results.html', context)
