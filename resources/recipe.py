import os

from flask import request
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_restful import Resource
from http import HTTPStatus

from webargs import fields
from webargs.flaskparser import use_kwargs
from marshmallow import ValidationError

from extensions import image_set
from models.recipe import Recipe
from schemas.recipe import RecipeSchema, RecipePaginationSchema
from utils import save_image

recipe_schema = RecipeSchema()
recipe_list_schema = RecipeSchema(many=True)
# recipe图像schema
recipe_cover_schema = RecipeSchema(only=('cover_url', ))
# 分页schema
recipe_pagination_schema = RecipePaginationSchema()


class RecipeListResource(Resource):
    # keyword 添加一些参数并进行初始化
    # 由于版本变更 需要添加location="query" 否则无法识别参数
    # https://webargs.readthedocs.io/en/latest/upgrading.html#upgrading-to-6-0
    @use_kwargs({'q': fields.Str(missing=''), 'page': fields.Int(missing=1),
                 'per_page': fields.Int(missing=20),
                 'sort': fields.Str(missing='created_at'),
                 'order': fields.Str(missing='desc')}, location="query")
    def get(self, q, page, per_page, sort, order):
        # sort和order参数值
        if sort not in ['created_at', 'cook_time', 'num_of_servings']:
            sort = 'created_at'
        if order not in ['asc', 'desc']:
            order = 'desc'
        paginated_recipes = Recipe.get_all_published(q, page, per_page, sort, order)
        return recipe_pagination_schema.dump(paginated_recipes), HTTPStatus.OK

    @jwt_required()
    def post(self):
        json_data = request.get_json()
        current_user = get_jwt_identity()
        try:
            # load 反序列化 json -》 obj
            data = recipe_schema.load(data=json_data)
        except ValidationError as exc:
            return {'message': "Validation errors", 'errors': exc.messages}, HTTPStatus.BAD_REQUEST
        recipe = Recipe(**data)
        recipe.user_id = current_user
        recipe.save()
        # dump 序列化  obj -》 json
        return recipe_schema.dump(recipe), HTTPStatus.CREATED


class RecipeResource(Resource):
    @jwt_required(optional=True)
    def get(self, recipe_id):
        recipe = Recipe.get_by_id(recipe_id=recipe_id)
        if recipe is None:
            return {'message': 'Recipe not found'}, HTTPStatus.NOT_FOUND
        current_user = get_jwt_identity()
        if recipe.is_publish is False and recipe.user_id != current_user:
            return {'message': 'Access is not allowed'}, HTTPStatus.FORBIDDEN
        return recipe_schema.dump(recipe), HTTPStatus.OK

    @jwt_required(optional=False)
    def patch(self, recipe_id):
        json_data = request.get_json()
        try:
            # load 反序列化 json -》 obj
            data = recipe_schema.load(data=json_data, partial=('name',))
        except ValidationError as exc:
            return {'message': "Validation errors", 'errors': exc.messages}, HTTPStatus.BAD_REQUEST

        recipe = Recipe.get_by_id(recipe_id=recipe_id)

        if recipe is None:
            return {'message': 'Recipe not found'}, HTTPStatus.NOT_FOUND
        current_user = get_jwt_identity()

        if current_user != recipe.user_id:
            return {'message': 'Access is not allowed'}, HTTPStatus.FORBIDDEN

        recipe.name = data.get('name') or recipe.name
        recipe.description = data.get('description') or recipe.description
        recipe.num_of_servings = data.get('num_of_servings') or recipe.num_of_servings
        recipe.cook_time = data.get('cook_time') or recipe.cook_time
        recipe.directions = data.get('directions') or recipe.directions
        recipe.ingredients = data.get('ingredients') or recipe.ingredients
        recipe.save()
        return recipe_schema.dump(recipe), HTTPStatus.OK

    @jwt_required(optional=False)
    def delete(self, recipe_id):
        recipe = Recipe.get_by_id(recipe_id=recipe_id)
        if recipe is None:
            return {'message': 'Recipe not found'}, HTTPStatus.NOT_FOUND
        current_user = get_jwt_identity()
        if current_user != recipe.user_id:
            return {'message': 'Access is not allowed'}, HTTPStatus.FORBIDDEN
        recipe.delete()
        return {}, HTTPStatus.NO_CONTENT


class RecipePublishResource(Resource):
    @jwt_required(optional=False)
    def put(self, recipe_id):
        recipe = Recipe.get_by_id(recipe_id=recipe_id)
        if recipe is None:
            return {'message': 'Recipe not found'}, HTTPStatus.NOT_FOUND
        current_user = get_jwt_identity()
        if current_user != recipe.user_id:
            return {'message': 'Access is not allowed'}, HTTPStatus.FORBIDDEN
        recipe.is_publish = True
        recipe.save()
        return {}, HTTPStatus.NO_CONTENT

    @jwt_required(optional=False)
    def delete(self, recipe_id):
        recipe = Recipe.get_by_id(recipe_id=recipe_id)
        if recipe is None:
            return {'message': 'Recipe not found'}, HTTPStatus.NOT_FOUND
        current_user = get_jwt_identity()
        if current_user != recipe.user_id:
            return {'message': 'Access is not allowed'}, HTTPStatus.FORBIDDEN
        recipe.is_publish = False
        recipe.save()
        return {}, HTTPStatus.NO_CONTENT


class RecipeCoverUploadResource(Resource):
    @jwt_required()
    def put(self, recipe_id):
        # form表单
        file = request.files.get('cover')
        if not file:
            return {'message': 'Not a valid image'}, HTTPStatus.BAD_REQUEST
        if not image_set.file_allowed(file, file.filename):
            return {'message': 'File type not allowed'}, HTTPStatus.BAD_REQUEST
        recipe = Recipe.get_by_id(recipe_id=recipe_id)
        if recipe is None:
            return {'message': 'Recipe not found'}, HTTPStatus.NOT_FOUND
        current_user = get_jwt_identity()
        # 用户是否有权修改
        if current_user != recipe.user_id:
            return {'message': 'Access is not allowed'}, HTTPStatus.FORBIDDEN
        if recipe.cover_image:
            cover_path = image_set.path(folder='recipes', filename=recipe.cover_image)
            if os.path.exists(cover_path):
                os.remove(cover_path)
        filename = save_image(image=file, folder='recipes')
        recipe.cover_image = filename
        recipe.save()
        return recipe_cover_schema.dump(recipe), HTTPStatus.OK
