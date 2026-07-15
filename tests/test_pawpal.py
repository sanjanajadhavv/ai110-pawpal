from __future__ import annotations

from datetime import date, datetime, timedelta

from pawpal_system import Owner, Pet, Priority, Scheduler, Task, TaskType


def _make_task(
    pet: Pet,
    name: str = "Walk",
    hour: int = 8,
    minute: int = 0,
    duration_minutes: int = 15,
    frequency: str = "daily",
    day_offset: int = 0,
) -> Task:
    deadline = datetime.combine(date.today(), datetime.min.time()).replace(
        hour=hour, minute=minute
    ) + timedelta(days=day_offset)
    return Task(
        name=name,
        priority=Priority.HIGH,
        frequency=frequency,
        deadline=deadline,
        duration_minutes=duration_minutes,
        task_type=TaskType.WALK,
        pet=pet,
    )


def _make_owner(availability: dict | None = None) -> Owner:
    return Owner(
        name="Jordan",
        availability=availability if availability is not None else {"07:00": "09:00"},
        preferences=[],
    )


def test_mark_complete_changes_task_status():
    pet = Pet(name="Buddy", age=3, species="Dog", breed="Lab")
    task = _make_task(pet)

    assert task.is_completed is False
    task.mark_complete()
    assert task.is_completed is True


def test_add_task_increases_pet_task_count():
    pet = Pet(name="Buddy", age=3, species="Dog", breed="Lab")
    task = _make_task(pet)

    assert len(pet.get_tasks()) == 0
    pet.add_task(task)
    assert len(pet.get_tasks()) == 1


# ---------------------------------------------------------------------------
# Sorting correctness
# ---------------------------------------------------------------------------

def test_sort_by_time_orders_tasks_chronologically():
    pet = Pet(name="Buddy", age=3, species="Dog", breed="Lab")
    evening = _make_task(pet, name="Evening Feeding", hour=17)
    morning = _make_task(pet, name="Breakfast", hour=7)
    midday = _make_task(pet, name="Midday Walk", hour=12)
    for t in (evening, morning, midday):
        pet.add_task(t)

    scheduler = Scheduler(_make_owner(), [pet])
    ordered = scheduler.sort_by_time()

    assert [t.name for t in ordered] == ["Breakfast", "Midday Walk", "Evening Feeding"]


def test_sort_by_time_uses_full_datetime_not_just_time_of_day():
    """A recurring task's next occurrence shares today's clock time but lands
    on a later date, so it must sort after today's task, not interleaved."""
    pet = Pet(name="Buddy", age=3, species="Dog", breed="Lab")
    today_task = _make_task(pet, name="Breakfast Today", hour=7, day_offset=0)
    next_week_same_time = _make_task(pet, name="Breakfast Next Week", hour=7, day_offset=7)
    later_today = _make_task(pet, name="Walk Today", hour=8, day_offset=0)
    for t in (next_week_same_time, later_today, today_task):
        pet.add_task(t)

    scheduler = Scheduler(_make_owner(), [pet])
    ordered = scheduler.sort_by_time()

    assert [t.name for t in ordered] == [
        "Breakfast Today",
        "Walk Today",
        "Breakfast Next Week",
    ]


def test_sort_by_time_on_pet_with_no_tasks_returns_empty_list():
    pet = Pet(name="Whiskers", age=2, species="Cat", breed="Tabby")
    scheduler = Scheduler(_make_owner(), [pet])

    assert scheduler.sort_by_time() == []
    assert scheduler.detect_conflicts() == []
    assert scheduler.filter_tasks() == []


# ---------------------------------------------------------------------------
# Recurrence logic
# ---------------------------------------------------------------------------

def test_completing_daily_task_spawns_next_day_occurrence():
    pet = Pet(name="Buddy", age=3, species="Dog", breed="Lab")
    task = _make_task(pet, name="Breakfast", hour=7, frequency="daily")
    pet.add_task(task)

    next_task = task.mark_complete()

    assert next_task is not None
    assert next_task.name == task.name
    assert next_task.is_completed is False
    assert next_task.deadline == task.deadline + timedelta(days=1)
    assert next_task in pet.get_tasks()


def test_completing_weekly_task_spawns_next_week_occurrence():
    pet = Pet(name="Buddy", age=3, species="Dog", breed="Lab")
    task = _make_task(pet, name="Grooming", hour=10, frequency="weekly")
    pet.add_task(task)

    next_task = task.mark_complete()

    assert next_task is not None
    assert next_task.deadline == task.deadline + timedelta(weeks=1)


def test_completing_one_off_task_does_not_spawn_a_new_task():
    pet = Pet(name="Buddy", age=3, species="Dog", breed="Lab")
    task = _make_task(pet, name="Vet Visit", frequency="once")
    pet.add_task(task)

    next_task = task.mark_complete()

    assert next_task is None
    assert len(pet.get_tasks()) == 1


def test_scheduler_mark_task_complete_registers_new_occurrence_immediately():
    pet = Pet(name="Buddy", age=3, species="Dog", breed="Lab")
    task = _make_task(pet, name="Breakfast", frequency="daily")
    pet.add_task(task)
    scheduler = Scheduler(_make_owner(), [pet])

    next_task = scheduler.mark_task_complete(task)

    assert next_task is not None
    assert next_task in scheduler.tasks


# ---------------------------------------------------------------------------
# Conflict detection
# ---------------------------------------------------------------------------

def test_detect_conflicts_flags_tasks_at_the_exact_same_time():
    pet_a = Pet(name="Buddy", age=3, species="Dog", breed="Lab")
    pet_b = Pet(name="Whiskers", age=2, species="Cat", breed="Tabby")
    task_a = _make_task(pet_a, name="Evening Brushing", hour=17, minute=30, duration_minutes=15)
    task_b = _make_task(pet_b, name="Evening Feeding", hour=17, minute=30, duration_minutes=10)
    pet_a.add_task(task_a)
    pet_b.add_task(task_b)

    scheduler = Scheduler(_make_owner(), [pet_a, pet_b])
    conflicts = scheduler.detect_conflicts()

    assert len(conflicts) == 1
    assert "Evening Brushing" in conflicts[0]
    assert "Evening Feeding" in conflicts[0]


def test_detect_conflicts_ignores_back_to_back_tasks():
    """One task ending exactly when the next starts is not an overlap."""
    pet = Pet(name="Buddy", age=3, species="Dog", breed="Lab")
    first = _make_task(pet, name="Morning Walk", hour=8, minute=0, duration_minutes=30)
    second = _make_task(pet, name="Breakfast", hour=8, minute=30, duration_minutes=15)
    pet.add_task(first)
    pet.add_task(second)

    scheduler = Scheduler(_make_owner(), [pet])

    assert scheduler.detect_conflicts() == []


def test_detect_conflicts_ignores_completed_tasks():
    pet = Pet(name="Buddy", age=3, species="Dog", breed="Lab")
    completed = _make_task(pet, name="Old Walk", hour=8, duration_minutes=30)
    completed.is_completed = True
    overlapping = _make_task(pet, name="New Walk", hour=8, minute=10, duration_minutes=15)
    pet.add_task(completed)
    pet.add_task(overlapping)

    scheduler = Scheduler(_make_owner(), [pet])

    assert scheduler.detect_conflicts() == []
