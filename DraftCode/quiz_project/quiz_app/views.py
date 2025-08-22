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
from .models import UserProfile, Filiere, SchoolLevel,StudentProgress,Question
from django.contrib import messages
from django.contrib.auth import logout  


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
        email = request.POST.get("email")
        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        date_of_birth = request.POST.get("date_of_birth")  # corrige le nom selon ton input
        gender = request.POST.get("gender")
        school_level = request.POST.get("school_level")  # corrige le name du select
        filiere_id = request.POST.get("filiere")

        try:
            schoollevel_instance = SchoolLevel.objects.get(id=school_level)
        except SchoolLevel.DoesNotExist:
            messages.error(request, "Niveau scolaire invalide.")
            return render(request, "register.html")

        try:
            filiere_instance = Filiere.objects.get(id=filiere_id)
        except Filiere.DoesNotExist:
            messages.error(request, "Filière invalide.")
            return render(request, "register.html")

        password = request.POST.get("password")   # <-- tu récupères ça
        password1 = request.POST.get("password1")
        password2 = request.POST.get("password2")

        if password1 != password2:
            messages.error(request, "Les mots de passe ne correspondent pas.")
            return render(request, "register.html")

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email déjà pris.")
            return render(request, "register.html")

        # Création de l'utilisateur
        user = User.objects.create_user(
            username=email,
            email=email,
            password=password1,
            first_name=first_name,
            last_name=last_name
        )
        user.is_active = False
        user.save()

        # Création du profil utilisateur
        profile = UserProfile.objects.create(
            user=user,
            date_of_birth=date_of_birth,
            gender=gender,
            school_level=schoollevel_instance,
            filiere=filiere_instance,
              # direct ici
            )
        code=str(random.randint(100000, 999999))
        profile.confirmation_code=code
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

    # GET → affichage du formulaire
    levels = SchoolLevel.objects.all()
    filieres = Filiere.objects.all()
    return render(request, "register.html", {"levels": levels, "filieres": filieres})



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
        if user is not None:
            login(request, user)
            return redirect("home")  # Redirect after login
        else:
            return render(request, "login.html", {"error": "Identifiants incorrects"})
    return render(request, "login.html")

def logout_view(request):
    logout(request)
    return redirect("home")

def get_next_question(student, subject, school_level):
    """
    Returns the next question for the student following the learning path:
    1. Filter by subject and school level
    2. Order by difficulty (Easy -> Medium -> Hard)
    3. Exclude already answered questions
    """
    # Step 1: Get all questions for this subject and level
    questions = Question.objects.filter(
        subject=subject,
        school_level=school_level
    ).order_by('difficulty')

    # Step 2: Exclude questions already answered by the student
    answered_question_ids = StudentProgress.objects.filter(
        student=student
    ).values_list('question_id', flat=True)

    unanswered_questions = questions.exclude(id__in=answered_question_ids)

    # Step 3: Return the first unanswered question, or None if finished
    return unanswered_questions.first()

def take_quiz(request, subject_id):
    student = request.user
    subject = Subject.objects.get(id=subject_id)
    level = UserProfile.objects.get(user=student).school_level

    question = get_next_question(student, subject, level)

    if not question:
        return redirect("quiz_finished", subject_id=subject.id)

    return render(request, "take_quiz.html", {"question": question})

def quiz_finished(request, subject_id):
    student = request.user
    subject = Subject.objects.get(id=subject_id)
    school_level = UserProfile.objects.get(user=student).school_level

    total_questions = Question.objects.filter(subject=subject, school_level=school_level).count()
    correct_answers = StudentProgress.objects.filter(
        student=student, 
        question__subject=subject, 
        question__school_level=school_level, 
        answered_correctly=True
    ).count()

    return render(request, "quiz_finished.html", {
        "total_questions": total_questions,
        "correct_answers": correct_answers,
        "subject": subject,
        "level": school_level
    })


def submit_answer(request, question_id):
    student = request.user
    question = Question.objects.get(id=question_id)
    answer = request.POST.get("answer")  # 'A', 'B', or 'C'
    correct = (answer == question.correct_option)

    StudentProgress.objects.update_or_create(
        student=student,
        question=question,
        defaults={"answered_correctly": correct}
    )

    # Redirect to next question
    return redirect("take_quiz", subject_id=question.subject.id)

def subject_choose(request):
    subjects = Subject.objects.all()
    return render(request, "subject_choose.html", {"subjects": subjects})
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
