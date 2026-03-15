"""Recovery goal progress, computed from the patient's workouts since the goal was set."""
from datetime import timedelta

from django.utils import timezone

from .models import RecoveryGoal, Workout

LOWER_IS_BETTER = {'curl', 'squat'}  # rules where the joint angle closes toward the top of a rep


def _best_streak(dates):
    days = sorted(set(dates))
    best = run = 0
    for i, day in enumerate(days):
        run = run + 1 if i and day - days[i - 1] == timedelta(days=1) else 1
        best = max(best, run)
    return best


def progress(goal):
    """(current value, percent 0-100, achieved) for a goal."""
    workouts = Workout.objects.filter(patient=goal.patient, total_reps__gt=0, date__gte=timezone.localdate(goal.created_at))
    if goal.exercise and goal.kind != 'streak':
        workouts = workouts.filter(exercise=goal.exercise.slug)
    if goal.kind == 'sessions':
        current = workouts.count()
    elif goal.kind == 'total_reps':
        current = sum(workouts.values_list('total_reps', flat=True))
    elif goal.kind == 'streak':
        current = _best_streak(workouts.values_list('date', flat=True))
    else:  # range: best rep angle on the exercise
        lower = goal.exercise and goal.exercise.rule in LOWER_IS_BETTER
        angles = [a['angle'] for w in workouts for a in w.angles_data if isinstance(a, dict) and a.get('angle')]
        if not angles:
            return None, 0, False
        current = min(angles) if lower else max(angles)
        achieved = current <= goal.target if lower else current >= goal.target
        percent = 100 if achieved else round(100 * (goal.target / current if lower else current / goal.target))
        return current, percent, achieved
    return current, min(100, round(100 * current / goal.target)), current >= goal.target


def update_goals(patient):
    """Stamp achieved_at on goals that have just been reached. Returns the newly achieved goals."""
    reached = []
    for goal in RecoveryGoal.objects.filter(patient=patient, achieved_at__isnull=True).select_related('exercise'):
        if progress(goal)[2]:
            goal.achieved_at = timezone.now()
            goal.save(update_fields=['achieved_at'])
            reached.append(goal)
    return reached
