from datetime import datetime, timedelta, date

from pawpal_system import Owner, Pet, Task, Scheduler, Priority, TaskType


def print_schedule(plan, owner: Owner) -> None:
    today = date.today().strftime("%A, %B %d %Y")
    width = 60
    print("=" * width)
    print(f"  PawPal — Today's Schedule for {owner.name}")
    print(f"  {today}")

    windows = []
    for start_str, end_str in owner.availability.items():
        start = datetime.strptime(start_str, "%H:%M").strftime("%I:%M %p")
        end = datetime.strptime(end_str, "%H:%M").strftime("%I:%M %p")
        windows.append(f"{start} – {end}")
    print(f"  Available: {', '.join(windows) if windows else 'none'}")

    print("=" * width)

    if not plan.scheduled_tasks:
        print("  No tasks scheduled for today.")
    else:
        for st in plan.scheduled_tasks:
            task = st.task
            start = st.start_time.strftime("%I:%M %p")
            end = st.end_time.strftime("%I:%M %p")
            status = "✓" if task.is_completed else "○"
            print(
                f"  {status} {start} – {end}  |  {task.task_type.value:<12}"
                f"  {task.name:<22}  [{task.priority.value}]  ({task.pet.name})"
            )

    print("-" * width)
    print(f"  Total tasks: {len(plan.scheduled_tasks)}   |   Total time: {plan.total_time_minutes} min")
    print("=" * width)


def main() -> None:
    # --- Owner ---
    owner = Owner(
        name="Jordan",
        availability={"07:00": "09:00", "17:00": "19:00"},
        preferences=["morning walks", "evening feeding"],
    )

    # --- Pets ---
    buddy = Pet(name="Buddy", age=3, species="Dog", breed="Golden Retriever")
    whiskers = Pet(name="Whiskers", age=5, species="Cat", breed="Tabby")

    owner.add_pet(buddy)
    owner.add_pet(whiskers)

    # --- Tasks (deadline = today at various times) ---
    today = datetime.combine(date.today(), datetime.min.time())

    buddy.add_task(Task(
        name="Morning Walk",
        priority=Priority.HIGH,
        frequency="daily",
        deadline=today.replace(hour=8, minute=0),
        duration_minutes=30,
        task_type=TaskType.WALK,
        pet=buddy,
    ))

    buddy.add_task(Task(
        name="Breakfast",
        priority=Priority.HIGH,
        frequency="daily",
        deadline=today.replace(hour=7, minute=30),
        duration_minutes=10,
        task_type=TaskType.FEEDING,
        pet=buddy,
    ))

    whiskers.add_task(Task(
        name="Hairball Medication",
        priority=Priority.MEDIUM,
        frequency="weekly",
        deadline=today.replace(hour=8, minute=30),
        duration_minutes=5,
        task_type=TaskType.MEDICATION,
        pet=whiskers,
    ))

    buddy.add_task(Task(
        name="Fetch & Play",
        priority=Priority.LOW,
        frequency="daily",
        deadline=today.replace(hour=18, minute=0),
        duration_minutes=20,
        task_type=TaskType.PLAY,
        pet=buddy,
    ))

    whiskers.add_task(Task(
        name="Evening Feeding",
        priority=Priority.HIGH,
        frequency="daily",
        deadline=today.replace(hour=17, minute=30),
        duration_minutes=10,
        task_type=TaskType.FEEDING,
        pet=whiskers,
    ))

    # --- Generate & print schedule ---
    scheduler = Scheduler(owner=owner, pets=[buddy, whiskers])
    plan = scheduler.create_schedule()
    print_schedule(plan, owner)


if __name__ == "__main__":
    main()
