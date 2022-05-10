import os
import uuid

from PIL import Image
from flask_uploads import extension
from passlib.hash import pbkdf2_sha256
from itsdangerous import URLSafeTimedSerializer
from flask import current_app


# 加密
from extensions import image_set


def hash_password(password):
    return pbkdf2_sha256.hash(password)


# 检查密码正确性
def check_password(password, hashed):
    return pbkdf2_sha256.verify(password, hashed)


# salt用于区分不同令牌 例如创建 重置密码 升级账户等
# 通过邮件创建令牌 URLSafeTimedSerializer规定（安全）时间序列化
def generate_token(email, salt=None):
    serializer = URLSafeTimedSerializer(current_app.config.get('SECRET_KEY'))
    return serializer.dumps(email, salt=salt)


# 在指定时间内可以验证令牌，30*60 30min
def verify_token(token, max_age=(30 * 60), salt=None):
    serializer = URLSafeTimedSerializer(current_app.config.get('SECRET_KEY'))
    try:
        email = serializer.loads(token, max_age=max_age, salt=salt)
    except:
        return False
    return email


# uuid生成文件名
# 保存目的地是static/images。如果我们folder="avatar"作为参数传入，目标图像将会存储在static/images/avatar
# 保存目的地在config.py中配置
def save_image(image, folder):
    filename = '{}.{}'.format(uuid.uuid4(), extension(image.filename))
    image_set.save(image, folder=folder, name=filename)
    filename = compress_image(filename=filename, folder=folder)
    return filename


# 压缩图像
def compress_image(filename, folder):
    file_path = image_set.path(filename=filename, folder=folder)
    # 创建图像对象
    image = Image.open(file_path)
    if image.mode != "RGB":
        image = image.convert("RGB")
    # 使图像宽高小于1600像素 同时保持横纵比不变
    if max(image.width, image.height) > 1600:
        maxsize = (1600, 1600)
        image.thumbnail(maxsize)

    compressed_filename = '{}.jpg'.format(uuid.uuid4())
    compressed_file_path = image_set.path(filename=compressed_filename, folder=folder)
    # quality 大于95几乎没优化
    image.save(compressed_file_path, optimize=True, quality=85)

    original_size = os.stat(file_path).st_size
    compressed_size = os.stat(compressed_file_path).st_size
    percentage = round((original_size - compressed_size) / original_size * 100)

    print("The file size is reduced by {}%, from {} to {}.".format(percentage, original_size, compressed_size))
    # 删除原始图像
    os.remove(file_path)
    return compressed_filename
