# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

- Briefly describe your initial UML design.
- What classes did you include, and what responsibilities did you assign to each?
    - Classes:
        - Animal 
            - attributes: name, age, type of animal, Set of Owners
            - methods: constructor
        - Owner
            - attributes: name, availability, preferences, Set of Pets
            - methods: constructor, add pet, remove pet, update availability
        - Task
            - attributes: name, priority, frequency, deadline
            - methods: constructor, remove task
        - Scheduler
            - attributes: list of tasks
            - methods: constructor, create schedule

**b. Design changes**

- Did your design change during implementation?
- If yes, describe at least one change and why you made it.

Yes, the design changed significantly during implementation:

1. **`Animal` → `Pet` (renamed and expanded):** The initial `Animal` class was renamed to `Pet` and gained two new attributes (`species`, `breed`) for more specific identification, plus a `tasks: list[Task]` field. This made `Pet` an active participant in task management rather than a passive data holder, which simplified lookups like "what does this pet need today?"

2. **`Task` gained a back-reference to `Pet`:** In the initial design, `Task` was standalone. During implementation, `Task` received a `pet: Pet` field so that any task knows which animal it belongs to without needing to search through all pets. This creates a bidirectional relationship that requires careful synchronization in `Pet.add_task()`.

3. **Two new classes: `ScheduledTask` and `DailyPlan`:** The initial design had `Scheduler` produce a schedule as an opaque output. Splitting that into `ScheduledTask` (a task pinned to a specific time window with a rationale) and `DailyPlan` (a container for all scheduled tasks on a given date) made the output structured and inspectable, and gave `Owner.get_schedule()` a concrete return type.

4. **`Task` gained richer state:** `duration_minutes`, `task_type` (enum), `is_completed`, and methods like `mark_complete()`, `is_due()`, and `get_time_required()` were all absent from the initial design. These were necessary once scheduling needed to reason about time constraints and completion tracking.

5. **`Scheduler` gained a direct relationship to `Pet`:** The initial design only gave `Scheduler` a list of tasks. During implementation, `Scheduler` also received a `pets: list[Pet]` field so it can look up all tasks across pets directly, rather than reconstructing that list from the task records alone. This also makes the `Scheduler → Pet` relationship explicit in the UML rather than implied.

6. **`ScheduledTask.get_duration()` simplified with a stored attribute:** The original `get_duration()` computed duration by promoting `start_time` and `end_time` to full `datetime` objects (via `datetime.combine`) just to subtract them. This was unnecessarily complex — `duration_minutes` is already known at scheduling time from `task.duration_minutes`. Adding `duration_minutes: int` as a direct field on `ScheduledTask` made `get_duration()` a simple return, removed the dependency on `date.today()`, and made the value immediately readable without recomputation.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

The scheduler considers three constraints: the owner's **available time windows** (`Owner.availability`), each task's **priority** (HIGH/MEDIUM/LOW), and the owner's **stated preferences** (free-text strings matched against a task's type/name in `_matches_preference`). `check_constraints()` also filters out tasks that couldn't fit in any window at all, so `create_schedule()` never tries to place something impossible.

Priority mattered most because it's the one constraint a pet owner would expect to never be silently violated — a HIGH-priority medication task should never lose its slot to a LOW-priority play session just because play was requested first. Preference match is a tiebreaker within a priority tier, not a constraint that can override priority, since "the owner likes mornings" is a nice-to-have, not a hard requirement the way "give the medication" is.

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

`detect_conflicts()` flags overlapping `[deadline, deadline + duration]` windows on the *raw requested* tasks, independent of whatever `create_schedule()` ultimately does with them. That means the schedule itself is always conflict-free (tasks are packed sequentially into a window, one after another), but the warning can still fire even when the final plan has no actual overlap — e.g. two tasks both "due at 17:30" get a conflict warning even though the plan places one at 17:30 and the next right after it finishes. This is a deliberate tradeoff: a schedule-aware conflict check would be more precise, but it would also hide a real signal from the owner — "you asked for two things at the same moment" is useful information even if the scheduler quietly resolved it by delaying one of them. For a small daily task list, over-warning is safer than under-warning.

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?
- Which AI coding assistant features were most effective for building your scheduler?
- How did using separate chat sessions for different phases help you stay organized?

I used AI across every phase: brainstorming the initial class list from the scenario description, converting that design into Python dataclasses/stubs, implementing the scheduling algorithms incrementally, and — in this final pass — wiring the Streamlit UI to the actual `Scheduler` methods, updating the UML to match the real code, and drafting this documentation.

