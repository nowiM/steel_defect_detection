import albumentations as A
import cv2
import os
import random
import shutil
from tqdm import tqdm

# 데이터 셋 경로
train_image_dir = '../datasets_pre/train/images'
train_label_dir = '../datasets_pre/train/labels'

# 데이터 셋 증강 경로
aug_image_dir = '../datasets_aug/train/images'
aug_label_dir = '../datasets_aug/train/labels'

# 지장한 경로 디렉토리 만들기
os.makedirs(aug_image_dir, exist_ok = True)
os.makedirs(aug_label_dir, exist_ok = True)

class_names = ['crazing', 'inclusion', 'patches',
               'pitted_surface', 'rolled_in_scale', 'scratches'
            ]
# 각 클래스당 증강 수
TARGET_COUNT = 2000

# 라벨 읽기
def read_yolo_label(labe_path):
    with open(label_path, 'r') as f:
        return [line.strip() for line in f.readlines()]


# 라벨 저장
def write_yolo_label(label_path, lines):
    with open(label_path, 'w') as f:
        for line in lines:
            f.write(f'{line}\n')



# 0 ~ 1 범위 clip
def clip_bbox(bbox):
    return [min(max(x, 0.0), 1.0) for x in bbox]


# 증강 파이프라인
transform = A.Compose([
    A.RandomBrightnessContrast(p = 0.5), # 밝기와 대비 무작위 조절 | p = 0.5 50% 확률로 적용
    A.GaussianBlur(p = 0.3), # 가우시안 블러(흐림 효과)
    A.Rotate(limit = 15, p = 0.5), # 시계/반시계 방향으로 회전 | limit=15: -15도 ~ +15도 범위 내에서 랜덤 회전
    A.HorizontalFlip(p = 0.5), # 좌우 반전
    A.Affine(scale = (0.9, 1.1), translate_percent = 0.05, rotate = 0, p = 0.5), # 어파인 변환(확대, 축소, 이동 등) 적용
], bbox_params = A.BboxParams(format = 'yolo', label_fields=['class_labels']))
# bbox_params = A.BboxParams(format = 'yolo', label_fields=['class_labels'])
# 바운딩 박스 처리 format = 'yolo'
# 바운딩 박스 포맷이 yolo 형식
# label_fields=['class_labels']
# 클래스 정보가 들어 있는 필드 이름을 명시

# 클래스별 이미지 목록
class_to_images = {cls: [] for cls in class_names}

# 라벨 파일이 저장된 경로에 마지막 파일까지 반복한다.
for fname in os.listdir(train_label_dir):
    print(fname)
    # fname 저장되 라벨 파일 이름
    if fname.endswith('.txt'): # 확장자가 txt 파일인 경우
        label_path = os.path.join(train_label_dir, fname) # 라벨 파일 경로
        lines = read_yolo_label(label_path) # 바운딩 박스 좌표값 저장

        for line in lines:
            # line => ['0 0.635000 0.222500 0.670000 0.245000', '0 0.515000 0.705000 0.940000 0.570000']
            cls_id = int(line.split()[0]) # 클래스 id
            class_name = class_names[cls_id] # 클래스 이름 저장
            # print('클래스 id : ', cls_id)
            # print('클래스 이름 : ', class_name)
            class_to_images[class_name].append(fname) # 딕셔너리에 해당하는 파일명 저장
            break

# print(class_to_images)

# 증강 시작
for cls in class_names:
    cls_id = class_names
    images = class_to_images[cls]
    existing = len(images) # 해당하는 클래스의 이미지 개수

    print(f'[{cls}] {existing}개 -> {TARGET_COUNT}개로 증강 중...')

    count = 0

    for fname in images:
        img_name = fname.replace('.txt', '.jpg') # jpg 확장자로 변경
        src_img_path = os.path.join(train_image_dir, img_name)
        src_lbl_path = os.path.join(train_label_dir, fname)

        dst_img_path = os.path.join(aug_image_dir, img_name)
        dst_lbl_path = os.path.join(aug_label_dir, fname)

        if not os.path.exists(dst_img_path):
            shutil.copyfile(src_img_path, dst_img_path)
            shutil.copyfile(src_lbl_path, dst_lbl_path)
            count += 1


    augment_idx = 0

    while count < TARGET_COUNT:
        src_label_name = random.choice(images)
        src_img_name = src_label_name.replace('.txt', '.jpg')

        img_path = os.path.join(train_image_dir, src_img_name)
        label_path = os.path.join(train_label_dir, src_label_name)

        if not os.path.exists(img_path) or not os.path.exists(label_path):
            continue

        image = cv2.imread(img_path)

        if image is None:
            continue

        lines = read_yolo_label(label_path)
        bboxes = []
        class_labels = []

        for line in lines:
            parts = line.strip().split()

            if len(parts) != 5:
                continue

            class_id = int(parts[0])
            bbox = list(map(float, parts[1:]))
            bboxes.append(bbox)
            class_labels.append(class_id)


        try:
            transformed = transform(
                image = image,
                bboxes = bboxes,
                class_labels = class_labels
            )

            if len(transformed['bboxes']) == 0:
                continue


            aug_image = transformed['image']
            aug_bboxes = [clip_bbox(b) for b in transformed['bboxes']]
            aug_labels = transformed['class_labels']

            new_img_name = f'{cls}_{augment_idx}_aug.jpg'
            new_lbl_name = f'{cls}_{augment_idx}_aug.txt'

            cv2.imwrite(os.path.join(aug_image_dir, new_img_name), aug_image)

            new_lines = []

            for lab, box in zip(aug_labels, aug_bboxes):
                new_lines.append(f"{lab} {' '.join(map(str, box))}")

                write_yolo_label(os.path.join(aug_label_dir, new_lbl_name), new_lines)

                count += 1
                augment_idx += 1
        except Exception as e:
            continue

    print(f'[{cls}] 총 {count}장 저장 완료 (증강 {count - existing}장 포함')

print('모든 클래스 증강 완료')





