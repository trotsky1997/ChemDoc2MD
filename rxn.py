from email.mime import image
import glob
import os
from pydoc import doc
from paddleocr import PaddleOCR, draw_ocr
from copy import deepcopy
import re
import hashlib
from tqdm import tqdm
from multiprocessing import Pool, pool

def md5(string):
    return str(hashlib.md5(string.encode('utf-8')).hexdigest())


def docx_to_markdown(docx_path, md_path, image_dir):
    if docx_path.split('.')[-1] == 'doc':
        if os.path.exists(docx_path.replace('.doc', '.docx')):
            return
        else:
            print(f'Converting {docx_path} to {docx_path.replace(".doc", ".docx")}')
        os.system(f"libreoffice --headless --convert-to docx '{docx_path}' --outdir '{os.path.dirname(docx_path)}'")
        docx_path = docx_path.replace('.doc', '.docx')
    os.system(f"pandoc -f docx -t markdown '{docx_path}' -o '{md_path}' --extract-media '{image_dir}' --verbose")
    

def ocr_images(docx_path,image_dir,ocr,ocr_en):
    ocr_texts = {}
    for image_path in glob.glob(image_dir+'/*/*.*',recursive=True)+glob.glob(image_dir+'/*.*',recursive=True):
        raw_image_path = deepcopy(image_path)
        if image_path.endswith('wmf'):
            os.system(f"convert '{image_path}' -resize x100 '{image_path.replace('.wmf', '.png')}'")
            image_path = image_path.replace('.wmf', '.png')
        try:
            if raw_image_path.endswith('.wmf'):
                text = ocr_en.ocr(image_path, cls=True, det=True, rec=True)
            else:
                text = ocr.ocr(image_path, cls=True, det=True, rec=True)
            text = '\n'.join([t[-1][0] for t in text[0]])            
        except:
            text = ''
        ocr_texts[raw_image_path] = text
    print(ocr_texts)
    return ocr_texts

def replace_images_with_text(md_path, ocr_texts):
    with open(md_path, 'r', encoding='utf-8') as file:
        content = file.read()
    content = re.sub(r'!\[.*\]\(',"![](",content)
    # content = content.replace(f"![学科网(www.zxxk.com)\--教育资源门户，提供试题试卷、教案、课件、教学论文、素材等各类教学资源库下载，还有大量丰富的教学资讯！]", f'![]')
    for image_name, text in ocr_texts.items():
        print(image_name)
        # 确保 OCR 文本适合作为 Markdown 内容
        safe_text = text.replace('\n', '  ').replace('\r', '')
        content = content.replace(f"![]({image_name})", f'![{safe_text}]()')

    content = remove_width_substrings(content)

    with open(md_path, 'w', encoding='utf-8') as file:
        file.write(content)



def remove_width_substrings(text):
    # 正则表达式模式匹配以 {width 开头，以 } 结尾的子串
    pattern = r"\{width[^}]*in\"\}"
    # 使用空字符串替换找到的所有匹配项
    text = re.sub(pattern, '', text)
    pattern = r'height="[^"]*in"}'
    text = re.sub(pattern, '', text)
    return text

def main(a):
    try:
        main0(a)
    except:
        print(f'Error in {a}')

def main0(docx_path):
    image_dir = "./img"
    md_path = docx_path.replace(".docx", ".md").replace(".doc", ".md")
    a = docx_path
    if a.split('.')[-1] == 'doc':
        image_dir = image_dir + '/' + md5(docx_path.replace(".doc", ".docx"))
    else:
        image_dir = image_dir + '/' + md5(docx_path)
    if os.path.exists(image_dir):
        return
    ocr = PaddleOCR(use_angle_cls=True, lang="ch")  # 使用中文模型
    ocr_en = PaddleOCR(use_angle_cls=True, lang="en")

    print('Convert DOCX to Markdown and extract images')
    # Convert DOCX to Markdown and extract images
    docx_to_markdown(docx_path, md_path, image_dir)
    print('OCR on extracted images')
    # OCR on extracted images
    ocr_texts = ocr_images(docx_path,image_dir,ocr,ocr_en)
    print('Replace image links in Markdown with OCR text')
    # Replace image links in Markdown with OCR text
    replace_images_with_text(md_path, ocr_texts)
    del ocr,ocr_en,ocr_texts


if __name__ == "__main__":
    # os.system(f'rm -rf ./img')
    docx_paths = list(set(glob.glob("./*.docx",recursive=True)+glob.glob("./*/*.docx",recursive=True)+glob.glob("./*.doc",recursive=True)+glob.glob("./*/*.doc",recursive=True)))
    docx_paths = sorted(docx_paths)
    print(docx_paths)
    with pool.Pool(2) as p:
        p.map(main, docx_paths)