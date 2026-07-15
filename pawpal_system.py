from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta
from enum import Enum
from typing import Optional


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------

class Priority(Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class TaskType(Enum):
    WALK = "WALK"
    FEEDING = "FEEDING"
    MEDICATION = "MEDICATION"
    ENRICHMENT = "ENRICHMENT"
    GROOMING = "GROOMING"
    VET_VISIT = "VET_VISIT"
    TRAINING = "TRAINING"
    PLAY = "PLAY"


_PRIORITY_ORDER = {Priority.HIGH: 0, Priority.MEDIUM: 1, Priority.LOW: 2}


# ---------------------------------------------------------------------------
# Dataclasses  (Pet, Task, ScheduledTask)
# ---------------------------------------------------------------------------

# eq=False so Pet uses object identity for __eq__ and __hash__,
# allowing it to live in sets and dicts safely with mutable fields.
@dataclass(eq=False)
class Pet:
    name: str
    age: int
    species: str
    breed: str
    owners: set[Owner] = field(default_factory=set)
    tasks: list[Task] = field(default_factory=list)

    def add_owner(self, owner: Owner) -> None:
        """Link this pet to an owner, updating both sides of the relationship."""
        self.owners.add(owner)
        owner.pets.add(self)

    def remove_owner(self, owner: Owner) -> None:
        """Unlink this pet from an owner, updating both sides of the relationship."""
        self.owners.discard(owner)
        owner.pets.discard(self)

    def add_task(self, task: Task) -> None:
        """Add a task to this pet, taking ownership of the task's pet reference."""
        # Keep the Pet<->Task backreference consistent, the same way
        # add_owner/add_pet keep the Owner<->Pet sides in sync.
        if task.pet is not self:
            if task in task.pet.tasks:
                task.pet.tasks.remove(task)
            task.pet = self
        if task not in self.tasks:
            self.tasks.append(task)

    def get_tasks(self) -> list[Task]:
        """Return a copy of this pet's task list."""
        return list(self.tasks)


@dataclass
class Task:
    name: str
    priority: Priority
    frequency: str
    deadline: datetime
    duration_minutes: int
    task_type: TaskType
    pet: Pet
    is_completed: bool = False

    def remove_task(self) -> None:
        """Remove this task from its pet's task list."""
        self.pet.tasks.remove(self)

    def mark_complete(self) -> None:
        """Mark this task as completed."""
        self.is_completed = True

    def is_due(self) -> bool:
        """Return whether this task's deadline has passed."""
        return datetime.now() >= self.deadline

    def get_time_required(self) -> int:
        """Return the task's required duration in minutes."""
        return self.duration_minutes


@dataclass
class ScheduledTask:
    task: Task
    start_time: time
    end_time: time
    rationale: str
    duration_minutes: int = 0

    def get_duration(self) -> int:
        """Return the scheduled duration in minutes."""
        return self.duration_minutes


# ---------------------------------------------------------------------------
# Regular classes  (Owner, DailyPlan, Scheduler)
# ---------------------------------------------------------------------------

class Owner:
    def __init__(self, name: str, availability: dict, preferences: list[str]) -> None:
        """Initialize an owner with availability, preferences, and no pets yet."""
        self.name = name
        # availability format: {"HH:MM": "HH:MM"}  (window start -> window end)
        self.availability = availability
        self.preferences = preferences
        self.pets: set[Pet] = set()
        self.daily_plan: Optional[DailyPlan] = None

    def add_pet(self, pet: Pet) -> None:
        """Link a pet to this owner, updating both sides of the relationship."""
        self.pets.add(pet)
        pet.owners.add(self)

    def remove_pet(self, pet: Pet) -> None:
        """Unlink a pet from this owner, updating both sides of the relationship."""
        self.pets.discard(pet)
        pet.owners.discard(self)

    def update_availability(self, time_slots: dict) -> None:
        """Merge new time slots into this owner's availability."""
        self.availability.update(time_slots)

    def get_schedule(self) -> Optional[DailyPlan]:
        """Return this owner's current daily plan, if one has been generated."""
        return self.daily_plan


class DailyPlan:
    def __init__(self, plan_date: date) -> None:
        """Initialize an empty plan for the given date."""
        self.plan_date = plan_date
        self.scheduled_tasks: list[ScheduledTask] = []
        self.total_time_minutes: int = 0

    def add_scheduled_task(self, scheduled_task: ScheduledTask) -> None:
        """Add a scheduled task to the plan and update the total time."""
        self.scheduled_tasks.append(scheduled_task)
        self.total_time_minutes += scheduled_task.get_duration()

    def get_summary(self) -> str:
        """Return a human-readable summary of the plan."""
        header = (
            f"Daily Plan for {self.plan_date} — "
            f"{len(self.scheduled_tasks)} tasks, {self.total_time_minutes} min total"
        )
        lines = [header]
        for st in self.scheduled_tasks:
            lines.append(
                f"  {st.start_time.strftime('%H:%M')}–{st.end_time.strftime('%H:%M')} "
                f"[{st.task.priority.value}] {st.task.name} ({st.task.pet.name})"
            )
        return "\n".join(lines)

    def get_explanation(self) -> str:
        """Return the rationale behind each scheduled task."""
        lines = ["Schedule rationale:"]
        for st in self.scheduled_tasks:
            lines.append(f"  {st.task.name}: {st.rationale}")
        return "\n".join(lines)


class Scheduler:
    def __init__(self, owner: Owner, pets: list[Pet]) -> None:
        """Initialize the scheduler and flatten the managed pets' tasks."""
        self.owner = owner
        self.pets = pets
        self.daily_plan: Optional[DailyPlan] = None
        self.explanation: str = ""
        # Flatten tasks from all managed pets into a single list.
        # self.pets (not owner.pets) is used: Scheduler manages a specific
        # ordered subset, while owner.pets is an unordered set of all pets.
        self.tasks: list[Task] = [t for pet in self.pets for t in pet.get_tasks()]

    def _refresh_tasks(self) -> None:
        """Rebuild the task list from the managed pets' current tasks."""
        self.tasks = [t for pet in self.pets for t in pet.get_tasks()]

    def create_schedule(self) -> DailyPlan:
        """Build and return today's daily plan from the owner's availability."""
        self._refresh_tasks()
        plan = DailyPlan(date.today())
        today = date.today()
        # Only tasks due today or already overdue belong in today's plan; a task
        # deadline dated for a future day doesn't need a slot yet. (Previously the
        # date component of `deadline` was ignored entirely and only the
        # time-of-day was compared, so future-dated tasks leaked into today's plan.)
        ordered = [
            t for t in self.prioritize_tasks()
            if not t.is_completed and t.deadline.date() <= today and self.check_constraints(t)
        ]
        scheduled_ids: set[int] = set()

        for start_str, end_str in self.owner.availability.items():
            cursor = datetime.combine(today, datetime.strptime(start_str, "%H:%M").time())
            window_end = datetime.combine(today, datetime.strptime(end_str, "%H:%M").time())

            for task in ordered:
                if id(task) in scheduled_ids:
                    continue
                # Only place a task in a window whose end time is on or after the task's
                # target time-of-day. This prevents an "Evening Feeding" (deadline 17:30)
                # from being scheduled at 7 AM.
                if task.deadline.time() > window_end.time():
                    continue
                task_end = cursor + timedelta(minutes=task.duration_minutes)
                if task_end <= window_end:
                    overdue = " (OVERDUE)" if task.deadline.date() < today else ""
                    rationale = (
                        f"Priority {task.priority.value}, "
                        f"due {task.deadline.strftime('%Y-%m-%d %H:%M')}{overdue}"
                    )
                    plan.add_scheduled_task(
                        ScheduledTask(task, cursor.time(), task_end.time(), rationale, task.duration_minutes)
                    )
                    scheduled_ids.add(id(task))
                    cursor = task_end

        self.daily_plan = plan
        self.owner.daily_plan = plan
        self.explanation = plan.get_explanation()
        return plan

    def add_task(self, task: Task) -> None:
        """Add a task via its pet so it persists across task-list refreshes."""
        # Route through the pet so the task survives the next _refresh_tasks().
        task.pet.add_task(task)
        if task not in self.tasks:
            self.tasks.append(task)

    def remove_task(self, task: Task) -> None:
        """Remove a task via its pet so it doesn't reappear after a refresh."""
        # Remove from the pet too, otherwise _refresh_tasks() would resurrect it.
        task.remove_task()
        if task in self.tasks:
            self.tasks.remove(task)

    def _matches_preference(self, task: Task) -> bool:
        """Return whether a task matches one of the owner's stated preferences."""
        haystacks = (task.task_type.name, task.task_type.value, task.name)
        return any(
            h.lower() in pref.lower() or pref.lower() in h.lower()
            for pref in self.owner.preferences
            for h in haystacks
        )

    def prioritize_tasks(self) -> list[Task]:
        """Return tasks sorted by priority, then preference match, then deadline."""
        # Within the same priority tier, tasks matching an owner preference
        # (e.g. "evening feeding") sort ahead of ones that don't.
        return sorted(
            self.tasks,
            key=lambda t: (_PRIORITY_ORDER[t.priority], not self._matches_preference(t), t.deadline),
        )

    def check_constraints(self, task: Task) -> bool:
        """Return whether a task can feasibly fit in the owner's availability."""
        if task.is_completed:
            return False
        if not self.owner.availability:
            return False
        longest_window = max(
            (datetime.strptime(end, "%H:%M") - datetime.strptime(start, "%H:%M")).total_seconds() / 60
            for start, end in self.owner.availability.items()
        )
        return task.duration_minutes <= longest_window

    def explain_plan(self) -> str:
        """Return the explanation for the most recently generated plan."""
        return self.explanation if self.explanation else "No plan generated yet."
