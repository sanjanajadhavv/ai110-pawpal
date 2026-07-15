# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.

## ✨ Features

- **Priority + preference sorting** — `Scheduler.prioritize_tasks()` orders tasks by priority (HIGH → MEDIUM → LOW) first, then by whether they match one of the owner's stated preferences (e.g. "evening feeding"), then by deadline. This is the order used to fill the day's availability windows.
- **Chronological sorting** — `Scheduler.sort_by_time()` orders every task by its full deadline (date + time), so a recurring task's next occurrence lands after today's tasks instead of interleaving by time-of-day alone.
- **Conflict warnings** — `Scheduler.detect_conflicts()` flags any two incomplete tasks whose `[deadline, deadline + duration]` windows overlap, regardless of which pet they belong to, since the owner can't physically do both at once.
- **Daily/weekly recurrence** — `Task.mark_complete()` automatically spawns the next occurrence of a "daily" or "weekly" task, attached to the same pet, when the current one is completed.
- **Availability-aware scheduling** — `Scheduler.create_schedule()` packs prioritized tasks into the owner's actual free time windows, skips tasks that don't fit (`check_constraints()`), and labels overdue tasks.
- **Filtering** — `Scheduler.filter_tasks(is_completed=..., pet_name=...)` returns tasks matching completion status and/or a specific pet.
- **Plan explanation** — `DailyPlan.get_explanation()` / `Scheduler.explain_plan()` surface the reasoning (priority, due date/time, overdue status) behind every scheduled task.

## 🖥️ Sample Output

```============================================================
  PawPal — Today's Schedule for Jordan
  Wednesday, July 15 2026
  Available: 07:00 AM – 09:00 AM, 05:00 PM – 07:00 PM
============================================================
  ○ 07:00 AM – 07:10 AM  |  FEEDING       Breakfast               [HIGH]  (Buddy)
  ○ 07:10 AM – 07:40 AM  |  WALK          Morning Walk            [HIGH]  (Buddy)
  ○ 07:40 AM – 07:45 AM  |  MEDICATION    Hairball Medication     [MEDIUM]  (Whiskers)
  ○ 05:00 PM – 05:10 PM  |  FEEDING       Evening Feeding         [HIGH]  (Whiskers)
  ○ 05:10 PM – 05:25 PM  |  GROOMING      Evening Brushing        [LOW]  (Buddy)
  ○ 05:25 PM – 05:45 PM  |  PLAY          Fetch & Play            [LOW]  (Buddy)
------------------------------------------------------------
  Total tasks: 6   |   Total time: 90 min
============================================================

Scheduling conflicts:
  ⚠ Conflict: 'Evening Brushing' (Buddy) at 17:30 overlaps 'Evening Feeding' (Whiskers) at 17:30.

Completed 'Breakfast' — next occurrence spawned for 2026-07-16 07:30.

Tasks sorted by time:
  2026-07-15 07:30  Breakfast              (Buddy)
  2026-07-15 08:00  Morning Walk           (Buddy)
  2026-07-15 08:30  Hairball Medication    (Whiskers)
  2026-07-15 17:30  Evening Brushing       (Buddy)
  2026-07-15 17:30  Evening Feeding        (Whiskers)
  2026-07-15 18:00  Fetch & Play           (Buddy)
  2026-07-16 07:30  Breakfast              (Buddy)

Incomplete tasks:
  Morning Walk           (Buddy)
  Fetch & Play           (Buddy)
  Evening Brushing       (Buddy)
  Hairball Medication    (Whiskers)
  Evening Feeding        (Whiskers)
  Breakfast              (Buddy)

Completed tasks:
  Breakfast              (Buddy)

Buddy's tasks:
  Morning Walk           [HIGH]
  Breakfast              [HIGH]
  Fetch & Play           [LOW]
  Evening Brushing       [LOW]
  Breakfast              [HIGH]
```

## 🧪 Testing PawPal+

```bash
# Run the full test suite:
python -m pytest

# Run with coverage:
python -m pytest --cov

```

Sample test output:

```
............                                                                                                 [100%]

========================================================== 12 passed in 0.01s ===========================================================
```

The suite (`tests/test_pawpal.py`) covers 12 cases across three behaviors, plus a couple of the original smoke tests:

- **Sorting** — chronological ordering, and the trickier case of a recurring task's next occurrence sharing today's clock time but landing on a future date (sorts by full `deadline`, not time-of-day).
- **Recurrence** — daily → next-day spawn, weekly → next-week spawn, one-off tasks spawning nothing, and the scheduler registering a new occurrence immediately on completion.
- **Conflict detection** — two tasks at the identical start time, back-to-back tasks that shouldn't conflict, and completed tasks correctly excluded from the check.
- **Edge case** — a pet with no tasks returns empty lists everywhere instead of raising.

**Confidence Level: ⭐⭐⭐⭐☆ (4/5)**

The core scheduling logic (sorting, recurrence, conflict detection) is well covered and all tests pass. Confidence isn't higher because `create_schedule()` end-to-end (multi-window packing, `check_constraints`, overdue-task labeling), `prioritize_tasks()`'s priority/preference/deadline ordering, and the Streamlit UI (`app.py`) have no test coverage yet — the risk of a regression there is unverified, not just unlikely.

## 📐 Smarter Scheduling

