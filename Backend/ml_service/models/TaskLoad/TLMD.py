import csv
import random
import numpy as np
import math
from datetime import timedelta, datetime

random.seed(42)
np.random.seed(42)

data = []
n_samples = 12000
i = 0

def calculate_workload(active_tasks, avg_priority, max_priority, overdue_tasks):
    if active_tasks > 285:
        return 100

    base_task_load = active_tasks * 0.4
    priority_score = 0.5 * avg_priority + 0.3 * max_priority

    base_load = base_task_load + priority_score * active_tasks * 0.6

    overload_penalty = overdue_tasks * 0.5

    workload = base_load + overload_penalty
    return max(1, min(100, round(workload)))

while i < n_samples:
    active_tasks = random.randint(1, 40)
    priorities = [random.randint(1, 10) for _ in range(active_tasks)]
    deadlines = [datetime.now() + timedelta(hours=random.randint(-48, 240)) for _ in range(active_tasks)]

    overdue_tasks = random.randint(1, 20)
    avg_hours_to_deadline = max(0, sum(
        (d - datetime.now()).total_seconds() / 3600 for d in deadlines) / active_tasks)

    avg_priority = round(sum(priorities) / active_tasks, 2)
    workload = calculate_workload(active_tasks, avg_priority, max(priorities), overdue_tasks)

    data.append([active_tasks,
                 avg_priority,
                 max(priorities),
                 round(avg_hours_to_deadline,2),
                 overdue_tasks,
                 workload])
    i+=1

header = ["active_tasks", "avg_priority", "max_priority", "avg_hours_to_deadline",
           "overdue_tasks", "workload"]
with open("tlmd.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(header)
    writer.writerows(data)

print("✅ tlmd.csv создан! Всего строк:", len(data))