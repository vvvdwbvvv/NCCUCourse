import pytest
from DB import DB

@pytest.fixture
def db():
    return DB(location="testdb", user="youruser", password="yourpassword", host="localhost", port="5432")

def test_get_this_semester_course(db):
    courses = db.get_this_semester_course("111", "2")
    assert isinstance(courses, list)