from datetime import date, datetime

from pawpal_system import Pet, Priority, Task, TaskType


def _make_task(pet: Pet, name: str = "Walk") -> Task:
    return Task(
        name=name,
        priority=Priority.HIGH,
        frequency="daily",
        deadline=datetime.combine(date.today(), datetime.min.time()).replace(hour=8),
        duration_minutes=15,
        task_type=TaskType.WALK,
        pet=pet,
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
