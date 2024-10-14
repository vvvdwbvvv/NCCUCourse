import os
import psycopg2
from psycopg2.extensions import connection
from dotenv import load_dotenv

load_dotenv()
PATH = f"dbname='{os.getenv('DB_NAME')}' user='{os.getenv('DB_USER')}' password='{os.getenv('DB_PASSWORD')}' host='{os.getenv('DB_HOST')}' port='{os.getenv('DB_PORT')}'"

try:
    con = psycopg2.connect(PATH)
    print("Connected to the database successfully.")
except psycopg2.OperationalError as e:
    print(f"Failed to connect to the database: {e}")


class DB:
    con: connection

    def __init__(self, location: str) -> None:
        self.con = psycopg2.connect(location)
        cur = self.con.cursor()

        # Create tables
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
        cur.execute(
            "CREATE TABLE IF NOT EXISTS RATE ( courseId TEXT NOT NULL, rowId TEXT NOT NULL, teacherId TEXT, content TEXT, contentEn TEXT, PRIMARY KEY (courseId, rowId) )")
        cur.execute(
            "CREATE TABLE IF NOT EXISTS RESULT ( courseId TEXT PRIMARY KEY, yearsem TEXT, name TEXT, teacher TEXT, time TEXT, studentLimit INTEGER, studentCount INTEGER, lastEnroll INTEGER)")

        self.con.commit()

    def add_rate(self, row_id: str, course_id: str, teacher_id: str, content: str, content_en: str):
        cur = self.con.cursor()
        cur.execute(
            "INSERT INTO RATE (rowId, courseId, teacherId, content, contentEn) VALUES (%s, %s, %s, %s, %s) "
            "ON CONFLICT (courseId, rowId) DO UPDATE SET teacherId = EXCLUDED.teacherId, "
            "content = EXCLUDED.content, contentEn = EXCLUDED.contentEn",
            (row_id, course_id, teacher_id, content, content_en))
        self.con.commit()

    def add_teacher(self, id: str, name: str):
        cur = self.con.cursor()
        cur.execute(
            "INSERT INTO TEACHER (id, name) VALUES (%s, %s) ON CONFLICT (id, name) DO UPDATE SET name = EXCLUDED.name",
            (id, name))
        self.con.commit()

    def add_result(self, year_sem: str, course_id: str, name: str, teacher: str, time: str, student_limit: int,
                   student_count: int, last_enroll: int):
        cur = self.con.cursor()
        cur.execute(
            "INSERT INTO RESULT (courseId, yearsem, name, teacher, time, studentLimit, studentCount, lastEnroll) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s) "
            "ON CONFLICT (courseId) DO UPDATE SET "
            "yearsem = EXCLUDED.yearsem, name = EXCLUDED.name, teacher = EXCLUDED.teacher, "
            "time = EXCLUDED.time, studentLimit = EXCLUDED.studentLimit, "
            "studentCount = EXCLUDED.studentCount, lastEnroll = EXCLUDED.lastEnroll",
            (year_sem + course_id, year_sem, name, teacher, time, student_limit, student_count, last_enroll))
        self.con.commit()

    def get_teacher(self):
        cur = self.con.cursor()
        cur.execute("SELECT * FROM TEACHER")
        response = cur.fetchall()

        res = dict()
        for x in response:
            res[x[1]] = x[0]

        return res

    def add_course(self, course_data: dict, course_data_en: dict, dp1: str, dp2: str, dp3: str, syllabus: str,
                   description: str):
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
            '''INSERT INTO COURSE ( id, y, s,  subNum, name, nameEn, teacher, teacherEn, kind, time, timeEn, lmtKind, lmtKindEn, core, lang, langEn, smtQty, classroom, classroomId, unit, unitEn, dp1, dp2, dp3, point, subRemainUrl, subSetUrl, subUnitRuleUrl, teaExpUrl, teaSchmUrl, tranTpe, tranTpeEn, info, infoEn, note, noteEn, syllabus, objective ) 
              VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
              ON CONFLICT (id, dp1, dp2, dp3) DO UPDATE SET
              y = EXCLUDED.y, s = EXCLUDED.s, subNum = EXCLUDED.subNum, name = EXCLUDED.name, nameEn = EXCLUDED.nameEn,
              teacher = EXCLUDED.teacher, teacherEn = EXCLUDED.teacherEn, kind = EXCLUDED.kind, time = EXCLUDED.time,
              timeEn = EXCLUDED.timeEn, lmtKind = EXCLUDED.lmtKind, lmtKindEn = EXCLUDED.lmtKindEn, core = EXCLUDED.core,
              lang = EXCLUDED.lang, langEn = EXCLUDED.langEn, smtQty = EXCLUDED.smtQty, classroom = EXCLUDED.classroom,
              classroomId = EXCLUDED.classroomId, unit = EXCLUDED.unit, unitEn = EXCLUDED.unitEn, point = EXCLUDED.point,
              subRemainUrl = EXCLUDED.subRemainUrl, subSetUrl = EXCLUDED.subSetUrl, subUnitRuleUrl = EXCLUDED.subUnitRuleUrl,
              teaExpUrl = EXCLUDED.teaExpUrl, teaSchmUrl = EXCLUDED.teaSchmUrl, tranTpe = EXCLUDED.tranTpe,
              tranTpeEn = EXCLUDED.tranTpeEn, info = EXCLUDED.info, infoEn = EXCLUDED.infoEn, note = EXCLUDED.note,
              noteEn = EXCLUDED.noteEn, syllabus = EXCLUDED.syllabus, objective = EXCLUDED.objective;''',
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
                1 if course_data["core"] == "是" else 0,
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
        cur.execute('SELECT teaNam FROM COURSE WHERE y = %s AND s = %s', (y, s))
        response = cur.fetchall()

        return [str(x[0]) for x in response]

    def get_this_semester_course(self, y: str, s: str):
        cur = self.con.cursor()
        cur.execute('SELECT * FROM COURSE WHERE y = %s AND s = %s', (y, s))
        response = cur.fetchall()

        return response

    def is_course_exist(self, course_id: str, dp: dict):
        cur = self.con.cursor()
        cur.execute('SELECT COUNT(*) FROM COURSE WHERE id = %s AND dp1 = %s AND dp2 = %s AND dp3 = %s',
                    (course_id, dp["dp1"], dp["dp2"], dp["dp3"]))
        response = cur.fetchone()
        return response[0] > 0

    def is_rate_exist(self, course_id: str):
        cur = self.con.cursor()
        cur.execute('SELECT COUNT(DISTINCT courseId) FROM RATE WHERE courseId = %s', [course_id])
        response = cur.fetchone()
        return response[0] > 0


if __name__ == "__main__":
    db = DB(location)
    print(db.get_this_semester_course("111", "2"))
