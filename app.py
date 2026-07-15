import streamlit as st
from datetime import date, datetime, time as time_cls

from pawpal_system import Owner, Pet, Task, Priority, TaskType, Scheduler

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")
st.caption("A pet care planning assistant — sorts, prioritizes, and flags conflicts in your daily task list.")

# ---------------------------------------------------------------------------
# Session state setup (Owner + Pets persist across reruns)
# ---------------------------------------------------------------------------

if "owner" not in st.session_state:
    st.session_state.owner = Owner(
        name="Jordan",
        availability={"07:00": "09:00", "17:00": "19:00"},
        preferences=["morning walks", "evening feeding"],
    )
owner = st.session_state.owner

if "pets" not in st.session_state:
    buddy = Pet(name="Buddy", age=3, species="Dog", breed="Golden Retriever")
    owner.add_pet(buddy)
    st.session_state.pets = [buddy]
pets = st.session_state.pets

# ---------------------------------------------------------------------------
# Owner settings: availability + preferences drive the Scheduler's constraints
# ---------------------------------------------------------------------------

with st.expander("👤 Owner settings", expanded=False):
    owner.name = st.text_input("Owner name", value=owner.name)

    st.caption("Availability windows — the Scheduler only places tasks inside these.")
    windows = list(owner.availability.items())
    col_a, col_b = st.columns(2)
    with col_a:
        morning_start = st.time_input("Morning start", value=datetime.strptime(windows[0][0], "%H:%M").time())
        morning_end = st.time_input("Morning end", value=datetime.strptime(windows[0][1], "%H:%M").time())
    with col_b:
        evening_start = st.time_input("Evening start", value=datetime.strptime(windows[1][0], "%H:%M").time())
        evening_end = st.time_input("Evening end", value=datetime.strptime(windows[1][1], "%H:%M").time())
    owner.availability = {
        morning_start.strftime("%H:%M"): morning_end.strftime("%H:%M"),
        evening_start.strftime("%H:%M"): evening_end.strftime("%H:%M"),
    }

    prefs_text = st.text_input(
        "Preferences (comma-separated)", value=", ".join(owner.preferences)
    )
    owner.preferences = [p.strip() for p in prefs_text.split(",") if p.strip()]

with st.expander("🐶 Pets", expanded=False):
    new_pet_name = st.text_input("New pet name", key="new_pet_name")
    new_pet_species = st.selectbox("Species", ["dog", "cat", "other"], key="new_pet_species")
    if st.button("Add pet") and new_pet_name:
        pet = Pet(name=new_pet_name, age=0, species=new_pet_species, breed="")
        owner.add_pet(pet)
        pets.append(pet)
    st.write("Current pets: " + ", ".join(p.name for p in pets))

st.divider()

# ---------------------------------------------------------------------------
# Add a task
# ---------------------------------------------------------------------------

st.subheader("Add a task")
pet_names = [p.name for p in pets]
selected_pet_name = st.selectbox("For pet", pet_names)
selected_pet = next(p for p in pets if p.name == selected_pet_name)

col1, col2, col3 = st.columns(3)
with col1:
    task_title = st.text_input("Task title", value="Morning walk")
with col2:
    duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
with col3:
    priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)

col4, col5, col6 = st.columns(3)
with col4:
    task_type_name = st.selectbox("Task type", [t.name for t in TaskType])
with col5:
    deadline_time = st.time_input("Deadline (time of day)", value=time_cls(17, 0))
with col6:
    frequency = st.selectbox("Frequency", ["once", "daily", "weekly"])

if st.button("Add task"):
    task = Task(
        name=task_title,
        priority=Priority[priority.upper()],
        frequency=frequency,
        deadline=datetime.combine(date.today(), deadline_time),
        duration_minutes=int(duration),
        task_type=TaskType[task_type_name],
        pet=selected_pet,
    )
    selected_pet.add_task(task)

st.divider()

