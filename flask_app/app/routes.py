from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import pyodbc
from datetime import datetime, timedelta
import logging
import os
import traceback

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

from db.db_config import get_connection
from scripts.hashcryto import hash_password, verify_password

# 获取当前文件的绝对路径
basedir = os.path.abspath(os.path.dirname(__file__))
# 创建 Flask 应用实例，指定模板文件夹路径
app = Flask(__name__, template_folder=os.path.join(basedir, '..', 'templates'))
app.secret_key = os.urandom(24)  # 请替换为实际的密钥

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# 首页
@app.route('/')
def index():
    if 'uid' in session:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

# 用户注册
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        pname = request.form['pname']
        psex = request.form['psex']
        pphone = request.form['pphone']

        # 验证手机号格式
        if not (pphone.startswith(('13', '14', '15', '16', '17', '18', '19')) and len(pphone) == 11):
            flash('手机号格式不正确')
            return redirect(url_for('register'))

        try:
            conn = get_connection()
            cursor = conn.cursor()

            # 检查用户名是否已存在
            cursor.execute("SELECT * FROM Users WHERE Uname = ?", username)
            if cursor.fetchone():
                flash('用户名已存在')
                return redirect(url_for('register'))

            # 插入患者信息
            cursor.execute(
                "INSERT INTO Patients (Pname, Psex, Pphone) OUTPUT INSERTED.Pid VALUES (?, ?, ?)",
                pname, psex, pphone
            )
            pid = cursor.fetchone()[0]

            # 插入用户信息
            hashed_pwd = hash_password(password)
            cursor.execute(
                "INSERT INTO Users (Uname, Upassword, Pid) VALUES (?, ?, ?)",
                username, hashed_pwd, pid
            )

            conn.commit()
            flash('注册成功，请登录')
            return redirect(url_for('login'))

        except Exception as e:
            logger.error(f"注册错误: {str(e)}")
            conn.rollback()
            flash('注册失败，请稍后再试')
            return redirect(url_for('register'))

        finally:
            if 'conn' in locals():
                conn.close()

    return render_template('register.html')

# 用户登录
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        try:
            conn = get_connection()
            cursor = conn.cursor()

            # 获取用户信息
            cursor.execute(
                "SELECT Uid, Upassword, Pid FROM Users WHERE Uname = ?", 
                username
            )
            user = cursor.fetchone()

            if user and verify_password(password, user.Upassword):
                session['uid'] = user.Uid
                session['pid'] = user.Pid
                session['username'] = username
                flash('登录成功')
                return redirect(url_for('dashboard'))
            else:
                flash('用户名或密码错误')
                return redirect(url_for('login'))

        except Exception as e:
            logger.error(f"登录错误: {str(e)}")
            flash('登录失败，请稍后再试')
            return redirect(url_for('login'))

        finally:
            if 'conn' in locals():
                conn.close()

    return render_template('login.html')

# 用户登出
@app.route('/logout')
def logout():
    session.clear()
    flash('您已成功登出')
    return redirect(url_for('index'))

# 用户仪表盘
@app.route('/dashboard')
def dashboard():
    if 'uid' not in session:
        return redirect(url_for('login'))

    try:
        conn = get_connection()
        cursor = conn.cursor()

        # 获取患者信息
        cursor.execute(
            "SELECT Pname, Psex, Pphone FROM Patients WHERE Pid = ?", 
            session['pid']
        )
        patient = cursor.fetchone()

        # 获取预约记录
        cursor.execute(
            """
            SELECT a.Aid, d.Dname, de.DeName, a.ADate, a.ATimeSlot, a.Astatus, a.BookTime
            FROM Appointments a
            JOIN Doctors d ON a.Did = d.Did
            JOIN Departments de ON d.DeId = de.DeId
            WHERE a.Pid = ?
            ORDER BY a.ADate DESC, a.BookTime DESC
            """, 
            session['pid']
        )
        appointments = cursor.fetchall()

        return render_template(
            'dashboard.html', 
            patient=patient, 
            appointments=appointments
        )

    except Exception as e:
        logger.error(f"仪表盘错误: {str(e)}")
        flash('获取信息失败')
        return redirect(url_for('index'))

    finally:
        if 'conn' in locals():
            conn.close()

# 查看排班
@app.route('/schedules')
def view_schedules():
    if 'uid' not in session:
        return redirect(url_for('login'))

    dept_id = request.args.get('dept_id', type=int)
    date_str = request.args.get('date')

    try:
        conn = get_connection()
        cursor = conn.cursor()

        # 获取所有科室
        cursor.execute("SELECT DeId, DeName FROM Departments")
        departments = cursor.fetchall()

        # 默认显示未来7天的排班
        if not date_str:
            date = datetime.now().date()
        else:
            date = datetime.strptime(date_str, '%Y-%m-%d').date()

        # 计算一星期的日期范围
        start_date = date
        end_date = start_date + timedelta(days=6)
        dates = [start_date + timedelta(days=i) for i in range(7)]
        
        # 修复：根据实际日期计算星期几
        weekdays = ['星期一', '星期二', '星期三', '星期四', '星期五', '星期六', '星期日']
        actual_weekdays = [weekdays[d.weekday()] for d in dates]  # 使用实际日期的星期几

        # 获取排班信息
        query = """
        SELECT s.Sid, s.WorkDay, s.TimeSlot, s.MaxPeople, s.CurrPeople, 
               d.Did, d.Dname, d.Dtitle, de.DeName
        FROM Schedules s
        JOIN Doctors d ON s.Did = d.Did
        JOIN Departments de ON d.DeId = de.DeId
        WHERE 1=1
        """
        params = []

        if dept_id:
            query += " AND d.DeId = ?"
            params.append(dept_id)

        query += " ORDER BY de.DeId, d.Did, s.WorkDay, s.TimeSlot"

        cursor.execute(query, params)
        schedules = cursor.fetchall()

        # 按科室、医生、日期和时间段组织排班数据
        organized_schedules = {}
        for s in schedules:
            dept_name = s.DeName
            if dept_name not in organized_schedules:
                organized_schedules[dept_name] = {}

            doctor_key = f"{s.Dname} ({s.Dtitle})"
            if doctor_key not in organized_schedules[dept_name]:
                organized_schedules[dept_name][doctor_key] = {}

            day_slot = f"{s.WorkDay}_{s.TimeSlot}"
            organized_schedules[dept_name][doctor_key][day_slot] = {
                'sid': s.Sid,
                'did': s.Did,
                'max': s.MaxPeople,
                'current': s.CurrPeople,
                'available': s.MaxPeople - s.CurrPeople
            }

        return render_template(
            'schedules.html',
            departments=departments,
            selected_dept=dept_id,
            dates=dates,
            weekdays=actual_weekdays,  # 使用修正后的星期几列表
            schedules=organized_schedules,
            start_date=start_date,
            timedelta=timedelta,
            zip=zip
        )

    except Exception as e:
        logger.error(f"排班查询错误: {str(e)}")
        logger.error(traceback.format_exc())
        flash('获取排班信息失败')
        return redirect(url_for('dashboard'))

    finally:
        if 'conn' in locals():
            conn.close()

