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
    x1  = min(box1[0], box2[0])
    x2  = max(box1[1], box2[1])
    y1  = min(box1[2], box2[2])
    y2  = max(box1[3], box2[3])

    return [x1, x2, y1, y2]


def area(box):
    width = box[1] - box[0]
    height = box[3] - box[2]

    return width * height


def dilate_rectangle(box, width, height):
    xmin = max(0, box[0] - DILATED_WIDTH)
    xmax = min(width, box[1] + DILATED_WIDTH)
    ymin = max(0, box[2] - DILATED_WIDTH)
    ymax = min(height, box[3] + DILATED_WIDTH)

    return [xmin, xmax, ymin, ymax]

def compute_overlapped_area(boxa, boxb, dilated = False, width = 0, height = 0):
    list_sort_xmin = sorted([boxa, boxb], key = itemgetter(0))

    box1 = list_sort_xmin[0]
    box2 = list_sort_xmin[1]

    x1 = box2[0]
    x2 = box2[1]

    if x2 < x1:
        return 0

    if dilated:
        box1 = dilate_rectangle(box1, width, height)
        box2 = dilate_rectangle(box1, width, height)

    if box2[2] < box1[3]:
        y1, y2 = box2[2], box1[3]
    else:
        y1, y2 = box1[2], box2[3]


    area = (x2 - x1 + 1) * (y2 - y1 + 1)

    return area


def union_boxes(list_boxes, dilated, width, height):
    # 서로 겹치는 박스들을 병합해서 하나의 더 큰 박스로 만드는 알고리즘

    # bbox 좌표 리스트를 xmin 기준으로 정렬
    list_sort_xmin = sorted(list_boxes, key = itemgetter(0)) # itemgetter : 0번째 요소 기준으로 정렬
    print(list_sort_xmin)
    n_box = len(list_boxes) # 전체 바운딩 박스 개수

    # i번째 박스를 기준으로 다른 박스와 비교
    for i in range(n_box - 1):
        # 이미 병합되어 삭제(None)된 박스는 건너뜀
        if list_sort_xmin[i] is None:
            continue

        box = list_sort_xmin[i][:] # 병합 대상이 되는 박스 복사(원본 X)

        list_index_review = []

        # i 이외의 박스들과 겹치는지 확인
        for j in range(n_box):
            # 자기 자신이거나 이미 병합된 박스는 제외
            if list_sort_xmin[j] is None or j == i:
                continue

            # 두 박스 사이의 겹치는 면적을 계산하는 함수
            overlappend_area = compute_overlapped_area(
                                    box,
                                    list_sort_xmin[j],
                                    dilated,
                                    width,
                                    height
                                )

            min_area = min(area(box), area(list_sort_xmin[j]))
            thresh = 1 if dilated else (OVERLAP_FRACTION * min_area)

            # 병합 조건 충족 시 두 박스를 합쳐서 더 큰 박스로 만듬
            if overlappend_area > thresh:
                box  = merge(box, list_sort_xmin[j])

                list_sort_xmin[j] = None

                # 병합된 새 박스와 다시 겹치는 박스가 있는지 검토
                for k in list_index_review[::-1]:
                    if list_sort_xmin[k] is None:
                        continue

                    # 이전에 검토했던 박스들과 다시 겹치는지 확인(역순으로 순회)
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
            # 겹치지 않았던 박스는 기록
            else:
                list_index_review.append(j) # 현재 병합하지 않았지만 나중에 다시 검사할 필요가 있으므로 리스트에 저장

        # 병합된 박스(None) 제거 후 최종 바운딩 박스 값 저장
        list_boxes = [box for box in list_sort_xmin if box is not None]

        return list_boxes


def indent(elem, level = 0):
    i = "\n" + level * "  "

    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
        if not elem.tail or not elem.tail.strip():
            elem.tail = i

        for elem in elem:
            indent(elem, level + 1)

        if not elem.tail or not elem.tail.strip():
            elem.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i


def write_xml(output_path, filename,
              width, height, list_bbox):

    folder_name = ''.join(i for i in filename if not i.isdigit())
    folder_name = folder_name.strip('_')

    root = Element('annotation')
    SubElement(root, 'folder').text = DICT_FOLDER[folder_name]
    SubElement(root, 'filename').text = filename + '.jpg'
    source = SubElement(root, 'source')
    SubElement(source, 'database').text = 'NEU-DET'

    size = SubElement(root, 'size')
    SubElement(size, 'width').text = str(width)
    SubElement(size, 'height').text = str(height)
    SubElement(size, 'depth').text = '1'
    SubElement(root, 'segmented').text = '0'

    for (class_name, xmin, xmax, ymin, ymax) in list_bbox:
        # xmin, ymin, xmax, ymax = entry

        obj = SubElement(root, 'object')
        SubElement(obj, 'name').text = class_name
        SubElement(obj, 'pose').text = 'Unspecified'
        SubElement(obj, 'truncated').text = '0'
        SubElement(obj, 'difficult').text = '0'

        bbox = SubElement(obj, 'bndbox')
        SubElement(bbox, 'xmin').text = str(xmin)
        SubElement(bbox, 'ymin').text = str(ymin)
        SubElement(bbox, 'xmax').text = str(xmax)
        SubElement(bbox, 'ymax').text = str(ymax)

    tree = ElementTree(root)
    indent(root)
    xml_filename = os.path.join(output_path, filename + '.xml')
    tree.write(xml_filename)



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

