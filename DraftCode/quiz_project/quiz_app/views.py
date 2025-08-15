from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from .models import Subject
from .forms import SubjectForm  # You'll need to create a SubjectForm


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
