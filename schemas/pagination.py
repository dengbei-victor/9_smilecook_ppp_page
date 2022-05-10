from flask import request
from marshmallow import Schema, fields
from urllib.parse import urlencode


# 这些属性由 Flask-SQLAlchemy 中的分页对象自动生成
# first: The link to the first page
# last: The link to the last page
# prev: The link to the previous page
# next: The link to the next page
# page: The current page
# pages: The total number of pages
# per_page: The number of records per page
# total: The total number of records
# data: The actual data records on this page   schema/recipe
class PaginationSchema(Schema):
    class Meta:
        ordered = True
    # 自定义如何序列化我们的对象
    links = fields.Method(serialize='get_pagination_links')
    page = fields.Integer(dump_only=True)
    pages = fields.Integer(dump_only=True)
    per_page = fields.Integer(dump_only=True)
    # total = fields.Integer(dump_only=True)
    # 修改Json（序列化后）键  属性依旧total
    total_count = fields.Integer(dump_only=True, attribute='total')

    # 根据页码生成页面url 并添加至request参数的字典中
    @staticmethod
    def get_url(page):
        query_args = request.args.to_dict()
        query_args['page'] = page
        return '{}?{}'.format(request.base_url, urlencode(query_args))

    # 生成指向不同页面的url
    def get_pagination_links(self, paginated_objects):
        pagination_links = {
            'first': self.get_url(page=1),
            'last': self.get_url(page=paginated_objects.pages)
        }
        if paginated_objects.has_prev:
            pagination_links['prev'] = self.get_url(page=paginated_objects.prev_num)
        if paginated_objects.has_next:
            pagination_links['next'] = self.get_url(page=paginated_objects.next_num)
        return pagination_links

