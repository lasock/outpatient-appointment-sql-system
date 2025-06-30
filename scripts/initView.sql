CREATE VIEW PatientBasicInfo AS
SELECT
P.Pid AS 患者ID,
P.Pname AS 姓名,
P.Psex AS 性别,
P.Pphone AS 电话,
U.Uname AS 用户名
FROM
Patients P
LEFT JOIN
Users U ON P.Pid = U.Uid;


CREATE VIEW v_lasock AS
SELECT
u.Uname AS 用户名,
p.Pname AS 姓名,
p.Psex AS 性别,
p.Pphone AS 电话,
a.ADate AS 日期,
a.ATimeSlot AS 时段,
d.Dname AS 医生,
de.Dename AS 科室,
a.Astatus AS 状态,
a.BookTime AS 预约时间
FROM Users u
JOIN Patients p ON u.Pid = p.Pid
JOIN Appointments a ON p.Pid = a.Pid
JOIN Doctors d ON a.Did = d.Did
JOIN Departments de ON d.DeID = de.DeID
WHERE u.Uname = 'lasock';
