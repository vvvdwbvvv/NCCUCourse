import sqlite3

class DB:
  con: sqlite3.Connection
  
  def __init__(self, location: str) -> None:
    self.con = sqlite3.connect(location)
    cur = self.con.cursor()
    # subNam => name 科目名稱
    # lmtKind 通識類別
    # core 是否為核心通識
    # langTpe => lang 語言
    # smtQty N學期科目
    # subClassroom => classroom 教室
    # subGde => unit 開課單位
    # subKind => kind 必選群
    # subPoint => point 學分
    # subTime => time 時間
    
    cur.execute("""
      CREATE TABLE IF NOT EXISTS COURSE ( 
        id TEXT NOT NULL,
        y TEXT,
        s TEXT,
        subNum TEXT,
        name TEXT,
        nameEn TEXT,
        teacher TEXT,
        teacherEn TEXT,
        kind INTEGER,
        time TEXT,
        timeEn TEXT,
        lmtKind TEXT,
        lmtKindEn TEXT,
        core INTEGER,
        lang TEXT,
        langEn TEXT,
        smtQty INTEGER,
        classroom TEXT,
        classroomId TEXT,
        unit TEXT,
        unitEn TEXT,
        dp1 TEXT NOT NULL,
        dp2 TEXT NOT NULL,
        dp3 TEXT NOT NULL,
        point REAL,
        subRemainUrl TEXT,
        subSetUrl TEXT,
        subUnitRuleUrl TEXT,
        teaExpUrl TEXT,
        teaSchmUrl TEXT,
        tranTpe TEXT,
        tranTpeEn TEXT,
        info TEXT,
        infoEn TEXT,
        note TEXT,
        noteEn TEXT,
        syllabus TEXT,
        objective TEXT,
        PRIMARY KEY ( id, dp1, dp2, dp3 )
      );
    """)
    cur.execute("CREATE TABLE IF NOT EXISTS TEACHER ( id TEXT, name TEXT, PRIMARY KEY ( id, name ) )")
    cur.execute("CREATE TABLE IF NOT EXISTS RATE ( courseId TEXT NOT NULL, rowId TEXT NOT NULL, teacherId TEXT, content TEXT, contentEn TEXT, PRIMARY KEY (courseId, rowId) )")
    cur.execute("CREATE TABLE IF NOT EXISTS RESULT ( courseId TEXT, yearsem TEXT, name TEXT, teacher TEXT, time TEXT, studentLimit INTEGER, studentCount INTEGER, lastEnroll INTEGER, PRIMARY KEY (courseId))")
    
  def add_rate(self, row_id: str, course_id: str, teacher_id: str, content: str, content_en: str):
    cur = self.con.cursor()
    cur.execute("INSERT OR REPLACE INTO RATE (row_id, course_id, teacher_id, content, content_en) VALUES (?, ?, ?, ?, ?)", (row_id, course_id, teacher_id, content, content_en))
    self.con.commit()
  
  def add_teacher(self, id: str, name: str):
    cur = self.con.cursor()
    cur.execute("INSERT OR REPLACE INTO TEACHER (id, name) VALUES (?, ?)", (id, name))
    self.con.commit()
  
  def add_result(self, year_sem: str, course_id: str, name: str, teacher: str, time: str, student_limit: int, student_count: int, last_enroll: int):
    cur = self.con.cursor()
    cur.execute("INSERT OR REPLACE INTO RESULT (course_id, year_sem, name, teacher, time, student_limit, student_count, last_enroll) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", (year_sem + course_id, year_sem, name, teacher, time, student_limit, student_count, last_enroll))
    self.con.commit()
    
  def get_teacher(self):
    cur = self.con.cursor()
    request = cur.execute("SELECT * FROM TEACHER")
    response = request.fetchall()
    
    res = dict()
    for x in response:
      res[x[1]] = x[0]
    
    return res
  
  def add_course(self, course_data: dict, course_data_en: dict, dp1: str, dp2: str, dp3: str, syllabus: str, description: str):
    if course_data["subKind"] == "必修":
      kind = 1
    elif course_data["subKind"] == "選修":
      kind = 2
    elif course_data["subKind"] == "群修":
      kind = 3
    elif "通識" in course_data["lmtKind"]:
      kind = 4
    else:
      kind = 0
        
    cur = self.con.cursor()
    cur.execute(
      '''INSERT OR REPLACE INTO COURSE ( id, y, s,  subNum, name, nameEn, teacher, teacherEn, kind, time, timeEn, lmtKind, lmtKindEn, core, lang, langEn, smtQty, classroom, classroomId, unit, unitEn, dp1, dp2, dp3, point, subRemainUrl, subSetUrl, subUnitRuleUrl, teaExpUrl, teaSchmUrl, tranTpe, tranTpeEn, info, infoEn, note, noteEn, syllabus, objective ) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);''',
      (
        "{}{}{}".format(course_data["y"], course_data["s"], course_data["subNum"]),
        course_data["y"],
        course_data["s"],
        course_data["subNum"],
        course_data["subNam"],
        course_data_en["subNam"],
        course_data["teaNam"],
        course_data_en["teaNam"],
        kind,
        course_data["subTime"],
        course_data_en["subTime"],
        course_data["lmtKind"],
        course_data_en["lmtKind"],
        (lambda x:1 if x == "是" else 0)(course_data["core"]),
        course_data["langTpe"],
        course_data_en["langTpe"],
        course_data["smtQty"],
        course_data["subClassroom"],
        course_data_en["subClassroom"],
        course_data["subGde"],
        course_data_en["subGde"],
        dp1,
        dp2,
        dp3,
        float(course_data["subPoint"]),
        course_data["subRemainUrl"],
        course_data["subSetUrl"],
        course_data["subUnitRuleUrl"],
        course_data["teaExpUrl"],
        course_data["teaSchmUrl"],
        course_data["tranTpe"],
        course_data_en["tranTpe"],
        course_data["info"],
        course_data_en["info"],
        course_data["note"],
        course_data_en["note"],
        syllabus, description
      )
    )
    self.con.commit()
  
  def get_course(self, y: str, s: str):
    cur = self.con.cursor()
    request = cur.execute('SELECT teaNam FROM COURSE WHERE y = 111 AND s = 2')
    response = request.fetchall()
    
    return [str(x[0]) for x in response]
  
  def get_this_semester_course(self, y: str, s: str):
    cur = self.con.cursor()
    request = cur.execute('SELECT DISTINCT subNum FROM COURSE WHERE y = ? AND s = ?', [y, s])
    response = request.fetchall()
    
    return [str(x[0]) for x in response]

  def is_course_exist(self, course_id: str, dp: dict):
    cur = self.con.cursor()
    request = cur.execute('SELECT COUNT(*) FROM COURSE WHERE id = ? AND dp1 = ? AND dp2 = ? AND dp3 = ?', [course_id, dp["dp1"], dp["dp2"], dp["dp3"]])
    response = request.fetchone()
    return response[0] > 0
  
  def is_rate_exist(self, course_id: str):
    cur = self.con.cursor()
    request = cur.execute('SELECT COUNT( DISTINCT courseId) FROM RATE WHERE courseId = ?', [course_id])
    response = request.fetchone()
    return response[0] > 0

if __name__ == "__main__":
  db = DB("test.db")
  print(db.get_this_semester_course("111", "2"))