# 预约挂号
@app.route('/book', methods=['POST'])
def book_appointment():
    if 'uid' not in session:
        return jsonify({'success': False, 'message': '请先登录'})

    sid = request.form.get('sid', type=int)
    did = request.form.get('did', type=int)
    date_str = request.form.get('date')

    if not sid or not did or not date_str:
        return jsonify({'success': False, 'message': '参数不完整'})

    try:
        date = datetime.strptime(date_str, '%Y-%m-%d').date()
        if date < datetime.now().date():
            return jsonify({'success': False, 'message': '不能预约过去的日期'})

        conn = get_connection()
        cursor = conn.cursor()

        # 检查排班是否存在且有余量
        cursor.execute(
            "SELECT WorkDay, TimeSlot, MaxPeople, CurrPeople FROM Schedules WHERE Sid = ?",
            sid
        )
        schedule = cursor.fetchone()

        # print(type(session['pid']))
        # pid = int(session['pid'])

        if not schedule:
            return jsonify({'success': False, 'message': '排班不存在'})

        if schedule.CurrPeople >= schedule.MaxPeople:
            return jsonify({'success': False, 'message': '该时段已约满'})

        # 检查患者是否已有同一天的预约
        cursor.execute(
            "SELECT 1 FROM Appointments WHERE Pid = ? AND ADate = ? AND Astatus = '待就诊'",
            session['pid'], date
        )
        if cursor.fetchone():
            return jsonify({'success': False, 'message': '您当天已有其他预约'})

        # 创建预约
        cursor.execute(
            """
            INSERT INTO Appointments (Pid, Did, ADate, Astatus, ATimeSlot)
            VALUES (?, ?, ?, '待就诊', ?)
            """,
            session['pid'], did, date, schedule.TimeSlot
        )

        # 更新排班当前人数
        cursor.execute(
            "UPDATE Schedules SET CurrPeople = CurrPeople + 1 WHERE Sid = ?",
            sid
        )

        conn.commit()
        return jsonify({'success': True, 'message': '预约成功'})

    except Exception as e:
        logger.error(f"预约错误: {str(e)}")
        logger.error(traceback.format_exc()) # 这将打印完整的错误回溯
        if 'conn' in locals():
            conn.rollback()
        return jsonify({'success': False, 'message': '预约失败，请稍后再试'})

    finally:
        if 'conn' in locals():
            conn.close()

# 取消预约
@app.route('/cancel', methods=['POST'])
def cancel_appointment():
    if 'uid' not in session:
        return jsonify({'success': False, 'message': '请先登录'})

    aid = request.form.get('aid', type=int)

    if not aid:
        return jsonify({'success': False, 'message': '参数不完整'})

    try:
        conn = get_connection()
        cursor = conn.cursor()

        # 获取预约信息
        cursor.execute(
            """
            SELECT a.Aid, a.Did, a.ADate, a.ATimeSlot, s.Sid
            FROM Appointments a
            JOIN Schedules s ON a.Did = s.Did AND 
                              DATENAME(WEEKDAY, a.ADate) LIKE s.WorkDay + '%' AND
                              a.ATimeSlot = s.TimeSlot
            WHERE a.Aid = ? AND a.Pid = ? AND a.Astatus = '待就诊'
            """,
            aid, session['pid']
        )
        appointment = cursor.fetchone()

        if not appointment:
            logger.error(traceback.format_exc()) # 这将打印完整的错误回溯
            return jsonify({'success': False, 'message': '预约不存在或无法取消'})

        # 更新预约状态
        cursor.execute(
            "UPDATE Appointments SET Astatus = '已取消' WHERE Aid = ?",
            aid
        )

        # 更新排班当前人数
        if appointment.Sid:
            cursor.execute(
                "UPDATE Schedules SET CurrPeople = CurrPeople - 1 WHERE Sid = ?",
                appointment.Sid
            )

        conn.commit()
        return jsonify({'success': True, 'message': '取消预约成功'})

    except Exception as e:
        logger.error(f"取消预约错误: {str(e)}")
        if 'conn' in locals():
            conn.rollback()
        return jsonify({'success': False, 'message': '取消预约失败'})

    finally:
        if 'conn' in locals():
            conn.close()



if __name__ == '__main__':
    app.run(debug=True)