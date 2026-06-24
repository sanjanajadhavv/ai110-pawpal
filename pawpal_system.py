from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, time
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


# ---------------------------------------------------------------------------
# Dataclasses  (Pet, Task, ScheduledTask)
# ---------------------------------------------------------------------------

@dataclass
class Pet:
    name: str
    age: int
    species: str
    breed: str
    owners: set[Owner] = field(default_factory=set)
    tasks: list[Task] = field(default_factory=list)

    def add_owner(self, owner: Owner) -> None:
        pass

    def remove_owner(self, owner: Owner) -> None:
        pass

    def add_task(self, task: Task) -> None:
        pass

    def get_tasks(self) -> list[Task]:
        pass


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
        pass

    def mark_complete(self) -> None:
        pass

    def is_due(self) -> bool:
        pass

    def get_time_required(self) -> int:
        pass


@dataclass
class ScheduledTask:
    task: Task
    start_time: time
    end_time: time
    rationale: str

    def get_duration(self) -> int:
        pass


# ---------------------------------------------------------------------------
# Regular classes  (Owner, DailyPlan, Scheduler)
# ---------------------------------------------------------------------------

class Owner:
    def __init__(self, name: str, availability: dict, preferences: list[str]) -> None:
        self.name = name
        self.availability = availability
        self.preferences = preferences
        self.pets: set[Pet] = set()

    def add_pet(self, pet: Pet) -> None:
        pass

    def remove_pet(self, pet: Pet) -> None:
        pass

    def update_availability(self, time_slots: dict) -> None:
        pass

    def get_schedule(self) -> DailyPlan:
        pass


class DailyPlan:
    def __init__(self, plan_date: date) -> None:
        self.plan_date = plan_date
        self.scheduled_tasks: list[ScheduledTask] = []
        self.total_time_minutes: int = 0

    def add_scheduled_task(self, task: ScheduledTask) -> None:
        pass

    def get_summary(self) -> str:
        pass

    def get_explanation(self) -> str:
        pass


class Scheduler:
    def __init__(self, owner: Owner, pets: list[Pet]) -> None:
        self.tasks: list[Task] = []
        self.owner = owner
        self.pets = pets
        self.daily_plan: Optional[DailyPlan] = None
        self.explanation: str = ""

    def create_schedule(self) -> DailyPlan:
        pass

    def add_task(self, task: Task) -> None:
        pass

    def remove_task(self, task: Task) -> None:
        pass

    def prioritize_tasks(self) -> list[Task]:
        pass

    def check_constraints(self, task: Task) -> bool:
        pass

    def explain_plan(self) -> str:
        pass
