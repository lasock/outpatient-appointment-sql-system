from db_config import get_connection
import os
from init_db import execute_sql_script


if __name__ == '__main__':
    conn = get_connection()
    script_path = os.path.join(os.path.dirname(__file__), '../scripts/initView.sql')
    execute_sql_script(script_path, conn)
    conn.close()