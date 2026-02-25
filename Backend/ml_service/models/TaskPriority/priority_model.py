import os
import csv
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader, random_split
from sklearn.preprocessing import LabelEncoder, OneHotEncoder, StandardScaler
import numpy as np
import pickle


class DualTPMD(Dataset):
    def __init__(self, path1, path2):
        self.data_list = []

        task_types = []
        hours_data = []

        with open(path1, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                row["hours_left"] = float(row["hours_left"])
                task_types.append(row["task_type"])
                hours_data.append([row["hours_left"]])
                self.data_list.append({"task_type": row["task_type"],
                                       "hours_left": row["hours_left"],
                                       "priority": row["priority"]})

        self.task_type_encoder = OneHotEncoder(sparse_output=False)
        self.task_type_encoder.fit(np.array(task_types).reshape(-1, 1))
        self.hours_scaler = StandardScaler().fit(hours_data)

        urgency_data = []
        priorities2 = []

        with open(path2, "r", encoding="utf-8") as f2:
            reader = csv.DictReader(f2)
            for idx, row in enumerate(reader):
                urgency = float(row["urgency"])
                urgency_data.append([urgency])
                priorities2.append(row["priority"])
                if idx < len(self.data_list):
                    self.data_list[idx]["urgency"] = urgency
                else:
                    self.data_list.append({"urgency": urgency, "priority": row["priority"]})

        self.urgency_scaler = StandardScaler().fit(urgency_data)

        self.priority_encoder = LabelEncoder()
        self.priority_encoder.fit([d["priority"] for d in self.data_list])

        self.input1_dim = len(self.task_type_encoder.categories_[0]) + 1
        self.input2_dim = 1
        self.output_dim = len(self.priority_encoder.classes_)

    def __len__(self):
        return len(self.data_list)

    def __getitem__(self, index):
        sample = self.data_list[index]

        task_type_encoded = self.task_type_encoder.transform([[sample["task_type"]]])[0]
        hours_scaled = self.hours_scaler.transform([[sample["hours_left"]]])[0]
        x1 = torch.tensor(list(task_type_encoded) + list(hours_scaled), dtype=torch.float32)

        urgency_scaled = self.urgency_scaler.transform([[sample["urgency"]]])[0]
        x2 = torch.tensor(urgency_scaled, dtype=torch.float32)

        y = torch.tensor(self.priority_encoder.transform([sample["priority"]])[0], dtype=torch.long)

        return x1, x2, y

# ---------------------------
# Multi-head Model
# ---------------------------
class DualHeadPriority(nn.Module):
    def __init__(self, input1_dim, input2_dim, hidden_dim, output_dim):
        super().__init__()
        self.head1 = nn.Sequential(
            nn.Linear(input1_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.3)
        )
        self.head2 = nn.Sequential(
            nn.Linear(input2_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.3)
        )
        self.fusion = nn.Sequential(
            nn.Linear(hidden_dim*2, hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(hidden_dim, output_dim)
        )

    def forward(self, x1, x2):
        h1 = self.head1(x1)
        h2 = self.head2(x2)
        combined = torch.cat([h1, h2], dim=1)
        out = self.fusion(combined)
        return out

# ---------------------------
# Training
# ---------------------------
def train_model(model, train_loader, test_loader, epochs=25, lr=0.0001):
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=lr)

    for epoch in range(epochs):
        model.train()
        total_loss = 0
        for x1_batch, x2_batch, y_batch in train_loader:
            optimizer.zero_grad()
            outputs = model(x1_batch, x2_batch)
            loss = criterion(outputs, y_batch)
            loss.backward()
            optimizer.step()
            total_loss += loss.item()

        model.eval()
        correct, total = 0, 0
        with torch.no_grad():
            for x1_batch, x2_batch, y_batch in test_loader:
                outputs = model(x1_batch, x2_batch)
                _, predicted = torch.max(outputs, 1)
                correct += (predicted == y_batch).sum().item()
                total += y_batch.size(0)
        acc = correct / total

        print(f"Epoch {epoch+1}/{epochs} | Loss: {total_loss:.4f} | Test Acc: {acc:.4f}")

# ---------------------------
# Main
# ---------------------------
if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    dataset = DualTPMD(
        path1=os.path.join(script_dir, "tpmhd.csv"),
        path2=os.path.join(script_dir, "tpmud.csv")
    )

    train_size = int(0.8 * len(dataset))
    test_size = len(dataset) - train_size
    train_dataset, test_dataset = random_split(dataset, [train_size, test_size])

    train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True)
    test_loader = DataLoader(test_dataset, batch_size=32)

    hidden_dim = 32
    model = DualHeadPriority(dataset.input1_dim, dataset.input2_dim, hidden_dim, dataset.output_dim)

    train_model(model, train_loader, test_loader, epochs=50, lr=0.0001)
    torch.save(model.state_dict(), "dualhead_tpm.pt")
    print("Модель сохранена в dualhead_tpm.pt")
    model.eval()

    dummy_input1 = torch.randn(1, dataset.input1_dim)
    dummy_input2 = torch.randn(1, dataset.input2_dim)

    torch.onnx.export(
        model,
        (dummy_input1, dummy_input2),
        "dualhead_tpm.onnx",
        input_names=["input1", "input2"],
        output_names=["output"],
        dynamic_axes={
            "input1": {0: "batch_size"},
            "input2": {0: "batch_size"},
            "output": {0: "batch_size"}
        },
        opset_version=17
    )
    print("Модель сохранена в dualhead_tpm.onnx")


    
    with open("dualhead_tpm_encoders.pkl", "wb") as f:
        pickle.dump({
            "task_type_encoder": dataset.task_type_encoder,
            "hours_scaler": dataset.hours_scaler,
            "urgency_scaler": dataset.urgency_scaler,
            "priority_encoder": dataset.priority_encoder
        }, f)
