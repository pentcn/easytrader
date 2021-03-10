import re

import requests
import base64
from PIL import Image

from easytrader import exceptions


class CodeDemo:
    def __init__(self, AK, SK, code_url, img_path):
        self.AK = AK
        self.SK = SK
        self.code_url = code_url
        self.img_path = img_path
        self.access_token = self.get_access_token()

    def get_access_token(self):
        token_host = 'https://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials&client_id={ak}&client_secret={sk}'.format(
            ak=self.AK, sk=self.SK)
        header = {'Content-Type': 'application/json; charset=UTF-8'}
        response = requests.post(url=token_host, headers=header)
        content = response.json()
        access_token = content.get("access_token")
        return access_token

    def getCode(self):
        header = {
            "Content-Type": "application/x-www-form-urlencoded"
        }

        def read_img():
            with open(self.img_path, "rb")as f:
                return base64.b64encode(f.read()).decode()

        image = read_img()
        response = requests.post(url=self.code_url, data={
                                 "image": image, "access_token": self.access_token}, headers=header)
        return response.json()


def captcha_recognize(img_path):
    import pytesseract

    im = Image.open(img_path).convert("L")
    # 1. threshold the image
    threshold = 200
    table = []
    for i in range(256):
        if i < threshold:
            table.append(0)
        else:
            table.append(1)

    out = im.point(table, "1")
    # 2. recognize with tesseract
    num = pytesseract.image_to_string(out)
    return num


def recognize_verify_code(image_path, broker="ht"):
    """识别验证码，返回识别后的字符串，使用 tesseract 实现
    :param image_path: 图片路径
    :param broker: 券商 ['ht', 'yjb', 'gf', 'yh']
    :return recognized: verify code string"""

    if broker == "gf":
        return detect_gf_result(image_path)
    if broker in ["yh_client", "gj_client"]:
        return detect_yh_client_result(image_path)
    # 调用 tesseract 识别
    return default_verify_code_detect(image_path)


def detect_yh_client_result(image_path):
    """用pentcn的账号申请百度的免费文字识别服务"""

    AK = "pvCwVGOC5vEq9tNpctyG3j3h"  # 官网获取的AK
    SK = "EgLsYDp20YktO7Po1OrDUnKZwqAoltwj"  # 官网获取的SK
    code_url = "https://aip.baidubce.com/rest/2.0/ocr/v1/accurate"  # 百度图片识别接口地址

    code_obj = CodeDemo(AK=AK, SK=SK, code_url=code_url, img_path=image_path)
    res = code_obj.getCode()
    return res.get("words_result")[0].get("words")


def input_verify_code_manual(image_path):
    from PIL import Image

    image = Image.open(image_path)
    image.show()
    code = input(
        "image path: {}, input verify code answer:".format(image_path)
    )
    return code


def default_verify_code_detect(image_path):
    from PIL import Image

    img = Image.open(image_path)
    return invoke_tesseract_to_recognize(img)


def detect_gf_result(image_path):
    from PIL import ImageFilter, Image

    img = Image.open(image_path)
    if hasattr(img, "width"):
        width, height = img.width, img.height
    else:
        width, height = img.size
    for x in range(width):
        for y in range(height):
            if img.getpixel((x, y)) < (100, 100, 100):
                img.putpixel((x, y), (256, 256, 256))
    gray = img.convert("L")
    two = gray.point(lambda p: 0 if 68 < p < 90 else 256)
    min_res = two.filter(ImageFilter.MinFilter)
    med_res = min_res.filter(ImageFilter.MedianFilter)
    for _ in range(2):
        med_res = med_res.filter(ImageFilter.MedianFilter)
    return invoke_tesseract_to_recognize(med_res)


def invoke_tesseract_to_recognize(img):
    import pytesseract

    try:
        res = pytesseract.image_to_string(img)
    except FileNotFoundError:
        raise Exception(
            "tesseract 未安装，请至 https://github.com/tesseract-ocr/tesseract/wiki 查看安装教程"
        )
    valid_chars = re.findall("[0-9a-z]", res, re.IGNORECASE)
    return "".join(valid_chars)
