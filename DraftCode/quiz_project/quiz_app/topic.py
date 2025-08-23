import csv
from quiz_app.models import Question, Subject, Topic

# Path to your CSV
csv_file_path = r"C:\Users\ahlam\Downloads\mcqs_morocco.csv"

with open(csv_file_path, newline="", encoding="utf-8") as csvfile:
    reader = csv.DictReader(csvfile, delimiter=",")
    for row in reader:
        subject_name = row["subject"].strip()
        topic_name = row.get("topic", "").strip()
        question_text = row["question"].strip()

        if not topic_name:
            continue  # skip if no topic in row

        # ✅ Fix: use the correct field name ("name")
        try:
            subject = Subject.objects.get(name=subject_name)
        except Subject.DoesNotExist:
            print(f"❌ Subject not found: {subject_name}")
            continue

        # Create/find topic under this subject
        topic, _ = Topic.objects.get_or_create(name=topic_name, subject=subject)

        # Attach topic to the right question
        try:
            question = Question.objects.get(subject=subject, question=question_text)
            question.topic = topic
            question.save()
            print(f"✅ Updated question '{question_text}' with topic '{topic_name}'")
        except Question.DoesNotExist:
            print(f"❌ Question not found in DB: {question_text}")
