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

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