The most effective feature by far was **giving the assistant direct tool access to run the code** rather than just asking it to reason about correctness in the abstract. For the UI step specifically, the assistant used Streamlit's headless `AppTest` harness to actually click "Add task" and "Generate schedule" inside the running app and read back what rendered — that's what caught a real bug (see below) that a pure code-read would have missed. Asking narrow, concrete questions ("does this UI actually show a conflict when I add two overlapping tasks?") produced much more useful results than open-ended ones ("does this look right?").

Separate chat sessions per phase (design → implementation → UI/polish) kept each conversation focused on one concern, so the assistant wasn't re-deriving the whole system's context every time, and I could review/accept one phase's output before the next phase built on top of it — e.g. the UML wasn't finalized until the implementation it was supposed to describe actually existed.

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?
- Give one example of an AI suggestion you rejected or modified to keep your system design clean.
- What did you learn about being the "lead architect" when collaborating with powerful AI tools?

While wiring up `app.py`, I asked the assistant to verify the conflict-warning feature actually worked, not just assume the existing `Scheduler.detect_conflicts()` code was correct because it had unit tests. It ran the app headlessly, added two tasks with identical fields, and found that only one ever showed up — `Pet.add_task()`'s `if task not in self.tasks` check was silently deduplicating tasks, because `Task` was a plain `@dataclass` with value-based equality (two tasks with the same name/priority/deadline/etc. compared as equal, even though they were meant to be two separate real-world tasks). `Pet` already avoided this exact trap with `eq=False`, but `Task` never got the same treatment. I had the assistant apply the same fix to `Task` rather than working around it in the UI (e.g. tagging each task with a unique ID), since the identity-based fix matches the pattern already established for `Pet` and fixes the bug at its source instead of papering over it in every caller.

The key lesson: an AI assistant will confidently report "tests pass" and stop there, but passing tests only prove the *cases someone thought to write*. Being the lead architect meant pushing past "does the existing test suite pass" to "does the feature I'm about to advertise in the README actually behave correctly when I use it the way a real pet owner would" — and treating a clean test run as a starting point for verification, not the end of it.

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

`tests/test_pawpal.py` covers sorting (chronological order, and recurring tasks sharing a time-of-day but landing on a future date), recurrence (daily/weekly spawning, one-off tasks spawning nothing, immediate registration on completion), conflict detection (identical start times, back-to-back non-conflicts, completed tasks excluded), and the edge case of a pet with no tasks. These matter because they're exactly the places where a naive implementation looks right on the happy path but breaks silently — e.g. sorting by time-of-day alone would interleave today's breakfast with next week's, which wouldn't show up unless you specifically test a recurring task against a same-time non-recurring one.

Separately, in this final UI/polish pass, I verified `app.py` itself using Streamlit's headless `AppTest` harness (no automated test file yet, but exercised the button flows for add-task, generate-schedule, mark-complete, and filtering). That's how the `Task` equality bug (described above) was actually caught — the pytest suite never exercised "add two tasks with identical fields," because none of the fixtures happened to do that.

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

I'm confident in the specific behaviors that are covered — sorting, recurrence, and conflict detection all have both a passing test and, now, a real UI reproduction. I'm less confident in `create_schedule()`'s full multi-window packing logic and `prioritize_tasks()`'s three-way tiebreak (priority, then preference, then deadline), since those are only exercised indirectly through `main.py`'s sample scenario, not through dedicated unit tests. If I had more time, I'd add: an automated `AppTest`-based test file for `app.py` so the UI flows aren't only manually verified once; a test for `prioritize_tasks()` with tasks that differ only in preference match; and a case where availability windows are too small for any task to fit, to confirm `check_constraints()` and the "no tasks could be scheduled" UI path both behave correctly.

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

I'm most satisfied with the conflict-detection design: sorting requested tasks by start time and sweeping once (`detect_conflicts()`) instead of comparing every pair keeps it O(n log n), it always returns a list of strings instead of raising, and it now visibly surfaces in the UI as a `st.warning` per conflict — the algorithm, the test coverage, and the user-facing behavior all actually line up.

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

I'd add automated tests for `app.py` (using `AppTest`) instead of relying on one-off manual verification, and I'd make recurrence weekday-aware (e.g. "every Monday") rather than a fixed `timedelta` offset, since a real pet owner's routine is usually pinned to specific days, not "N days after whenever it was last completed."

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?

The AI assistant is very good at producing code that *looks* internally consistent — the right method names, reasonable docstrings, tests that pass — but "internally consistent" isn't the same as "correct in practice." The `Task` equality bug this session is the clearest example: nothing about it looked wrong on a read-through, and the existing test suite was green. It only surfaced because we actually ran the UI and checked what a user would see. Being the lead architect means treating the AI's output as a strong first draft and your own end-to-end verification — not just the diff, not just the test run — as the actual bar for "done."
