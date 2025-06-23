def testResult_test():
    from ultralytics import YOLO
    import matplotlib.pyplot as plt
    import cv2
    import requests
    import numpy as np

    onnx_model = YOLO("runs/detect/yolo_test_train3/weights/best.pt")
    image_path = "main_test.png"
    image = cv2.imread(image_path)
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    input_size = (640, 640)
    resized_image = cv2.resize(image, input_size)

    results = onnx_model(image, imgsz=640)

    for result in results:
        boxes = result.boxes
        print("boxes :", len(boxes))
        names = result.names
        for box in boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            conf = box.conf[0]
            cls = int(box.cls[0])
            label = f"{names[cls]} {conf:.2f}"
            print("label :", label)

            cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 0), 2)
            (text_width, text_height), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
            cv2.rectangle(image, (x1, y1 - text_height - 5), (x1 + text_width, y1), (0, 255, 0), -1)
            cv2.putText(image, label, (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)

        plt.figure(figsize=(10, 10))
    plt.imshow(image)
    plt.axis("off")
    plt.show()

if __name__ == '__main__':
    testResult_test()