from http import HTTPStatus
from flask import request
from flask_restful import Resource
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    get_jwt_identity,
    jwt_required,
    get_jwt
)
from utils import check_password
from models.user import User

# 存储注销的访问令牌
black_list = set()


# 令牌 用户可通过令牌访问和检查他们在系统注册的个人信息
# 即有些信息只有正确用户才能看，其他用户只能看到部分信息
class TokenResource(Resource):
    @staticmethod
    def post():
        json_data = request.get_json()
        email = json_data.get('email')
        password = json_data.get('password')
        user = User.get_by_email(email=email)
        if user.is_active is False:
            return {'message': 'The user account is not activated yet'}, HTTPStatus.FORBIDDEN
        # check_password将传入密码进行散列化，然后进行比较，非明文比较
        if not user or not check_password(password, user.password):
            return {'message': 'username or password is incorrect'}, HTTPStatus.UNAUTHORIZED
        # fresh=True
        access_token = create_access_token(identity=user.id, fresh=True)
        # 创建刷新令牌
        refresh_token = create_refresh_token(identity=user.id)
        return {'access_token': access_token, 'refresh_token': refresh_token}, HTTPStatus.OK


class RefreshResource(Resource):
    @jwt_required(refresh=True)
    def post(self):
        current_user = get_jwt_identity()
        # fresh=False 刷新令牌不需要输入凭据
        access_token = create_access_token(identity=current_user, fresh=False)
        return {'access_token': access_token}, HTTPStatus.OK


# revoke 取消/废除
class RevokeResource(Resource):
    @jwt_required()
    def post(self):
        # 得到访问令牌(有效载荷payload)
        jti = get_jwt()['jti']
        # 加入黑名单
        black_list.add(jti)
        return {'message': 'Successfully logged out'}, HTTPStatus.OK
