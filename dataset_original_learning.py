import torch
from ultralytics import YOLO

import torch
from ultralytics import YOLO

def train_model():
    print(torch.cuda.is_available())
    print(torch.__version__)

    model = YOLO('yolo11n.pt')
    model.train(
        data='datasets/data.yaml',
        epochs=30,
        imgsz=640,
        batch=16,
        name='yolo_test_train',
        device='0'
    )

if __name__ == "__main__":
    import multiprocessing
    multiprocessing.freeze_support()
    train_model()
