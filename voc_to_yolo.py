import xml.etree.ElementTree as ET
from tqdm import tqdm
from pathlib import Path
import os
import shutil

ROOT_FOLDER_PATH = '../datasets'
VOC_FOLDER_PATH = os.path.join(ROOT_FOLDER_PATH, 'NEU-DET')
LABELS = ['crazing', 'inclusion', 'patches',
          'pitted_surface', 'rolled-in_scale', 'scratches'
]
COPY_IMG = False


def convet_box(size, box):
    pass

def convert_label(in_fp, out_fp):
    pass


for image_set in ['train', 'validation']:
    imgs_path = Path(f'{ROOT_FOLDER_PATH}/NEU-DET')
