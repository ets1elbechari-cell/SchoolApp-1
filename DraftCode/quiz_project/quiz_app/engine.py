# quiz_app/engine.py
from django.utils.timezone import now
from .models import LearnerTopic, ItemStats, Question, StudentProgress, Topic
from quiz_app.models import UserProfile
from django.db import transaction

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

def _get_base_queryset_for_learner(learner, topic):
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

    if hasattr(Question, "topic"):
        base_qs = base_qs.filter(topic=topic)

    return base_qs

def candidate_item(learner, subject, difficulties=None):
    """
    Return one unanswered-by-correct question for the learner for given subject (prefer learner level).
    If difficulties is provided, try that first, otherwise use any difficulty.
    Returns Question or None if none remain.
    """
    # get learner's level safely
    level = None
    try:
        level = learner.userprofile.school_level
    except Exception:
        level = None

    # prefer questions matching the learner's level if any exist
    if level:
        qs_level = Question.objects.filter(subject=subject, school_level=level)
        base_qs = qs_level if qs_level.exists() else Question.objects.filter(subject=subject)
    else:
        base_qs = Question.objects.filter(subject=subject)

    # IDs of questions the learner already answered correctly (for this subject)
    answered_correct_ids = list(
        StudentProgress.objects
            .filter(student=learner, answered_correctly=True, question__subject=subject)
            .values_list("question_id", flat=True)
    )

    # Remove already-correct questions
    candidate_qs = base_qs.exclude(id__in=answered_correct_ids)

    # If difficulties specified, prefer those
    if difficulties:
        dq = candidate_qs.filter(difficulty__in=difficulties)
        if dq.exists():
            candidate_qs = dq

    # If nothing left, return None
    if not candidate_qs.exists():
        return None

    # Build scored list (penalize shown_cnt)
    items = []
    for q in candidate_qs:
        stats, _ = ItemStats.objects.get_or_create(
            learner=learner,
            question=q,
            defaults={"shown_cnt": 0, "correct_cnt": 0, "incorrect_cnt": 0, "last_seen_at": None}
        )
        score = 1.0 / (1 + (stats.shown_cnt or 0))
        items.append((q, score))

    # pick one among highest-scoring (tie-break random)
    items.sort(key=lambda x: x[1], reverse=True)
    top_score = items[0][1]
    top_items = [q for q, s in items if s == top_score]
    return random.choice(top_items)
import random

def record_attempt(learner, question, is_correct):
    """
    Always update ItemStats. Also update / create LearnerTopic even if question.topic is None.
    """
    try:
        with transaction.atomic():
            stats, _ = ItemStats.objects.get_or_create(
                learner=learner,
                question=question,
                defaults={"shown_cnt": 0, "correct_cnt": 0, "incorrect_cnt": 0, "last_seen_at": None}
            )
            # increment counters defensively
            stats.shown_cnt = (stats.shown_cnt or 0) + 1
            stats.last_seen_at = now()
            if is_correct:
                stats.correct_cnt = (stats.correct_cnt or 0) + 1
            else:
                stats.incorrect_cnt = (stats.incorrect_cnt or 0) + 1
            stats.save()

            # Update LearnerTopic: if question has topic use it, otherwise try to pick a default
            topic_obj = getattr(question, "topic", None)
            if topic_obj is None:
                # optional: try to find a topic for this subject (e.g., a 'General' topic)
                # topic_obj = Topic.objects.filter(subject=question.subject).first()
                pass

            if topic_obj:
                lt, _ = LearnerTopic.objects.get_or_create(
                    learner=learner,
                    topic=topic_obj,
                    defaults={"p_mastery": 0.2, "unlocked": True}
                )
                lt.p_mastery = max(0.0, min(1.0, lt.p_mastery + (0.05 if is_correct else -0.02)))
                lt.last_seen_at = now()
                lt.save()

    except Exception as e:
        # log error (so we can see it)
        print("[record_attempt] error:", e)
        raise