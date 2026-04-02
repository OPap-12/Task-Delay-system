# Configure PyMySQL to work with Django (only if MySQL is being used)
try:
    import pymysql
    pymysql.install_as_MySQLdb()
except ImportError:
    pass