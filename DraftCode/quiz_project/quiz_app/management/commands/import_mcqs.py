import csv
from quiz_app.models import Question, Subject, SchoolLevel

# chemin de ton fichier
csv_file_path = r"C:\Users\ahlam\Downloads\mcqs_morocco.csv"

# dictionnaire pour mapper les difficultés
difficulty_map = {
    "Easy": 1,
    "Medium": 2,
    "Hard": 3
}

with open(csv_file_path, newline='', encoding="utf-8") as csvfile:
    reader = csv.DictReader(csvfile, delimiter=",")
    for row in reader:
        schoollevel_name = row["schoollevel"].strip()
        subject_name = row["subject"].strip()
        difficulty_text = row["difficulty"].strip()

        # récupérer ou créer SchoolLevel et Subject
        schoollevel, _ = SchoolLevel.objects.get_or_create(level_name=schoollevel_name)
        subject, _ = Subject.objects.get_or_create(subject_name=subject_name)

        # convertir difficulté texte -> int
        difficulty = difficulty_map.get(difficulty_text, 1)

        # création de la Question
        Question.objects.create(
            question=row["question"].strip(),
            subject=subject,
            school_level=schoollevel,
            difficulty=difficulty,
            option_a=row["option_a"].strip() if row["option_a"] else None,
            option_b=row["option_b"].strip() if row["option_b"] else None,
            option_c=row["option_c"].strip() if row["option_c"] else None,
            correct_option=row["correct_option"].strip() if row["correct_option"] else None,
            explanation=row["explanation"].strip() if row["explanation"] else None
        )
