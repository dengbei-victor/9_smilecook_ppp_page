from flask import url_for
from marshmallow import Schema, fields, validate, ValidationError, validates, post_dump

from schemas.pagination import PaginationSchema
from schemas.user import UserSchema


def validate_num_of_servings(n):
    if n < 1:
        raise ValidationError('Number of servings must be greater than 0.')
    if n > 50:
        raise ValidationError('Number of servings must not be greater than 50.')


# 序列化（创建配方）和反序列化（检索配方）
# id: Use fields.Int() to represent an integer, and apply dump_only=True to specify that this property is only available for serialization.
# name: Use fields.String() to represent a string and apply required=True to indicate that this attribute is required.
# description: Use fields.String() to represent a string.
# num_of_servings: Use fields.Int() to represent an integer.
# cook_time: Use fields.Int() to represent an integer.
# directions: Use fields.String() to represent a string.
# is_publish: Use fields.Boolean() to represent a Boolean, and apply dump_only=True to specify that this attribute is only available for serialization.
# author: This attribute is used to display the author of the recipe.
# created_at: Use fields.DateTime to represent the format of the time, and dump_only=True means that this attribute is only available for serialization.
# updated_at: Use fields.DateTime to represent the format of the time, and dump_only=True means that this attribute is only available for serialization.
class RecipeSchema(Schema):
    class Meta:
        ordered = True
    id = fields.Integer(dump_only=True)
    name = fields.String(required=True, validate=[validate.Length(max=100)])
    description = fields.String(validate=[validate.Length(max=200)])
    ingredients = fields.String(validate=[validate.Length(max=1000)])
    directions = fields.String(validate=[validate.Length(max=1000)])
    num_of_servings = fields.Integer(validate=validate_num_of_servings)
    cook_time = fields.Integer()
    is_publish = fields.Boolean(dump_only=True)
    # 嵌入一个属性 从UserSchema中除了邮件全部展示
    author = fields.Nested(UserSchema(exclude=('email', )), attribute='user', dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)
    # 图像url
    cover_url = fields.Method(serialize='dump_cover_url')

    # 序列化图像url
    @staticmethod
    def dump_cover_url(recipe):
        if recipe.cover_image:
            return url_for('static', filename='images/recipes/{}'.format(recipe.cover_image), _external=True)
        else:
            return url_for('static', filename='images/assets/default-recipe-cover.jpg', _external=True)

    # 判断cook_time的有效性
    @validates('cook_time')
    def validate_cook_time(self, value):
        if value < 1:
            raise ValidationError('Cook time must be greater than 0.')
        if value > 300:
            raise ValidationError('Cook time must not be greater than 300.')


class RecipePaginationSchema(PaginationSchema):
    # 最终JSON从item属性中获取数据
    data = fields.Nested(RecipeSchema, attribute='items', many=True)





