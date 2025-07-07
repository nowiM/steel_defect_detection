import torch
from ultralytics import YOLO

import torch
from ultralytics import YOLO

def learning_model():
    print(torch.cuda.is_available())
    print(torch.__version__)

    model = YOLO('yolov8n.pt')
    model.train(
        data='datasets_original/data.yaml',
        epochs=50,
        imgsz=640,
        batch=16,
        name='yolo_dataset_original',
        device='0'
    )

if __name__ == "__main__":
    import multiprocessing
    multiprocessing.freeze_support()
    learning_model()
