# quiz_app/engine.py

from django.utils.timezone import now
from .models import LearnerTopic, ItemStats, Question, Topic

def initialize_learner(learner, subject):
    topics = Topic.objects.filter(subject=subject)
    for topic in topics:
        unlocked = not topic.prereqs.exists()
        LearnerTopic.objects.get_or_create(
            learner=learner,
            topic=topic,
            defaults={"p_mastery": 0.20, "unlocked": unlocked}
        )

def pick_target_topic(learner, subject):
    return (LearnerTopic.objects
            .filter(learner=learner, topic__subject=subject, unlocked=True, p_mastery__lt=0.85)
            .order_by("p_mastery", "last_seen_at")
            .first())

def choose_difficulty(p_mastery):
    if p_mastery < 0.5:
        return [1, 2]  # Easy, Medium
    elif p_mastery < 0.75:
        return [2]     # Medium
    else:
        return [2, 3]  # Medium, Hard

def candidate_item(learner, topic, difficulties):
    recent_ids = (ItemStats.objects
                  .filter(learner=learner, question__subject=topic.subject)
                  .order_by("-last_seen_at")
                  .values_list("question_id", flat=True)[:10])

    qs = Question.objects.filter(
        subject=topic.subject,
        difficulty__in=difficulties
    ).exclude(id__in=recent_ids)

    items = []
    for q in qs:
        stats, _ = ItemStats.objects.get_or_create(learner=learner, question=q)
        score = 1 / (1 + stats.shown_cnt)  # penalize high exposure
        items.append((q, score))

    items.sort(key=lambda x: x[1], reverse=True)
    return items[0][0] if items else None

def record_attempt(learner, question, is_correct):
    stats, _ = ItemStats.objects.get_or_create(learner=learner, question=question)
    stats.shown_cnt += 1
    stats.last_seen_at = now()
    if is_correct:
        stats.correct_cnt += 1
    else:
        stats.incorrect_cnt += 1
    stats.save()

    lt = LearnerTopic.objects.get(learner=learner, topic=question.subject.topic)
    lt.p_mastery += 0.05 if is_correct else -0.02
    lt.p_mastery = max(0, min(1, lt.p_mastery))
    lt.last_seen_at = now()
    lt.save()

    for t in lt.topic.unlocks.all():
        prereqs = t.prereqs.all()
        if all(LearnerTopic.objects.get(learner=learner, topic=p).p_mastery >= 0.85 for p in prereqs):
            lt_unlock, _ = LearnerTopic.objects.get_or_create(learner=learner, topic=t)
            lt_unlock.unlocked = True
            lt_unlock.save()
