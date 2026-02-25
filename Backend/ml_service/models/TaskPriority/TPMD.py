import csv
import random
import numpy as np
from  datetime import timedelta, datetime

random.seed(42)
np.random.seed(42)

task_base_importance = [
    ("Dust Cleaning", 1.3),
    ("Meeting", 1.3),
    ("Documentation", 1.2),
    ("Customer Support", 1.2),
    ("Code Bug Fix", 1.1),
    ("Research", 1.1),
    ("Feature Development", 1.0),
    ("Optimization", 1.0),
    ("Other", 1.0),
    ("Deployment", 0.9),
    ("Project Management", 0.9)

]

classes_by_hours = [
    (0, 16, "Extreme"),
    (16, 32, "High"),
    (32, 80, "Mid"),
    (80, 120, "Low"),
    (120, 10000, "Casual")
]

classes_by_urgency = [
    (16, 20, "Extreme"),
    (12, 16, "High"),
    (8, 12, "Mid"),
    (4, 8, "Low"),
    (0, 4, "Casual")
]



def calculate_working_hours(deadline_str):
    WORK_START = 10
    WORK_END = 18

    now = datetime.now()
    deadline = datetime.strptime(deadline_str, "%d.%m.%Y %H:%M:%S")

    if deadline <= now:
        return 0

    total_working_hours = 0
    current_time = now

    while current_time.date() < deadline.date() or (
        current_time.date() == deadline.date() and current_time.hour < deadline.hour
    ):
        if current_time.weekday() >= 5:
            current_time += timedelta(days=1)
            current_time = current_time.replace(hour=WORK_START, minute=0, second=0, microsecond=0)
            continue

        if current_time.hour < WORK_START:
            current_time = current_time.replace(hour=WORK_START, minute=0, second=0, microsecond=0)

        if current_time.hour >= WORK_END:
            current_time += timedelta(days=1)
            current_time = current_time.replace(hour=WORK_START, minute=0, second=0, microsecond=0)
            continue

        end_of_day = current_time.replace(hour=WORK_END, minute=0, second=0, microsecond=0)
        hours_to_end_of_day = max(0, (end_of_day - current_time).total_seconds() / 3600)

        if current_time.date() == deadline.date():
            hours_to_deadline = max(0, (deadline - current_time).total_seconds() / 3600)
            total_working_hours += min(hours_to_deadline, hours_to_end_of_day)
            break

        total_working_hours += hours_to_end_of_day

        current_time += timedelta(days=1)
        current_time = current_time.replace(hour=WORK_START, minute=0, second=0, microsecond=0)

    return round(total_working_hours, 2)

def get_priority_hours(ideal_hours):
    for low, high, priority in classes_by_hours:
        if low < ideal_hours <= high:
            return priority

def get_priority_urgency(urgency):
    for low, high, priority in classes_by_urgency:
        if low < urgency <= high:
            return priority



data = []

n_samples = 12000
i = 0
while i < n_samples:
    task_type, coefficient = random.choice(task_base_importance)
    days_to_deadline = random.randint(1, 60)
    deadline = datetime.now() + timedelta(days=days_to_deadline)
    deadline_str = deadline.strftime("%d.%m.%Y %H:%M:%S")

    remaining_hours = calculate_working_hours(deadline_str)
    ideal_hours = remaining_hours * coefficient

    final_priority = get_priority_hours(ideal_hours)


    data.append([task_type, remaining_hours, final_priority])
    i+=1

header1 = ["task_type", "hours_left", "priority"] 
with open("tpmhd.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(header1)
    writer.writerows(data)

print("✅ tpmhd.csv создан! Всего строк:", len(data))

rows=[]
i = 0
while i < n_samples:
    influence = random.randint(1, 10)
    self_importance = random.randint(1, 10)
    urgency = influence + self_importance
    final_priority = get_priority_urgency(urgency)

    rows.append([urgency, final_priority])
    i+=1

header2 = ["urgency", "priority"]
with open("tpmud.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(header2)
    writer.writerows(rows)

print("✅ tpmud.csv создан! Всего строк:", len(rows))