# ---------------------------------------------------------------------------
# Task list — filter + mark complete, backed by Scheduler.filter_tasks()
# ---------------------------------------------------------------------------

scheduler = Scheduler(owner, pets)

st.subheader("Tasks")
if scheduler.tasks:
    filt_col1, filt_col2 = st.columns(2)
    with filt_col1:
        status_filter = st.selectbox("Status", ["All", "Incomplete", "Completed"])
    with filt_col2:
        pet_filter = st.selectbox("Pet", ["All pets"] + pet_names)

    filtered = scheduler.filter_tasks(
        is_completed={"All": None, "Incomplete": False, "Completed": True}[status_filter],
        pet_name=None if pet_filter == "All pets" else pet_filter,
    )

    for t in filtered:
        row = st.columns([4, 2, 2, 2, 1])
        row[0].write(f"**{t.name}** ({t.pet.name})")
        row[1].write(t.priority.value)
        row[2].write(t.deadline.strftime("%Y-%m-%d %H:%M"))
        row[3].write("✅ done" if t.is_completed else "○ pending")
        if not t.is_completed and row[4].button("Complete", key=f"complete-{id(t)}"):
            next_task = scheduler.mark_task_complete(t)
            if next_task is not None:
                st.success(f"Completed '{t.name}'. Next occurrence scheduled for {next_task.deadline.strftime('%Y-%m-%d %H:%M')}.")
            else:
                st.success(f"Completed '{t.name}'.")
else:
    st.info("No tasks yet. Add one above.")

st.divider()

# ---------------------------------------------------------------------------
# Build schedule — surfaces sort_by_time(), prioritize_tasks(), detect_conflicts()
# ---------------------------------------------------------------------------

st.subheader("Build today's schedule")

if st.button("Generate schedule", type="primary"):
    plan = scheduler.create_schedule()
    st.session_state.last_plan = plan
    st.session_state.last_conflicts = scheduler.conflicts

if "last_plan" in st.session_state:
    plan = st.session_state.last_plan
    conflicts = st.session_state.get("last_conflicts", [])

    if conflicts:
        st.warning(f"⚠️ {len(conflicts)} scheduling conflict(s) detected — review before you commit to this plan.")
        for warning in conflicts:
            st.warning(warning)
        st.caption("Consider moving one of the conflicting tasks to a different time, or reassigning it to someone else.")
    else:
        st.success("✅ No scheduling conflicts — every task has a clear time slot.")

    if plan.scheduled_tasks:
        st.table(
            [
                {
                    "Time": f"{st.start_time.strftime('%H:%M')}–{st.end_time.strftime('%H:%M')}",
                    "Task": st.task.name,
                    "Pet": st.task.pet.name,
                    "Priority": st.task.priority.value,
                    "Type": st.task.task_type.value,
                }
                for st in plan.scheduled_tasks
            ]
        )
        st.caption(f"Total: {len(plan.scheduled_tasks)} tasks, {plan.total_time_minutes} minutes.")
    else:
        st.info("No tasks could be scheduled in the current availability windows.")

    with st.expander("Why this schedule? (rationale per task)"):
        st.text(plan.get_explanation())

st.divider()

# ---------------------------------------------------------------------------
# Sorted / prioritized views — surfaces Scheduler.sort_by_time() / prioritize_tasks()
# ---------------------------------------------------------------------------

st.subheader("Other views")
view = st.radio("Show tasks", ["Sorted by time", "Sorted by priority + preference"], horizontal=True)

ordered = scheduler.sort_by_time() if view == "Sorted by time" else scheduler.prioritize_tasks()
if ordered:
    st.table(
        [
            {
                "Deadline": t.deadline.strftime("%Y-%m-%d %H:%M"),
                "Task": t.name,
                "Pet": t.pet.name,
                "Priority": t.priority.value,
                "Status": "done" if t.is_completed else "pending",
            }
            for t in ordered
        ]
    )
else:
    st.info("No tasks to show yet.")
