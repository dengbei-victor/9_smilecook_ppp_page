class Config:
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'postgresql+psycopg2://victor:123456@localhost:5432/smilecook'
    # 如果设置成True(默认情况)，Flask-SQLAlchemy将会追踪对象的修改并且发送信号。这需要额外的内存，如果不必要的可以禁用它。
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # This is the key for encrypting the message and generating the signature
    # recommend that you use a complex string
    # 用于保护客户端会话的安全，可随机字符串
    SECRET_KEY = 'super-secret-key'
    # This is the key for the error message whenever there is an error
    # default value is msg, but we are setting that to the message here
    JWT_ERROR_MESSAGE_KEY = 'message'
    # 启动黑名单功能
    JWT_BLACKLIST_ENABLED = True
    # 检查访问和刷新令牌
    JWT_BLACKLIST_TOKEN_CHECKS = ['access', 'refresh']
    # 上传图像的路径
    UPLOADED_IMAGES_DEST = 'static/images'
