import torch
from task_load_model import TLMD, TaskLoad
from datetime import datetime, timedelta
import random
import numpy as np

INPUT_DIM = 5
HIDDEN_DIM = 32
OUTPUT_DIM = 1

SCRIPT_DIR = "."

model = TaskLoad(input_dim=INPUT_DIM, hidden_dim=HIDDEN_DIM, output_dim=OUTPUT_DIM)
model.load_state_dict(torch.load(f"{SCRIPT_DIR}/tlm.pt", map_location="cpu"))
model.eval()

dataset = TLMD(path=f"{SCRIPT_DIR}/tlmd.csv")

def calculate_workload(active_tasks, avg_priority, max_priority, overdue_tasks):
    if active_tasks > 285:
        return 100

    base_task_load = active_tasks * 0.4
    priority_score = 0.5 * avg_priority + 0.3 * max_priority
    base_load = base_task_load + priority_score * active_tasks * 0.6
    overload_penalty = overdue_tasks * 0.05

    workload = base_load + overload_penalty
    return max(1, min(100, round(workload)))

def run_test(active_tasks, avg_priority, max_priority, avg_hours_to_deadline, overdue_tasks):

    active_scaled = dataset.active_tasks_scaler.transform([[active_tasks]])[0]
    avg_priority_scaled = dataset.avg_priority_scaler.transform([[avg_priority]])[0]
    max_priority_scaled = dataset.max_priority_scaler.transform([[max_priority]])[0]
    hours_scaled = dataset.avg_hours_to_deadline_scaler.transform([[avg_hours_to_deadline]])[0]
    overdue_scaled = dataset.overdue_tasks_scaler.transform([[overdue_tasks]])[0]

    x = torch.tensor(
        list(active_scaled) + list(avg_priority_scaled) + list(max_priority_scaled) +
        list(hours_scaled) + list(overdue_scaled),
        dtype=torch.float32
    ).unsqueeze(0)

    with torch.no_grad():
        pred = int(model(x).item())

    algo = calculate_workload(active_tasks, avg_priority, max_priority, overdue_tasks)
    match = "✅" if pred == algo else "❌"
    diff = algo - pred

    print(f"Active: {active_tasks}, Avg prio: {avg_priority}, Max prio: {max_priority}, "
          f"Hours: {avg_hours_to_deadline:.2f}, Overdue: {overdue_tasks} | "
          f"Algo: {algo}, Model: {pred} | Match: {match}, Diff: {diff}")

if __name__ == "__main__":

    random.seed(42)
    np.random.seed(42)
    for i in range(100):
        active = random.randint(1, 40)
        priorities = [random.randint(1, 10) for _ in range(active)]
        deadlines = [datetime.now() + timedelta(hours=random.randint(-48, 240)) for _ in range(active)]
        overdue = random.randint(1, 20)
        avg_hours = max(0, sum((d - datetime.now()).total_seconds() / 3600 for d in deadlines) / active)
        avg_prio = round(sum(priorities) / active, 2)
        max_prio = max(priorities)

        run_test(active, avg_prio, max_prio, avg_hours, overdue)

    run_test(4,3.25, 5, 81.98222222551703, 18)