| Feature | Method(s) | Notes |
|---------|-----------|-------|
| Task sorting | `Scheduler.sort_by_time()` | Returns all tasks sorted by their full `deadline` (earliest first). Sorting on the whole datetime — not just time-of-day — matters once recurring tasks exist, since a task's next occurrence lands on a later date but can share the same clock time as today's. |
| Filtering | `Scheduler.filter_tasks(is_completed=None, pet_name=None)` | Returns tasks matching either or both criteria — completion status and/or the owning pet's name — so a caller can ask for e.g. "everything still open for Buddy" without writing a list comprehension. |
| Conflict detection | `Scheduler.detect_conflicts()` | Flags any two (incomplete) tasks whose requested `[deadline, deadline + duration]` windows overlap, regardless of which pet they belong to — the owner physically can't do two things at once. It sorts tasks by start time and sweeps once, so it's O(n log n) rather than checking every pair, and it always returns a list of warning strings instead of raising, so a conflict never crashes the schedule build. `Scheduler.create_schedule()` recomputes this list (`scheduler.conflicts`) on every call. |
| Recurring tasks | `Task.mark_complete()`, `Task._spawn_next_occurrence()`, `Scheduler.mark_task_complete()` | Completing a task with `frequency` of `"daily"` or `"weekly"` automatically creates the next occurrence via `deadline + timedelta(...)` and attaches it to the same pet. `timedelta` arithmetic (rather than manually incrementing date fields) keeps the date math correct across month/year boundaries. `Scheduler.mark_task_complete()` is the entry point to use from a scheduler so the new occurrence is registered in `scheduler.tasks` immediately, without waiting for the next `create_schedule()` refresh. |

## 📸 Demo Walkthrough

### Main UI features (`app.py`)

- **Owner settings** — edit the owner's name, two daily availability windows (morning/evening), and a comma-separated list of preferences. These directly feed `Scheduler.check_constraints()` and `prioritize_tasks()`.
- **Pets** — add one or more pets by name and species.
- **Add a task** — pick a pet, then set the task's title, duration, priority, type, deadline time, and frequency (once/daily/weekly).
- **Task list** — filter tasks by status (all/incomplete/completed) and by pet, and mark any task complete with a button.
- **Build today's schedule** — generates the day's plan and displays it as a table, along with conflict warnings and a "why this schedule?" rationale expander.
- **Other views** — toggle between "sorted by time" and "sorted by priority + preference" to see the underlying orderings the Scheduler produces.

### Example workflow

1. Open the app and expand **Owner settings** to confirm Jordan's availability (07:00–09:00, 17:00–19:00) and preferences.
2. Add a pet, e.g. "Whiskers" (cat).
3. Add a task for Buddy: "Morning Walk", 30 minutes, HIGH priority, WALK, deadline 08:00, frequency daily.
4. Add a second task for Whiskers with a deadline that overlaps an existing one (e.g. 17:30) to see conflict detection in action.
5. Click **Generate schedule** — the app shows a `st.warning` for the overlap (or a `st.success` if the day is conflict-free), then a table of time-boxed tasks.
6. Mark a task complete — if it's "daily" or "weekly", the next occurrence appears automatically in the task list.
7. Switch **Other views** to compare "sorted by time" vs. "sorted by priority + preference".

### Key Scheduler behaviors shown

- **Sorting**: the "Other views" tables demonstrate `sort_by_time()` (chronological) vs. `prioritize_tasks()` (priority, then preference match, then deadline) producing different orderings for the same task list.
- **Conflict warnings**: two tasks with overlapping `[deadline, deadline + duration]` windows trigger a dedicated warning per conflict, plus a summary count — surfaced with `st.warning` rather than buried in a table, since a pet owner needs to notice it before trusting the plan.
- **Recurrence**: completing a "daily"/"weekly" task immediately shows its spawned next occurrence in the task list, without needing to regenerate the schedule.

### Sample CLI output (`python main.py`)

```
============================================================
  PawPal — Today's Schedule for Jordan
  Wednesday, July 15 2026
  Available: 07:00 AM – 09:00 AM, 05:00 PM – 07:00 PM
============================================================
  ○ 07:00 AM – 07:10 AM  |  FEEDING       Breakfast               [HIGH]  (Buddy)
  ○ 07:10 AM – 07:40 AM  |  WALK          Morning Walk            [HIGH]  (Buddy)
  ○ 07:40 AM – 07:45 AM  |  MEDICATION    Hairball Medication     [MEDIUM]  (Whiskers)
  ○ 05:00 PM – 05:10 PM  |  FEEDING       Evening Feeding         [HIGH]  (Whiskers)
  ○ 05:10 PM – 05:25 PM  |  GROOMING      Evening Brushing        [LOW]  (Buddy)
  ○ 05:25 PM – 05:45 PM  |  PLAY          Fetch & Play            [LOW]  (Buddy)
------------------------------------------------------------
  Total tasks: 6   |   Total time: 90 min
============================================================

Scheduling conflicts:
  ⚠ Conflict: 'Evening Brushing' (Buddy) at 17:30 overlaps 'Evening Feeding' (Whiskers) at 17:30.

Completed 'Breakfast' — next occurrence spawned for 2026-07-16 07:30.

Tasks sorted by time:
  2026-07-15 07:30  Breakfast              (Buddy)
  2026-07-15 08:00  Morning Walk           (Buddy)
  2026-07-15 08:30  Hairball Medication    (Whiskers)
  2026-07-15 17:30  Evening Brushing       (Buddy)
  2026-07-15 17:30  Evening Feeding        (Whiskers)
  2026-07-15 18:00  Fetch & Play           (Buddy)
  2026-07-16 07:30  Breakfast              (Buddy)

Incomplete tasks:
  Morning Walk           (Buddy)
  Fetch & Play           (Buddy)
  Evening Brushing       (Buddy)
  Hairball Medication    (Whiskers)
  Evening Feeding        (Whiskers)
  Breakfast              (Buddy)

Completed tasks:
  Breakfast              (Buddy)

Buddy's tasks:
  Morning Walk           [HIGH]
  Breakfast              [HIGH]
  Fetch & Play           [LOW]
  Evening Brushing       [LOW]
  Breakfast              [HIGH]
```

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->
