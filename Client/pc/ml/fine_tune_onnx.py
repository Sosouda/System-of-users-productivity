"""
Дообучение ONNX моделей через конвертацию в PyTorch.
Поддерживает TaskLoad и TaskPriority модели.
"""

import os
import sys
import numpy as np
from datetime import datetime
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from local_db.data_manager import get_unsynced_ml_feedback_taskload


def extract_onnx_weights(model_path):
    """Извлечь веса из ONNX"""
    try:
        import onnx
        from onnx import numpy_helper
        
        model = onnx.load(model_path)
        weights = {}
        for initializer in model.graph.initializer:
            weights[initializer.name] = numpy_helper.to_array(initializer)
        return weights
    except Exception as e:
        print(f"⚠️ Не удалось извлечь веса: {e}")
        return {}


def create_torch_model_from_onnx(onnx_weights, model_type="taskload"):
    """Создать PyTorch модель с весами из ONNX"""
    import torch
    import torch.nn as nn
    
    if model_type == "taskload":
        class TaskLoadModel(nn.Module):
            def __init__(self):
                super().__init__()
                self.net = nn.Sequential(
                    nn.Linear(5, 32),
                    nn.ReLU(),
                    nn.Dropout(0.3),
                    nn.Linear(32, 32),
                    nn.ReLU(),
                    nn.Dropout(0.3),
                    nn.Linear(32, 1)
                )
            
            def forward(self, x):
                return self.net(x).squeeze(-1)
        
        model = TaskLoadModel()
        
        with torch.no_grad():
            model.net[0].weight.copy_(torch.from_numpy(onnx_weights['net.0.weight'].copy()))
            model.net[0].bias.copy_(torch.from_numpy(onnx_weights['net.0.bias'].copy()))
            model.net[3].weight.copy_(torch.from_numpy(onnx_weights['net.3.weight'].copy()))
            model.net[3].bias.copy_(torch.from_numpy(onnx_weights['net.3.bias'].copy()))
            model.net[6].weight.copy_(torch.from_numpy(onnx_weights['net.6.weight'].copy()))
            model.net[6].bias.copy_(torch.from_numpy(onnx_weights['net.6.bias'].copy()))
        
        return model
    
    elif model_type == "taskpriority":
        class DualHeadPriority(nn.Module):
            def __init__(self, input1_dim=12, input2_dim=1, hidden_dim=32, output_dim=5):
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
        
        model = DualHeadPriority()
        
        with torch.no_grad():
            model.head1[0].weight.copy_(torch.from_numpy(onnx_weights['head1.0.weight'].copy()))
            model.head1[0].bias.copy_(torch.from_numpy(onnx_weights['head1.0.bias'].copy()))
            model.head2[0].weight.copy_(torch.from_numpy(onnx_weights['head2.0.weight'].copy()))
            model.head2[0].bias.copy_(torch.from_numpy(onnx_weights['head2.0.bias'].copy()))
            model.fusion[0].weight.copy_(torch.from_numpy(onnx_weights['fusion.0.weight'].copy()))
            model.fusion[0].bias.copy_(torch.from_numpy(onnx_weights['fusion.0.bias'].copy()))
            model.fusion[3].weight.copy_(torch.from_numpy(onnx_weights['fusion.3.weight'].copy()))
            model.fusion[3].bias.copy_(torch.from_numpy(onnx_weights['fusion.3.bias'].copy()))
        
        return model
    
    return None


