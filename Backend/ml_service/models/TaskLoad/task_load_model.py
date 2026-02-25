import os
import csv
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader, random_split
from sklearn.preprocessing import LabelEncoder, OneHotEncoder, StandardScaler
import numpy as np
import pickle

class TLMD(Dataset):
    def __init__(self, path):
        self.data_list = []
        active_tasks_data = []
        avg_priority_data = []
        max_priority_data = []
        avg_hours_to_deadline_data = []
        overdue_tasks_data = []
        with open(path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                row["active_tasks"] = float(row["active_tasks"])
                active_tasks_data.append([row["active_tasks"]])
                row["avg_priority"] = float(row["avg_priority"])
                avg_priority_data.append([row["avg_priority"]])
                row["max_priority"] = float(row["max_priority"])
                max_priority_data.append([row["max_priority"]])
                row["avg_hours_to_deadline"] = float(row["avg_hours_to_deadline"])
                avg_hours_to_deadline_data.append([row["avg_hours_to_deadline"]])
                row["overdue_tasks"] = float(row["overdue_tasks"])
                overdue_tasks_data.append([row["overdue_tasks"]])
                self.data_list.append({"active_tasks": row["active_tasks"],
                                       "avg_priority": row["avg_priority"],
                                       "max_priority": row["max_priority"],
                                       "avg_hours_to_deadline": row["avg_hours_to_deadline"],
                                       "overdue_tasks": row["overdue_tasks"],
                                       "workload": row["workload"]})

        self.active_tasks_scaler = StandardScaler().fit(active_tasks_data)
        self.avg_priority_scaler = StandardScaler().fit(avg_priority_data)
        self.max_priority_scaler = StandardScaler().fit(max_priority_data)
        self.avg_hours_to_deadline_scaler = StandardScaler().fit(avg_hours_to_deadline_data)
        self.overdue_tasks_scaler = StandardScaler().fit(overdue_tasks_data)

        self.workload = np.array([int(d["workload"]) for d in self.data_list])

        self.input_dim = 5
        self.output_dim = 1

    def __len__(self):
        return len(self.data_list)

    def __getitem__(self, index):
        sample = self.data_list[index]

        active_tasks_scaler = self.active_tasks_scaler.transform([[sample["active_tasks"]]])[0]
        avg_priority_scaler = self.avg_priority_scaler.transform([[sample["avg_priority"]]])[0]
        max_priority_scaler = self.max_priority_scaler.transform([[sample["max_priority"]]])[0]
        avg_hours_to_deadline_scaler = self.avg_hours_to_deadline_scaler.transform([[sample["avg_hours_to_deadline"]]])[0]
        overdue_tasks_scaled = self.overdue_tasks_scaler.transform([[sample["overdue_tasks"]]])[0]
        x = torch.tensor(list(active_tasks_scaler) + list(avg_priority_scaler)
                         + list(max_priority_scaler) + list(avg_hours_to_deadline_scaler)
                         + list(overdue_tasks_scaled), dtype=torch.float32)

        y = torch.tensor(float(sample["workload"]), dtype=torch.float32)

        return x, y

class TaskLoad(nn.Module):
    def __init__(self, input_dim, hidden_dim, output_dim):
        super().__init__()

        self.net = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(hidden_dim, output_dim)
        )

    def forward(self, x):
        return self.net(x).squeeze(-1)

def train_model(model, train_loader, test_loader, epochs=25, lr=0.0001):
    criterion = nn.MSELoss()
    optimizer = optim.Adam(model.parameters(), lr=lr)

    for epoch in range(epochs):
        model.train()
        total_loss = 0
        for x_batch, y_batch in train_loader:
            optimizer.zero_grad()
            outputs = model(x_batch)
            loss = criterion(outputs, y_batch)
            loss.backward()
            optimizer.step()
            total_loss += loss.item()

        model.eval()
        test_loss = 0
        with torch.no_grad():
            for x_batch, y_batch in test_loader:
                outputs = model(x_batch)
                loss = criterion(outputs, y_batch)
                test_loss += loss.item()

        print(f"Epoch {epoch+1}/{epochs} | Train Loss: {total_loss:.4f} | Test Loss: {test_loss:.4f}")

if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    dataset = TLMD(
        path=os.path.join(script_dir, "tlmd.csv"),
    )

    train_size = int(0.8 * len(dataset))
    test_size = len(dataset) - train_size
    train_dataset, test_dataset = random_split(dataset, [train_size, test_size])

    train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True)
    test_loader = DataLoader(test_dataset, batch_size=32)

    hidden_dim = 32
    model = TaskLoad(dataset.input_dim, hidden_dim, dataset.output_dim)

    train_model(model, train_loader, test_loader, epochs=100, lr=0.0001)
    torch.save(model.state_dict(), "tlm.pt")
    print("Модель сохранена в tlm.pt")
    model.eval()

    dummy_input = torch.randn(1, dataset.input_dim)

    torch.onnx.export(
        model,
        dummy_input,
        "tlm.onnx",
        input_names=["input"],
        output_names=["output"],
        dynamic_axes={
            "input": {0: "batch_size"},
            "output": {0: "batch_size"}
        },
        opset_version=17
    )

    print("Модель сохранена в tlm.onnx")
    with open("tlm_scalers.pkl", "wb") as f:
        pickle.dump({
            "active_tasks_scaler": dataset.active_tasks_scaler,
            "avg_priority_scaler": dataset.avg_priority_scaler,
            "max_priority_scaler": dataset.max_priority_scaler,
            "avg_hours_to_deadline_scaler": dataset.avg_hours_to_deadline_scaler,
            "overdue_tasks_scaler": dataset.overdue_tasks_scaler
        }, f)