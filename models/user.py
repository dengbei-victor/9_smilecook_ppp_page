from extensions import db


# id: The identity of a user.
# username: The username of the user. The maximum length allowed is 80 characters. It can't be null and is a unique field.
# email: The user's email. The maximum length allowed is 200. It can't be blank and is a unique field.
# password: The user's password. The maximum length allowed is 200.
# is_active: This is to indicate whether the account is activated by email. It is a Boolean field with a default value of False.
# recipes: This doesn't create a field in the database table. This is just to define the relationship with the recipe model. So, subsequently, we can get all recipes using user.recipes.
# created_at: The creation time of the user.
# updated_at: The last update time of the user.

class User(db.Model):
    # __tablename__表名
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False, unique=True)
    email = db.Column(db.String(200), nullable=False, unique=True)
    password = db.Column(db.String(200))
    # bio = db.Column(db.String())
    # 图标
    avatar_image = db.Column(db.String(100), default=None)
    is_active = db.Column(db.Boolean(), default=False)
    created_at = db.Column(db.DateTime(), nullable=False, server_default=db.func.now())
    updated_at = db.Column(db.DateTime(), nullable=False, server_default=db.func.now(), onupdate=db.func.now())
    # 与Recipe模型建立关系， 参考user表
    recipes = db.relationship('Recipe', backref='user')

    @classmethod
    def get_by_username(cls, username):
        return cls.query.filter_by(username=username).first()

    @classmethod
    def get_by_email(cls, email):
        return cls.query.filter_by(email=email).first()

    @classmethod
    def get_by_id(cls, id):
        return cls.query.filter_by(id=id).first()

    def save(self):
        db.session.add(self)
        db.session.commit()

