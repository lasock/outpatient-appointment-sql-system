from db_config import get_connection
import os

def execute_sql_script(file_path, conn):
    with open(file_path, 'r', encoding='utf-8') as f:
        sql_commands = f.read().split(';')
        cursor = conn.cursor()
        for command in sql_commands:
            command = command.strip()
            if command:
                try:
                    cursor.execute(command)
                except Exception as e:
                    print(f'执行失败：\n{command}\n错误：{e}')
        conn.commit()
        cursor.close()


if __name__ == '__main__':
    conn = get_connection()
    script_path = os.path.join(os.path.dirname(__file__), '../scripts/initTable.sql')
    execute_sql_script(script_path, conn)
    conn.close()
