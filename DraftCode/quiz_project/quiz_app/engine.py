# quiz_app/engine.py
from django.utils.timezone import now
from .models import LearnerTopic, ItemStats, Question, StudentProgress, Topic
from quiz_app.models import UserProfile

DEFAULT_MASTERY = 0.2

def initialize_learner(learner, subject):
    """
    Ensure LearnerTopic and ItemStats exist for this learner & subject.
    Idempotent: safe to call any time.
    """
    # create LearnerTopic rows (unlocked=True always since you removed prereqs)
    topics = Topic.objects.filter(subject=subject)
    for topic in topics:
        LearnerTopic.objects.get_or_create(
            learner=learner,
            topic=topic,
            defaults={"p_mastery": DEFAULT_MASTERY, "unlocked": True, "last_seen_at": None}
        )

    # create ItemStats for every question in subject for this learner (if you want per-item tracking)
    level = None
    try:
        level = UserProfile.objects.get(user=learner).school_level
    except UserProfile.DoesNotExist:
        level = None

    qs = Question.objects.filter(subject=subject)
    if level:
        qs = qs.filter(school_level=level)

    for q in qs:
        ItemStats.objects.get_or_create(learner=learner, question=q, defaults={
            "shown_cnt": 0, "correct_cnt": 0, "incorrect_cnt": 0, "last_seen_at": None
        })

def pick_target_topic(learner, subject):
    """
    Pick unlocked topic with lowest mastery < 0.85, tie by last_seen_at.
    Returns LearnerTopic or None.
    """
    return (LearnerTopic.objects
            .filter(learner=learner, topic__subject=subject, unlocked=True, p_mastery__lt=0.85)
            .order_by("p_mastery", "last_seen_at")
            .first())

def choose_difficulty(p_mastery):
    if p_mastery < 0.5:
        return [1, 2]      # Easy, Medium
    elif p_mastery < 0.75:
        return [2]         # Medium
    else:
        return [2, 3]      # Medium, Hard

# engine.py (replace candidate_item + record_attempt)

def _get_base_queryset_for_learner(learner, topic):
    # prefer learner level if exists, else all subject questions
    level = None
    try:
        level = learner.userprofile.school_level
    except Exception:
        level = None

    if level:
        qs_level = Question.objects.filter(subject=topic.subject, school_level=level)
        if qs_level.exists():
            base_qs = qs_level
        else:
            base_qs = Question.objects.filter(subject=topic.subject)
    else:
        base_qs = Question.objects.filter(subject=topic.subject)

    # prefer topic-specific if the Question model has a topic FK
    if hasattr(Question, "topic"):
        base_qs = base_qs.filter(topic=topic)

    return base_qs

def candidate_item(learner, topic, difficulties, exclude_ids=None):
    """
    Robust candidate picker:
    - exclude questions answered correctly by learner
    - exclude recent items for learner (last 10)
    - exclude optional exclude_ids (e.g. last answered question from session)
    - penalize by shown_cnt and randomize tie
    """
    if exclude_ids is None:
        exclude_ids = []

    # recent IDs for this learner & subject
    recent_ids = list(
        ItemStats.objects
                 .filter(learner=learner, question__subject=topic.subject)
                 .order_by("-last_seen_at")
                 .values_list("question_id", flat=True)[:10]
    )

    # ids of questions learner already answered correctly (for this subject)
    answered_correct_ids = list(
        StudentProgress.objects
                       .filter(student=learner, answered_correctly=True, question__subject=topic.subject)
                       .values_list("question_id", flat=True)
    )

    # combined set to exclude
    combined_exclude = set(recent_ids) | set(answered_correct_ids) | set([i for i in exclude_ids if i])

    # debug: print to server log
    print("[candidate_item] recent_ids:", recent_ids)
    print("[candidate_item] answered_correct_ids:", answered_correct_ids)
    print("[candidate_item] exclude_ids param:", exclude_ids)
    print("[candidate_item] combined_exclude:", combined_exclude)

    base_qs = _get_base_queryset_for_learner(learner, topic)
    # always exclude already-correct + combined_exclude
    qs_filtered = base_qs.exclude(id__in=combined_exclude).filter(difficulty__in=difficulties)

    if not qs_filtered.exists():
        qs_filtered = base_qs.exclude(id__in=combined_exclude)

    if not qs_filtered.exists():
        # last resort try any question in subject but still exclude correct answers
        qs_filtered = Question.objects.filter(subject=topic.subject).exclude(id__in=answered_correct_ids)

    if not qs_filtered.exists():
        # nothing to show
        print("[candidate_item] no candidate found after filtering.")
        return None

    # Build scored list penalizing shown_cnt
    items = []
    for q in qs_filtered:
        stats, _ = ItemStats.objects.get_or_create(learner=learner, question=q,
                                                   defaults={"shown_cnt": 0, "correct_cnt": 0, "incorrect_cnt": 0})
        score = 1.0 / (1 + (stats.shown_cnt or 0))
        items.append((q, score))

    if not items:
        return None

    items.sort(key=lambda x: x[1], reverse=True)
    top_score = items[0][1]
    top_items = [q for q, s in items if s == top_score]

    import random
    chosen = random.choice(top_items)
    print("[candidate_item] chosen_id:", chosen.id)
    return chosen


def record_attempt(learner, question, is_correct):
    # update per-question stats (always do this)
    stats, _ = ItemStats.objects.get_or_create(learner=learner, question=question,
                                               defaults={"shown_cnt": 0, "correct_cnt": 0, "incorrect_cnt": 0})
    # ensure integers
    stats.shown_cnt = (stats.shown_cnt or 0) + 1
    stats.last_seen_at = now()
    if is_correct:
        stats.correct_cnt = (stats.correct_cnt or 0) + 1
    else:
        stats.incorrect_cnt = (stats.incorrect_cnt or 0) + 1
    stats.save()

    # update LearnerTopic if question.topic exists
    if hasattr(question, "topic") and question.topic is not None:
        lt, _ = LearnerTopic.objects.get_or_create(
            learner=learner, topic=question.topic,
            defaults={"p_mastery": 0.2, "unlocked": True}
        )
        lt.p_mastery = max(0.0, min(1.0, lt.p_mastery + (0.05 if is_correct else -0.02)))
        lt.last_seen_at = now()
        lt.save()
