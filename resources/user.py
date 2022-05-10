import os

from flask import request, url_for, render_template
# https://flask-jwt-extended.readthedocs.io/en/stable/v4_upgrade_guide/ 版本变化
from flask_jwt_extended import get_jwt_identity, jwt_required
from flask_restful import Resource
from http import HTTPStatus

from marshmallow import ValidationError
from webargs import fields
from webargs.flaskparser import use_kwargs

from extensions import image_set
from mailgun import MailgunApi
from models.recipe import Recipe
from schemas.recipe import RecipeSchema, RecipePaginationSchema
from schemas.user import UserSchema
from models.user import User


# schema.dump().data --》 data弃用 直接使用schema.dump()返回数据
from utils import generate_token, verify_token, save_image

user_schema = UserSchema()
# 排除邮箱 未经过验证或正在访问其他人的url端点时 隐藏电子邮件
user_public_schema = UserSchema(exclude=('email', ))
# 一个用户存在多个recipe
recipe_list_schema = RecipeSchema(many=True)
# mailgun对象
mailgun = MailgunApi(domain=os.environ.get('MAILGUN_DOMAIN'),
                     api_key=os.environ.get('MAILGUN_API_KEY'))
# 用户图标schema 只显示avatar_url
user_avatar_schema = UserSchema(only=('avatar_url', ))
# 分页所展示的schema
recipe_pagination_schema = RecipePaginationSchema()


class UserListResource(Resource):
    @staticmethod
    def post():
        json_data = request.get_json()
        try:
            # load 反序列化
            data = user_schema.load(data=json_data)
        except ValidationError as exc:
            return {'message': "Validation errors", 'errors': exc.messages}, HTTPStatus.BAD_REQUEST
        # 用户名或邮箱存在
        if User.get_by_username(data.get('username')):
            return {'message': 'username already used'}, HTTPStatus.BAD_REQUEST
        if User.get_by_email(data.get('email')):
            return {'message': 'email already used'}, HTTPStatus.BAD_REQUEST
        user = User(**data)
        token = generate_token(user.email, salt='activate')
        subject = 'Please confirm your registration.'
        # API <-> endpoint <-> function
        # 在app.py中add_resource将对应资源与其endpoint（默认名字小写 即useractivateresource）进行映射
        link = url_for('useractivateresource',
                       token=token,
                       _external=True)
        text = 'Hi, Thanks for using SmileCook! Please confirm your registration by clicking on the link: {}'.format(link)
        # 发送激活邮件
        mailgun.send_email(to=user.email,
                           subject=subject,
                           text=text,
                           html=render_template('email/confirmation.html', link=link))
        user.save()
        # dump 序列化
        return user_schema.dump(user), HTTPStatus.CREATED


class UserResource(Resource):
    # token参数可选
    @jwt_required(optional=True)
    def get(self, username):
        user = User.get_by_username(username=username)
        if user is None:
            return {'message': 'user not found'}, HTTPStatus.NOT_FOUND
        # 根据token得到用户id
        current_user = get_jwt_identity()
        if current_user == user.id:
            data = user_schema.dump(user)
        else:
            data = user_public_schema.dump(user)
        return data, HTTPStatus.OK


# 仅通过令牌token就可以访问用户信息，url中不需要其他信息
class MeResource(Resource):
    @jwt_required()
    def get(self):
        user = User.get_by_id(id=get_jwt_identity())
        return user_schema.dump(user), HTTPStatus.OK


# 获取特定用户的recipes
class UserRecipeListResource(Resource):
    @jwt_required(optional=True)
    #  location="query" 对请求值进行加载
    @use_kwargs({'page': fields.Int(missing=1), 'per_page': fields.Int(missing=10), 'visibility': fields.Str(missing='public')}, location="query")
    def get(self, username, page, per_page, visibility):
        user = User.get_by_username(username=username)
        if user is None:
            return {'message': 'User not found'}, HTTPStatus.NOT_FOUND
        current_user = get_jwt_identity()
        if current_user == user.id and visibility in ['all', 'private']:
            pass
        else:
            visibility = 'public'
        paginated_recipes = Recipe.get_all_by_user(user_id=user.id, page=page, per_page=per_page, visibility=visibility)
        return recipe_pagination_schema.dump(paginated_recipes), HTTPStatus.OK


# 用户激活resource
class UserActivateResource(Resource):
    @staticmethod
    def get(token):
        email = verify_token(token, salt='activate')
        if email is False:
            return {'message': 'Invalid token or token expired'}, HTTPStatus.BAD_REQUEST
        user = User.get_by_email(email=email)
        if not user:
            return {'message': 'User not found'}, HTTPStatus.NOT_FOUND
        if user.is_active is True:
            return {'message': 'The user account is already activated'}, HTTPStatus.BAD_REQUEST
        user.is_active = True
        user.save()
        return {}, HTTPStatus.NO_CONTENT


# 图标上传resource
class UserAvatarUploadResource(Resource):
    @jwt_required()
    def put(self):
        # 上传的form表单 name “avatar”
        file = request.files.get('avatar')
        # 验证图像是否存在 文件扩展名是否允许
        if not file:
            return {'message': 'Not a valid image'}, HTTPStatus.BAD_REQUEST
        if not image_set.file_allowed(file, file.filename):
            return {'message': 'File type not allowed'}, HTTPStatus.BAD_REQUEST
        user = User.get_by_id(id=get_jwt_identity())
        if user.avatar_image:
            avatar_path = image_set.path(folder='avatars', filename=user.avatar_image)
            if os.path.exists(avatar_path):
                os.remove(avatar_path)
        filename = save_image(image=file, folder='avatars')
        user.avatar_image = filename
        user.save()
        return user_avatar_schema.dump(user), HTTPStatus.OK
