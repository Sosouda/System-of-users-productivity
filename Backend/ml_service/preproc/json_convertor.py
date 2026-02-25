import pickle
import json

with open("dualhead_tpm_encoders.pkl", "rb") as f:
    encoders = pickle.load(f)

task_type_encoder = encoders["task_type_encoder"]
priority_encoder = encoders["priority_encoder"]

out = {}

if hasattr(task_type_encoder, "classes_"):
    out["task_type_mapping"] = {
        label: int(idx)
        for idx, label in enumerate(task_type_encoder.classes_)
    }
else:
    out["task_type_mapping"] = {
        name: int(i)
        for i, name in enumerate(task_type_encoder.get_feature_names_out())
    }

out["priority_labels"] = priority_encoder.classes_.tolist()

with open("dualhead_tpm_encoders.json", "w", encoding="utf-8") as f:
    json.dump(out, f, indent=2, ensure_ascii=False)

print("dualhead_tpm_encoders.json успешно создан")

with open("tlm_scalers.pkl", "rb") as f:
    scalers = pickle.load(f)

def export_scaler(scaler):
    if hasattr(scaler, "mean_"):
        return {
            "type": "standard",
            "mean": scaler.mean_.tolist(),
            "scale": scaler.scale_.tolist()
        }
    elif hasattr(scaler, "min_"):
        return {
            "type": "minmax",
            "min": scaler.min_.tolist(),
            "scale": scaler.scale_.tolist()
        }
    else:
        raise ValueError("Unknown scaler type")

out = {
    "active_tasks": export_scaler(scalers["active_tasks_scaler"]),
    "avg_priority": export_scaler(scalers["avg_priority_scaler"]),
    "max_priority": export_scaler(scalers["max_priority_scaler"]),
    "avg_hours_to_deadline": export_scaler(scalers["avg_hours_to_deadline_scaler"]),
    "overdue_tasks": export_scaler(scalers["overdue_tasks_scaler"])
}

with open("tlm_scalers.json", "w", encoding="utf-8") as f:
    json.dump(out, f, indent=2)

print("tlm_scalers.json успешно создан")