def fine_tune_torch_model(model, feedback_records, model_type="taskload", epochs=10, lr=0.001):
    """Дообучение PyTorch модели"""
    import torch
    import torch.nn as nn
    import torch.optim as optim
    from torch.utils.data import Dataset, DataLoader
    from sklearn.preprocessing import StandardScaler
    
    class FeedbackDataset(Dataset):
        def __init__(self, records, model_type):
            self.data = []
            self.data2 = []  # Для второго входа (TaskPriority)
            self.targets = []
            self.model_type = model_type
            
            for record in records:
                if model_type == "taskload":
                    if hasattr(record, 'predicted_workload') and record.predicted_workload and record.actual_workload:
                        x = np.array([
                            record.active_tasks,
                            record.avg_priority if record.avg_priority else 0,
                            record.max_priority if record.max_priority else 0,
                            record.avg_hours_to_deadline if record.avg_hours_to_deadline else 0,
                            record.overdue_tasks
                        ], dtype=np.float32)
                        y = float(record.actual_workload)
                        self.data.append(x)
                        self.targets.append(y)
                
                elif model_type == "taskpriority":
                    if hasattr(record, 'hours_left') and hasattr(record, 'user_priority'):
                        # TaskPriority модель ожидает:
                        # x1: task_type one-hot (11 признаков) + hours_left (1 признак) = 12
                        # x2: urgency (1 признак)
                        
                        # Для простоты используем только hours_left + dummy task_type
                        task_type_dummy = np.zeros(11, dtype=np.float32)  # One-hot для 11 типов
                        x1 = np.concatenate([task_type_dummy, [record.hours_left if record.hours_left else 0]])
                        
                        # Второй вход: urgency
                        x2 = np.array([
                            record.urgency if record.urgency else 0
                        ], dtype=np.float32)
                        
                        # Кодируем приоритет как число
                        priority_map = {'Casual': 0, 'Low': 1, 'Mid': 2, 'High': 3, 'Extreme': 4}
                        y = priority_map.get(record.user_priority, 2)
                        
                        self.data.append(x1)
                        self.data2.append(x2)
                        self.targets.append(y)
            
            self.data = np.array(self.data)
            self.data2 = np.array(self.data2) if self.data2 else np.array([])
            self.targets = np.array(self.targets)
            
            # Нормализация для TaskLoad
            if len(self.data) > 0 and model_type == "taskload":
                self.scaler = StandardScaler()
                self.data = self.scaler.fit_transform(self.data)
        
        def __len__(self):
            return len(self.data)
        
        def __getitem__(self, idx):
            if self.model_type == "taskpriority":
                x1 = torch.tensor(self.data[idx], dtype=torch.float32)
                x2 = torch.tensor(self.data2[idx], dtype=torch.float32)
                y = torch.tensor(self.targets[idx], dtype=torch.long)
                return x1, x2, y
            else:
                x = torch.tensor(self.data[idx], dtype=torch.float32)
                y = torch.tensor(self.targets[idx], dtype=torch.float32)
                return x, y
    
    dataset = FeedbackDataset(feedback_records, model_type)
    
    if len(dataset) < 3:
        print(f"⚠️ Недостаточно данных для дообучения (минимум 3, есть {len(dataset)})")
        return model, []
    
    dataloader = DataLoader(dataset, batch_size=4, shuffle=True)
    
    if model_type == "taskload":
        criterion = nn.MSELoss()
    else:
        criterion = nn.CrossEntropyLoss()
    
    optimizer = optim.Adam(model.parameters(), lr=lr)
    
    loss_history = []
    model.train()
    
    for epoch in range(epochs):
        total_loss = 0
        for batch in dataloader:
            optimizer.zero_grad()
            
            if model_type == "taskload":
                x_batch, y_batch = batch
                outputs = model(x_batch)
                loss = criterion(outputs, y_batch)
            else:
                x1_batch, x2_batch, y_batch = batch
                outputs = model(x1_batch, x2_batch)
                loss = criterion(outputs, y_batch)
            
            loss.backward()
            optimizer.step()
            total_loss += loss.item()
        
        avg_loss = total_loss / len(dataloader)
        loss_history.append(avg_loss)
        print(f"   Эпоха {epoch+1}/{epochs} | Loss: {avg_loss:.2f}")
    
    return model, loss_history


def get_torch_weights(model, model_type="taskload"):
    """Извлечь веса из PyTorch модели"""
    if model_type == "taskload":
        return {
            'net.0.weight': model.net[0].weight.detach().numpy(),
            'net.0.bias': model.net[0].bias.detach().numpy(),
            'net.3.weight': model.net[3].weight.detach().numpy(),
            'net.3.bias': model.net[3].bias.detach().numpy(),
            'net.6.weight': model.net[6].weight.detach().numpy(),
            'net.6.bias': model.net[6].bias.detach().numpy()
        }
    elif model_type == "taskpriority":
        return {
            'head1.0.weight': model.head1[0].weight.detach().numpy(),
            'head1.0.bias': model.head1[0].bias.detach().numpy(),
            'head2.0.weight': model.head2[0].weight.detach().numpy(),
            'head2.0.bias': model.head2[0].bias.detach().numpy(),
            'fusion.0.weight': model.fusion[0].weight.detach().numpy(),
            'fusion.0.bias': model.fusion[0].bias.detach().numpy(),
            'fusion.3.weight': model.fusion[3].weight.detach().numpy(),
            'fusion.3.bias': model.fusion[3].bias.detach().numpy()
        }
    return {}


def save_onnx_with_weights(base_model_path, new_weights, output_path):
    """Сохранить ONNX с новыми весами"""
    try:
        import onnx
        from onnx import numpy_helper
        
        model = onnx.load(base_model_path)
        
        for initializer in model.graph.initializer:
            if initializer.name in new_weights:
                new_tensor = numpy_helper.from_array(new_weights[initializer.name], name=initializer.name)
                initializer.CopyFrom(new_tensor)
        
        onnx.save(model, output_path)
        print(f"✅ Модель сохранена: {output_path}")
        return True
    except Exception as e:
        print(f"❌ Ошибка сохранения: {e}")
        return False


if __name__ == "__main__":
    print("\n" + "="*80)
    print("🚀 ТЕСТОВОЕ ДООбучЕНИЕ")
    print("="*80 + "\n")
    
    records = get_unsynced_ml_feedback_taskload()
    print(f"📦 Записей: {len(records)}")
    
    if len(records) < 3:
        print("⚠️ Недостаточно записей")
    else:
        print("✅ Готово к дообучению!")
