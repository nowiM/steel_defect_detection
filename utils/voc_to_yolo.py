import xml.etree.ElementTree as ET
from tqdm import tqdm
from pathlib import Path
import os
import shutil

ROOT_FOLDER_PATH = '../datasets_original'
VOC_FOLDER_PATH = '../NEU-DET'
LABELS = ['crazing', 'inclusion', 'patches',
          'pitted_surface', 'rolled-in_scale', 'scratches'
]
COPY_IMG = True


def convet_box(size, box):
    dw, dh = 1. / size[0], 1. / size[1]
    x, y, w, h = (box[0] + box[1]) / 2.0 - 1, (box[2] + box[3]) / 2.0 - 1, box[1] - box[0], box[3] - box[2]

    return x * dw, y * dh, w * dh, h * dh

def convert_label(in_fp, out_fp):
    in_file = open(in_fp)
    out_file = open(out_fp, 'w')
    tree = ET.parse(in_file)
    root = tree.getroot()
    size = root.find('size')
    w = int(size.find('width').text)
    h = int(size.find('height').text)

    for obj in root.iter('object'):
        cls = obj.find('name').text

        if cls in LABELS and not int(obj.find('difficult').text) == 1:
            xmlbox = obj.find('bndbox')
            bb = convet_box((w, h), [float(xmlbox.find(x).text) for x in ('xmin', 'xmax', 'ymin', 'ymax')])
            cls_id = LABELS.index(cls)
            out_file.write(" ".join([str(a) for a in (cls_id, *bb)]) + '\n')


for image_set in ['train', 'validation']:
    imgs_path = Path(f'{ROOT_FOLDER_PATH}/images/{image_set}') # 이미지 경로
    lbs_path = Path(f'{ROOT_FOLDER_PATH}/labels/{image_set}') # 라벨 경로

    # print(imgs_path)
    # print(lbs_path)

    # 디렉토리 생성
    # exist_ok = True : 이미 폴더가 있어도 에러 없이 넘어감,
    # parents = True : 경로 중간에 부모 디렉토리가 없으면 자동으로 생성
    imgs_path.mkdir(exist_ok = True, parents = True)
    lbs_path.mkdir(exist_ok = True, parents = True)

    # 라벨링 파일이 저장된 디렉토리 경로
    annot_folder = os.path.join(VOC_FOLDER_PATH, image_set, 'annotations')
    xml_files = os.listdir(annot_folder) # 라벨링 파일들을 리스트에 저장
    print(xml_files)

    for xml_fn in tqdm(xml_files, desc = f'{image_set}'):
        if COPY_IMG:
            img_fn = xml_fn.replace('xml', 'jpg')
            str_digits = img_fn.split('.')[0] # 확장자를 제거한 값 ex) crazing_1
            label_folder = ''.join([i for i in str_digits if not i.isdigit()]) # 숫자를 제거하고 클래스명만 추출
            label_folder = label_folder.strip('_') # 양쪽 끝 _ 제거
            img_fn = os.path.join(VOC_FOLDER_PATH, image_set, 'images', label_folder, img_fn)

            # src : 복사할 원본 파일 경로, dst : 복사할 대상 폴더
            shutil.copy(src = img_fn, dst = str(imgs_path))


        xml_fp = Path(f'{annot_folder}/{xml_fn}')
        xml_out_fp = lbs_path / xml_fn
        txt_out_fp = xml_out_fp. with_suffix('.txt')

        convert_label(xml_fp, txt_out_fp)