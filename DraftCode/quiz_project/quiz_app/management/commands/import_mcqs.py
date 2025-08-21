# quiz_app/management/commands/import_mcqs.py
import csv, os
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils.text import slugify
from quiz_app.models import Level, Subject, Topic, Question

class Command(BaseCommand):
    help = "Import MCQ CSV. Usage: python manage.py import_mcqs path/to/mcqs.csv"

    def add_arguments(self, parser):
        parser.add_argument("csvfile", type=str, help="Path to CSV file")
        parser.add_argument("--skip-header", action="store_true", help="If csv has a header and you want to skip explicitly")

    def handle(self, *args, **options):
        path = options["csvfile"]
        if not os.path.exists(path):
            raise CommandError(f"File not found: {path}")

        created_q = 0
        skipped = 0

        with open(path, newline='', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        if not rows:
            self.stdout.write(self.style.WARNING("No rows found in CSV."))
            return

        with transaction.atomic():
            for r in rows:
                source_id = (r.get('id') or '').strip()
                level_name = (r.get('level') or '').strip()
                subject_name = (r.get('subject') or '').strip()
                topic_name = (r.get('topic') or '').strip()
                difficulty = (r.get('difficulty') or '').strip().lower()
                question_text = (r.get('question') or '').strip()
                option_a = (r.get('option_a') or '').strip()
                option_b = (r.get('option_b') or '').strip()
                option_c = (r.get('option_c') or '').strip()
                correct_option = (r.get('correct_option') or '').strip().upper()
                explanation = (r.get('explanation') or '').strip()

                if not question_text:
                    skipped += 1
                    continue

                # Avoid duplicate by source_id if present
                if source_id:
                    if Question.objects.filter(source_id=source_id).exists():
                        skipped += 1
                        continue

                # Ensure Level
                level = None
                if level_name:
                    level, _ = Level.objects.get_or_create(name=level_name, defaults={'slug': slugify(level_name)})

                # Ensure Subject
                subject = None
                if subject_name:
                    subject, _ = Subject.objects.get_or_create(name=subject_name)

                # Optional: create Topic model instance (if you use Topic model)
                # If you prefer to store as free text, skip creating Topic model
                if topic_name:
                    try:
                        topic_obj, _ = Topic.objects.get_or_create(subject=subject, name=topic_name)
                    except Exception:
                        topic_obj = None
                else:
                    topic_obj = None

                # Map difficulty to allowed choices
                mapped_diff = ''
                if difficulty in ('easy', 'facile', 'e'):
                    mapped_diff = 'easy'
                elif difficulty in ('medium', 'moyen', 'm'):
                    mapped_diff = 'medium'
                elif difficulty in ('hard', 'difficile', 'h'):
                    mapped_diff = 'hard'
                else:
                    # fallback: leave empty or set 'medium'
                    mapped_diff = ''

                # Validate correct option
                if correct_option not in ('A','B','C'):
                    # try to detect by matching text equality
                    co = None
                    for label, text in [('A', option_a), ('B', option_b), ('C', option_c)]:
                        if text and correct_option and correct_option.strip().lower() == text.strip().lower():
                            co = label
                            break
                    correct_option = co or 'A'  # default to A to avoid null

                q = Question.objects.create(
                    source_id = source_id or None,
                    level = level,
                    subject = subject,
                    topic = topic_name,
                    difficulty = mapped_diff,
                    question_text = question_text,
                    option_a = option_a or None,
                    option_b = option_b or None,
                    option_c = option_c or None,
                    correct_option = correct_option,
                    explanation = explanation or None,
                )
                created_q += 1

        self.stdout.write(self.style.SUCCESS(f"Import finished: {created_q} created, {skipped} skipped."))
