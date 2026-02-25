import onnx
import os
from onnx.external_data_helper import convert_model_to_external_data

INPUT_MODEL_PATH = "tlm.onnx"
OUTPUT_MODEL_PATH = "tlm_embedded.onnx"

print(f"Загрузка модели с внешними данными: {INPUT_MODEL_PATH}")
model = onnx.load(INPUT_MODEL_PATH)

print(f"Сохранение модели с встраиванием данных в: {OUTPUT_MODEL_PATH}")
onnx.save(
    model,
    OUTPUT_MODEL_PATH,
    save_as_external_data=False
)
print("-" * 30)
model = onnx.load("tlm.onnx")

onnx.save(model, "tlm_packed.onnx")
print("-" * 2)
print("-" * 30)
print("Готово! Теперь используйте файл:", OUTPUT_MODEL_PATH)