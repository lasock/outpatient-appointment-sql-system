CREATE TABLE Patients(
    Pid INT IDENTITY(1,1) PRIMARY KEY,
    Pname NVARCHAR(50) NOT NULL,
    Psex CHAR(2) CHECK(Psex IN ('男','女')),
    Pphone CHAR(11) CHECK(
    Pphone LIKE '1[3456789]%' 
    AND LEN(Pphone) = 11
    AND Pphone NOT LIKE '%[^0-9]%' -- 确保全数字
    )
);

CREATE TABLE Departments(
    DeId INT IDENTITY PRIMARY KEY,
    DeName NVARCHAR(50),
    DeDescription NVARCHAR(255)
);

CREATE TABLE Doctors(
    Did INT IDENTITY PRIMARY KEY,
    Dname NVARCHAR(50) NOT NULL,
    Dsex CHAR(2) CHECK(Dsex IN ('男','女')),
    Dtitle NVARCHAR(50),
    DeId INT FOREIGN KEY REFERENCES Departments(DeId),
    Dphone CHAR(11) CHECK(
    Dphone LIKE '1[3456789]%' 
    AND LEN(Dphone) = 11
    AND Dphone NOT LIKE '%[^0-9]%' -- 确保全数字
    )
);
CREATE INDEX idx_doctors_dept ON Doctors(DeId);


CREATE TABLE Users(
    Uid INT IDENTITY PRIMARY KEY,
    Uname NVARCHAR(50) UNIQUE NOT NULL,
    Upassword NVARCHAR(256) NOT NULL,
    Pid INT FOREIGN KEY REFERENCES Patients(Pid)
);

CREATE TABLE Appointments(
    Aid INT IDENTITY PRIMARY KEY,
    Pid INT FOREIGN KEY REFERENCES Patients(Pid),
    Did INT FOREIGN KEY REFERENCES Doctors(Did),
    ADate DATE NOT NULL,
    Astatus NVARCHAR(20) DEFAULT '待就诊' CHECK (
        Astatus IN ('待就诊','已完成','已取消')
        ),
    ATimeSlot CHAR(4) CHECK(ATimeSlot IN ('上午','下午')),
    BookTime DATETIME NOT NULL DEFAULT GETDATE()
);
CREATE INDEX idx_appointments_patient ON Appointments(Pid);
CREATE INDEX idx_appointments_doctor ON Appointments(Did);

CREATE TABLE Schedules(
    Sid INT IDENTITY PRIMARY KEY,
    Did INT FOREIGN KEY REFERENCES Doctors(Did),
    WorkDay NVARCHAR(3) CHECK (
        WorkDay IN ('星期一', '星期二', '星期三', '星期四', '星期五', '星期六', '星期日')
        ), -- 存储星期几
    MaxPeople INT DEFAULT 30,
    CurrPeople INT,
    TimeSlot CHAR(4) CHECK(TimeSlot IN ('上午','下午'))
);
CREATE INDEX idx_schedules_doctor ON Schedules(Did);
