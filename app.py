import streamlit as st
from datetime import date, datetime, time as time_cls

from pawpal_system import Owner, Pet, Task, Priority, TaskType, Scheduler

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")

st.markdown(
    """
Welcome to the PawPal+ starter app.

This file is intentionally thin. It gives you a working Streamlit app so you can start quickly,
but **it does not implement the project logic**. Your job is to design the system and build it.

Use this app as your interactive demo once your backend classes/functions exist.
"""
)

with st.expander("Scenario", expanded=True):
    st.markdown(
        """
**PawPal+** is a pet care planning assistant. It helps a pet owner plan care tasks
for their pet(s) based on constraints like time, priority, and preferences.

You will design and implement the scheduling logic and connect it to this Streamlit UI.
"""
    )

with st.expander("What you need to build", expanded=True):
    st.markdown(
        """
At minimum, your system should:
- Represent pet care tasks (what needs to happen, how long it takes, priority)
- Represent the pet and the owner (basic info and preferences)
- Build a plan/schedule for a day that chooses and orders tasks based on constraints
- Explain the plan (why each task was chosen and when it happens)
"""
    )

st.divider()

st.subheader("Quick Demo Inputs (UI only)")
owner_name = st.text_input("Owner name", value="Jordan")
pet_name = st.text_input("Pet name", value="Mochi")
species = st.selectbox("Species", ["dog", "cat", "other"])

# Check the session_state "vault" before creating the Owner/Pet so they
# aren't rebuilt (and emptied) on every rerun.
if "owner" not in st.session_state:
    st.session_state.owner = Owner(name=owner_name, availability={"09:00": "17:00"}, preferences=[])
owner = st.session_state.owner

if "pet" not in st.session_state:
    pet = Pet(name=pet_name, age=0, species=species, breed="")
    owner.add_pet(pet)
    st.session_state.pet = pet
pet = st.session_state.pet

st.markdown("### Tasks")
st.caption("Add a few tasks. In your final version, these should feed into your scheduler.")

col1, col2, col3 = st.columns(3)
with col1:
    task_title = st.text_input("Task title", value="Morning walk")
with col2:
    duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
with col3:
    priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)
task_type_name = st.selectbox("Task type", [t.name for t in TaskType])

if st.button("Add task"):
    task = Task(
        name=task_title,
        priority=Priority[priority.upper()],
        frequency="daily",
        deadline=datetime.combine(date.today(), time_cls(17, 0)),
        duration_minutes=int(duration),
        task_type=TaskType[task_type_name],
        pet=pet,
    )
    pet.add_task(task)

if pet.get_tasks():
    st.write("Current tasks:")
    st.table(
        [
            {"title": t.name, "duration_minutes": t.duration_minutes, "priority": t.priority.value}
            for t in pet.get_tasks()
        ]
    )
else:
    st.info("No tasks yet. Add one above.")

st.divider()

st.subheader("Build Schedule")
st.caption("This button should call your scheduling logic once you implement it.")

if st.button("Generate schedule"):
    scheduler = Scheduler(owner, [pet])
    plan = scheduler.create_schedule()
    st.text(plan.get_summary())
    with st.expander("Why this schedule?"):
        st.text(plan.get_explanation())
