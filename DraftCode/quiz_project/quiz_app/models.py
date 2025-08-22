from django.db import models
from django.contrib.auth.models import User



class ConfirmUser(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    confirmation_code = models.CharField(max_length=6, blank=True, null=True)

    def __str__(self):
        return f"Profile({self.user.username})"

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    confirmation_code = models.CharField(max_length=6, blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    school_level = models.ForeignKey('SchoolLevel', on_delete=models.CASCADE, blank=True, null=True)
    filiere = models.ForeignKey('Filiere', on_delete=models.CASCADE, blank=True, null=True)
    gender = models.CharField(max_length=10, choices=[('M', 'Male'), ('F', 'Female')], blank=True, null=True)

    def __str__(self):
        return f"Profile({self.user.username})"
    
class SchoolLevel(models.Model):
    level_name = models.CharField(max_length=50)

    def __str__(self):
        return self.level_name

class Filiere(models.Model):
    name = models.CharField(max_length=100)
    schoollevel = models.ForeignKey(SchoolLevel, on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return self.name


class Subject(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Question(models.Model):
    question = models.TextField()
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    school_level = models.ForeignKey(SchoolLevel, on_delete=models.CASCADE)

    difficulty = models.CharField(
        max_length=10,
        choices=[('Easy', 'Easy'), ('Medium', 'Medium'), ('Hard', 'Hard')]
    )

    option_a = models.CharField(max_length=255,blank=True, null=True)
    option_b = models.CharField(max_length=255,blank=True, null=True)
    option_c = models.CharField(max_length=255,blank=True, null=True)
    correct_option = models.CharField(max_length=1, choices=[('A','A'),('B','B'),('C','C')],blank=True, null=True)
    explanation = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.question[:50]


class Answer(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    text = models.CharField(max_length=1000)
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return self.text


class Quiz(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    questions = models.ManyToManyField(Question, through='QuizQuestion')

    def __str__(self):
        return f"{self.user.username}'s Quiz on {self.subject.name}"


class QuizQuestion(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)


class QuizResult(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE)
    score = models.IntegerField()

    def __str__(self):
        return f"{self.user.username}'s Result for {self.quiz}"

class StudentProgress(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    answered_correctly = models.BooleanField(default=False)
    answered_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('student', 'question')  # avoid duplicates

    def __str__(self):
        return f"{self.student.username} - {self.question.id} - {self.answered_correctly}"