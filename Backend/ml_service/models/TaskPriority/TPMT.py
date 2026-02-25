import torch
import numpy as np
from datetime import datetime, timedelta
from priority_model import DualTPMD, DualHeadPriority
import random


random.seed(41)
np.random.seed(41)
torch.manual_seed(41)

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
    while current_time.date() < deadline.date() or (current_time.date() == deadline.date() and current_time.hour < deadline.hour):
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

script_dir = "."
dataset = DualTPMD(
    path1=f"{script_dir}/tpmhd.csv",
    path2=f"{script_dir}/tpmud.csv"
)

model = DualHeadPriority(
    input1_dim=dataset.input1_dim,
    input2_dim=dataset.input2_dim,
    hidden_dim=32,
    output_dim=dataset.output_dim
)

model.load_state_dict(torch.load(f"{script_dir}/dualhead_tpm.pt", map_location=torch.device("cpu")))
model.eval()

tests = []
for _ in range(10):
    task_type, coefficient = random.choice(task_base_importance)
    days_to_deadline = random.randint(1, 60)
    deadline = datetime.now() + timedelta(days=days_to_deadline)
    deadline_str = deadline.strftime("%d.%m.%Y %H:%M:%S")
    remaining_hours = calculate_working_hours(deadline_str)
    ideal_hours = remaining_hours * coefficient
    final_priority_algo = get_priority_hours(ideal_hours)

    influence = random.randint(1, 10)
    self_importance = random.randint(1, 10)
    urgency = influence + self_importance
    final_priority_urgency = get_priority_urgency(urgency)

    tests.append({
        "task_type": task_type,
        "hours_left": remaining_hours,
        "urgency": urgency,
        "priority_algo": final_priority_algo,
        "priority_urgency": final_priority_urgency
    })

for test in tests:
    task_type_encoded = dataset.task_type_encoder.transform([[test["task_type"]]])[0]
    hours_scaled = dataset.hours_scaler.transform([[test["hours_left"]]])[0]
    x1 = torch.tensor(list(task_type_encoded) + list(hours_scaled), dtype=torch.float32).unsqueeze(0)

    urgency_scaled = dataset.urgency_scaler.transform([[test["urgency"]]])[0]
    x2 = torch.tensor(urgency_scaled, dtype=torch.float32).unsqueeze(0)

    with torch.no_grad():
        output = model(x1, x2)
        pred_idx = torch.argmax(output, dim=1).item()
        pred_priority = dataset.priority_encoder.inverse_transform([pred_idx])[0]

    algo_priority = test["priority_algo"]
    match = "✅" if pred_priority == algo_priority else "❌"

    print(f"Task: {test['task_type']:<20} | Hours Left: {test['hours_left']:<5} | Urgency: {test['urgency']:<3} | "
          f"Priority Algo: {algo_priority:<8} | Priority Model: {pred_priority:<8} | Match: {match}")
