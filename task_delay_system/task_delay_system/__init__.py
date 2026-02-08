# Configure PyMySQL to work with Django (only if MySQL is being used)
# This will be imported when Django starts, so we need to handle the import gracefully
try:
    import pymysql
    pymysql.install_as_MySQLdb()
except ImportError:
    # PyMySQL not installed or not using MySQL - that's okay
    pass
