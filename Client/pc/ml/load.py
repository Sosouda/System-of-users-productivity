import onnxruntime as rt
import pickle
import numpy as np
from datetime import datetime,timedelta, timezone
import sys
import os

def get_path(relative_path):
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS if hasattr(sys, '_MEIPASS') else os.path.dirname(sys.executable)
    else:
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    relative_path = relative_path.replace('/', os.sep)
    return os.path.normpath(os.path.join(base_path, relative_path))


def predict_capacity(active_tasks, avg_priority, max_priority, avg_hours_to_deadline, overdue_tasks):
    model_path = get_path("ml/TaskLoad/tlm.onnx")
    scaler_path = get_path("ml/TaskLoad/tlm_scalers.pkl")

    ort_session = rt.InferenceSession(model_path)

    with open(scaler_path, "rb") as f:
        scalers = pickle.load(f)

    active_tasks_scaler = scalers["active_tasks_scaler"]
    avg_priority_scaler = scalers["avg_priority_scaler"]
    max_priority_scaler = scalers["max_priority_scaler"]
    avg_hours_to_deadline_scaler = scalers["avg_hours_to_deadline_scaler"]
    overdue_tasks_scaler = scalers["overdue_tasks_scaler"]

    active_scaled = active_tasks_scaler.transform([[active_tasks]])[0]
    avg_priority_scaled = avg_priority_scaler.transform([[avg_priority]])[0]
    max_priority_scaled = max_priority_scaler.transform([[max_priority]])[0]
    hours_scaled = avg_hours_to_deadline_scaler.transform([[avg_hours_to_deadline]])[0]
    overdue_scaled = overdue_tasks_scaler.transform([[overdue_tasks]])[0]

    x = np.concatenate([active_scaled, avg_priority_scaled, max_priority_scaled, hours_scaled, overdue_scaled]).astype(np.float32).reshape(1, -1)

    outputs = ort_session.run(None, {"input": x})
    pred = outputs[0][0]

    return int(pred)

def predict_priority(task_type,deadline,urgency):
    model_path = get_path("ml/TaskPriority/dualhead_tpm.onnx")
    encoder_path = get_path("ml/TaskPriority/dualhead_tpm_encoders.pkl")

    ort_session = rt.InferenceSession(model_path)

    with open(encoder_path, "rb") as f:
        encoders = pickle.load(f)

    task_type_encoder = encoders["task_type_encoder"]
    hours_scaler = encoders["hours_scaler"]
    urgency_scaler = encoders["urgency_scaler"]
    priority_encoder = encoders["priority_encoder"]

    hours_left = calculate_working_hours(deadline)

    task_type_encoded = task_type_encoder.transform([[task_type]])[0]
    hours_scaled = hours_scaler.transform([[hours_left]])[0]
    x1 = np.concatenate([task_type_encoded, hours_scaled]).astype(np.float32).reshape(1, -1)

    x2 = urgency_scaler.transform([[urgency]])[0].astype(np.float32).reshape(1, -1)

    outputs = ort_session.run(None, {"input1": x1, "input2": x2})
    logits = outputs[0]
    pred_idx = np.argmax(logits, axis=1)[0]
    predicted_priority = priority_encoder.inverse_transform([pred_idx])[0]

    print(predicted_priority)
    return predicted_priority


def calculate_working_hours(deadline_str):
    WORK_START = 10
    WORK_END = 18
    now = datetime.now()
    deadline = datetime.strptime(deadline_str, "%Y-%m-%d")
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


