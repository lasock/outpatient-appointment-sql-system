import pyodbc

# 
# Windows身份验证连接sql
DB_CONFIG = {
    'driver': '{ODBC Driver 17 for SQL Server}',
    'server': 'localhost',
    'database': 'test',
    'trusted_connection': 'yes'
}

def get_connection():
    conn_str = (
        f"DRIVER={DB_CONFIG['driver']};"
        f"SERVER={DB_CONFIG['server']};"
        f"DATABASE={DB_CONFIG['database']};"
        f"Trusted_Connection={DB_CONFIG['trusted_connection']};"
    )
    return pyodbc.connect(conn_str)


if __name__ == '__main__':
    try:
        connection = get_connection()
        print("连接数据库成功")
    except Exception as e:
        print("连接错误：", e)
        exit()

    connection.close()