import xml.etree.ElementTree as ET
from xml.etree.ElementTree import Element, SubElement, ElementTree
from tqdm import tqdm
from pathlib import Path
import os
from operator import itemgetter

ROOT_FOLDER_PATH = '../NEU-DET'
LABELS = [
    'crazing', 'inclusion', 'patches',
    'pitted_surface', 'rolled-in_scale', 'scratches'
]
DILATED_WIDTH = 10
OVERLAP_FRACTION = 0.4
PASS_LABELS = ['patches', 'scratches']
DICT_FOLDER = {
    'crazing': 'cz',
    'inclusion': 'in',
    'patches': 'pa',
    'pitted_surface': 'ps',
    'rolled-in_scale': 'rs',
    'scratches': 'sc'
}


def read_xml(in_fp):
    # XML 파일 열기
    in_file = open(in_fp)

    # ElementTree 객체 파싱
    tree = ET.parse(in_file)
    # 최상위 루트 엘리먼트 root 변수에 저장
    root = tree.getroot()
    # 하위 엘리먼트에 size 엘리먼트 찾아 저장
    size = root.find('size')
    # size 엘리먼트 하위에 width 엘리먼트 text를 int로 변환
    w = int(size.find('width').text)
    h = int(size.find('height').text)

    dict_group = {}
    obj = root.find('object')

    # 하나의 파일에 여러개의 라벨링 파일을 dict_group 저장
    for obj in root.iter('object'):
        cls = obj.find('name').text
        if cls in LABELS:
            xmlbox = obj.find('bndbox')
            bb = [int(xmlbox.find(x).text) for x in ('xmin', 'xmax', 'ymin', 'ymax')]
            if cls in dict_group:
                dict_group[cls].append(bb)
            else:
                dict_group[cls] = [bb]

    return w, h, dict_group



def merge(box1, box2):
    pass


def area(box):
    pass


def compute_overlapped_area(boxa, boxb, dilated=False, width=0, height=0):
    pass


def union_boxes(list_boxes, dilated, width, height):
    # bbox 좌표 리스트를 xmin 기준으로 정렬
    list_sort_xmin = sorted(list_boxes, key = itemgetter(0)) # itemgetter : 0번째 요소 기준으로 정렬

    n_box = len(list_boxes) # bbox 좌표 리스트 길이

    for i in range(n_box - 1):
        if list_sort_xmin[i] is None:
            continue

        box = list_sort_xmin[i][:] # 참조
        # print(list_sort_xmin[i]) # 복사

        list_index_review = []

        for j in range(n_box):
            if list_sort_xmin[j] is None or j == i:
                continue

            overlappend_area = compute_overlapped_area(
                                    box,
                                    list_sort_xmin[j],
                                    dilated,
                                    width,
                                    height
                                )

            min_area = min(area(box), area(list_sort_xmin[j]))
            thresh = 1 if dilated else (OVERLAP_FRACTION * min_area)

            if overlappend_area > thresh:
                box  = merge(box, list_sort_xmin[j])

                list_sort_xmin[j] = None

                for k in list_index_review[::-1]:
                    if list_sort_xmin[k] is None:
                        continue

                    overlappend_area = compute_overlapped_area(
                                    box,
                                    list_sort_xmin[k],
                                    dilated,
                                    width,
                                    height
                                )

                    min_area = min(area(box), area(list_sort_xmin[k]))
                    thresh = 1 if dilated else (OVERLAP_FRACTION * min_area)

                    if overlappend_area > thresh:
                        box = merge(box, list_sort_xmin[k])

                        list_sort_xmin[k] = None
            else:
                list_index_review.append(j)

        list_sort_xmin[i] = [box for box in list_sort_xmin if box is not None]

        return list_boxes


def write_xml(output_path, filename,
              width, height, list_bbox):
    pass


def clean(xml_files, annot_folder, output_folder, image_set):
    # tqdm는 반복 작업의 진행 상태를 한눈에 볼 수 있게 하는 progress bar 라이브러리, 에포크 실행 시 나오는 바와 같다.
    for xml_fn in tqdm(xml_files, desc = f'{image_set}'):
        in_fp = Path(f'{annot_folder}/{xml_fn}')
        w, h, dict_group = read_xml(in_fp)

        for class_name in dict_group:
            if class_name in PASS_LABELS or len(dict_group[class_name]) < 2:
                continue

            if class_name in ['crazing', 'pitted_surface']:
                dilated = True
            else:
                dilated = False

            list_boxes = union_boxes(dict_group[class_name], dilated, w, h)
            dict_group[class_name] = list_boxes

        list_bbox = []

        for class_name in dict_group:
            for box in dict_group[class_name]:
                list_bbox.append([class_name])
                list_bbox[-1].extend(box)

        write_xml(
            output_folder,
            xml_fn.split('.')[0],
            w,
            h,
            list_bbox
        )


def main():
    for image_set in ['train', 'validation']:
        # 여러 개의 디렉토리 경로 조각을 연결해주는 함수, OS 독립적 => ../NEU-DET/'train'/'annotations'
        annot_folder = os.path.join(ROOT_FOLDER_PATH, image_set, 'annotations')
        print(annot_folder)
        # 지정한 경로 안에 모든 파일 및 하위 디렉토리 이름 리스트로 반환
        xml_files = os.listdir(annot_folder)
        print(f'{image_set} 폴더 xml 파일 개수 : ', len(xml_files))

        output_folder = os.path.join(ROOT_FOLDER_PATH, image_set, 'annotations_clean')
        lbs_path = Path(output_folder) # 문자열 => 경로 객체로 변환
        lbs_path.mkdir(exist_ok = True, parents = True) # 디렉토리 생성

        clean(xml_files, annot_folder, output_folder, image_set)


if __name__ == '__main__':
    main()

