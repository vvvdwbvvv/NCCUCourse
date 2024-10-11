from bs4 import BeautifulSoup
from time import sleep
import os
import json
import logging
import tqdm
import requests
import datetime
import argparse
import csv
from DB import DB

from User import User
from constant import YEAR_SEM, YEAR, SEM, course_result_csv, COURSERESULT_YEARSEM
from fetchDescription import fetch_description
from fetchRate import fetch_rate

# from translateRate import translateRate

all_semesters = [
    "1011",
    "1012",
    "1021",
    "1022",
    "1031",
    "1032",
    "1041",
    "1042",
    "1051",
    "1052",
    "1061",
    "1062",
    "1071",
    "1072",
    "1081",
    "1082",
    "1091",
    "1092",
    "1101",
    "1102",
    "1111",
    "1112",
    "1121",
    "1122",
    "1131",
]

dirPath = os.path.dirname(os.path.realpath(__file__))

parser = argparse.ArgumentParser()
parser.add_argument("--course", action="store_true", help="Fetch class")
parser.add_argument("--fast", action="store_true", help="Fetch this semester only")
parser.add_argument("--teacher", action="store_true", help="Fetch teacher")
parser.add_argument("--rate", action="store_true", help="Fetch rate")
parser.add_argument("--result", action="store_true", help="Fetch result")
parser.add_argument("--db", help="Database name", default="test.db")
args = parser.parse_args()

if __name__ == "__main__":

    # Setup logger
    logging.basicConfig(
        filename="log.log",
        format="%(asctime)s [%(levelname)s] %(message)s",
        encoding="utf-8",
    )

    if os.path.exists(os.path.join(dirPath, "_data")):
        os.makedirs(os.path.join(dirPath, "_data"), exist_ok=True)

    db = DB(args.db)

    # ==============================
    # \ 1. Fetch Classes           \
    # ==============================

    if args.course:
        # fetch all deps first, make a single search less than 500
        try:
            units = requests.get("https://qrysub.nccu.edu.tw/assets/api/unit.json")
            units.raise_for_status()
            units = units.json()
        except Exception:
            logging.error("Failed to get unit list, falls back to local cache")
            with open("data/unit.json") as f:
                units = json.load(f)

        categories = list()
        for dp1 in [x for x in units if x["utCodL1"] != "0"]:
            for dp2 in [x for x in dp1["utL2"] if x["utCodL2"] != "0"]:
                for dp3 in [x for x in dp2["utL3"] if x["utCodL3"] != "0"]:
                    categories.append(
                        {
                            "dp1": dp1["utCodL1"],
                            "dp2": dp2["utCodL2"],
                            "dp3": dp3["utCodL3"],
                        }
                    )

        # run through all deps, get their classId
        courses_list = list()
        tqdm_categories = tqdm.tqdm(categories, leave=False)
        for category in tqdm_categories:
            tqdm_categories.set_postfix_str("{}".format(category))
            if args.fast:
                semesters = all_semesters[-1:]
            else:
                semesters = tqdm.tqdm(all_semesters, leave=False)
            for semester in semesters:
                if not args.fast:
                    semesters.set_postfix_str("processing: {}".format(semester))
                try:
                    sleep(0.1)
                    res = requests.get(
                        "https://es.nccu.edu.tw/course/zh-TW/:sem={} :dp1={} :dp2={} :dp3={}".format(
                            semester, category["dp1"], category["dp2"], category["dp3"]
                        )
                    )
                    res.raise_for_status()
                    courses = res.json()
                    if len(courses) >= 500:
                        raise Exception("{} too large".format(category))

                    # Add to courseList
                    if semester == YEAR_SEM:
                        courses_list += [x["subNum"] for x in courses]

                    # Write to databse
                    for course in tqdm.tqdm(courses, leave=False):
                        course_id = "{}{}".format(semester, course["subNum"])
                        # if db.isCourseExist(courseId, category):
                        #   continue
                        detail = fetch_description(course_id)
                        db.add_course(
                            detail["qrysub"],
                            detail["qrysubEn"],
                            category["dp1"],
                            category["dp2"],
                            category["dp3"],
                            "".join(detail["description"]),
                            "".join(detail["objectives"]),
                        )
                except Exception as e:
                    logging.error(e)

        logging.debug(courses_list)

        print("Fetch Class done at {}".format(datetime.datetime.now()))
    else:
        print("Skipping Fetch Class")

    # ==============================
    # \ 2. Fetch TeacherId         \
    # ==============================

    if args.teacher:
        # Read course list
        courses_list = db.get_this_semester_course(YEAR, SEM)

        user = User()

        # Delete exist track courses before adding
        courses = user.get_track()
        if len(courses) > 0:
            tqdm_courses = tqdm.tqdm(courses, leave=False)
            for course in tqdm_courses:
                try:
                    sleep(0.2)
                    course_id = str(course["subNum"])
                    tqdm_courses.set_postfix_str("Pre-deleting {}".format(course_id))
                    user.delete_track(course_id)
                except Exception as e:
                    logging.error(e)
                    continue

        # Add courses to track list
        tqdm_courses = tqdm.tqdm([*set(courses_list)], leave=False)
        for course_id in tqdm_courses:
            try:
                sleep(0.2)
                tqdm_courses.set_postfix_str("Adding {}".format(course_id))
                user.add_track(course_id)
            except Exception as e:
                logging.error(e)
                continue

        # get track list and parse out teacher id
        courses = user.get_track()
        teacher_id_dict = dict()
        tqdm_courses = tqdm.tqdm(courses, leave=False)
        for course in tqdm_courses:
            try:
                teacher_stat_url = str(course["teaStatUrl"])
                teacher_name = str(course["teaNam"])
                tqdm_courses.set_postfix_str("Processing {}".format(teacher_name))
                if teacher_stat_url.startswith(
                        "https://newdoc.nccu.edu.tw/teaschm/{}/statisticAll.jsp".format(
                            YEAR_SEM
                        )
                ):
                    teacher_id = teacher_stat_url.split(
                        "https://newdoc.nccu.edu.tw/teaschm/{}/statisticAll.jsp-tnum=".format(
                            YEAR_SEM
                        )
                    )[1].split(".htm")[0]
                    teacher_id_dict[teacher_name] = teacher_id
                    db.add_teacher(teacher_id, teacher_name)
                elif teacher_stat_url.startswith(
                        "https://newdoc.nccu.edu.tw/teaschm/{}/set20.jsp".format(YEAR_SEM)
                ):
                    # use ip to avoid name resolve error, and add time out
                    res = requests.get(
                        teacher_stat_url.replace(
                            "newdoc.nccu.edu.tw", "140.119.229.20"
                        ).replace("https://", "http://"),
                        timeout=10,
                    )
                    res.raise_for_status()
                    sleep(0.2)
                    soup = BeautifulSoup(
                        res.content.decode("big5").encode("utf-8"), "html.parser"
                    )
                    rows = soup.find_all("tr")
                    for row in [
                        x.find_all("td")
                        for x in soup.find_all("tr")
                        if x.find_all("td")[1].find("a")
                    ]:
                        teacher_name = str(row[0].text)
                        teacher_id = (
                            row[-1]
                            .find("a")["href"]
                            .split("statisticAll.jsp-tnum=")[1]
                            .split(".htm")[0]
                        )
                        teacher_id_dict[teacher_name] = teacher_id
                        db.add_teacher(teacher_id, teacher_name)
            except Exception as e:
                logging.error(e)
                continue

        # Delete courses from track list
        tqdm_courses = tqdm.tqdm(courses, leave=False)
        for course in tqdm_courses:
            try:
                sleep(0.2)
                course_id = str(course["subNum"])
                tqdm_courses.set_postfix_str("Deleting {}".format(course_id))
                user.delete_track(course_id)
            except Exception as e:
                logging.error(e)
                continue

        print("Fetch TeacherId done at {}".format(datetime.datetime.now()))
    else:
        print("Skipping Fetch TeacherId")

    # ==============================
    # \ 3. Fetch Rates and Details \
    # ==============================

    if args.rate:
        # Read teacher list
        new_teacher_list = db.get_teacher()
        with open(os.path.join(dirPath, "old_data", "1111_teachers.json"), "r") as f:
            old_teacher_list = json.loads(f.read())
        teacher_list = {**new_teacher_list, **old_teacher_list}
        with open(os.path.join(dirPath, "old_data", "1112_teachers.json"), "r") as f:
            old_teacher_list = json.loads(f.read())
        teacherList = {**new_teacher_list, **old_teacher_list}

        # Run through all teacherId, and fetch courses of teachers
        teachers = tqdm.tqdm(teacher_list, total=len(teacher_list), leave=False)
        for teacher in teachers:
            teacher_id = teacher_list[teacher]
            teachers.set_postfix_str("processing: {} {}".format(teacher_id, teacher))
            semesters = tqdm.tqdm(all_semesters, total=len(all_semesters), leave=False)
            for semester in semesters:
                semesters.set_postfix_str("processing: {}".format(semester))
                try:
                    location = "http://newdoc.nccu.edu.tw/teaschm/{}/statistic.jsp-tnum={}.htm".format(
                        semester, teacher_id
                    )
                    res = requests.get(location)
                    res.raise_for_status()
                    soup = BeautifulSoup(
                        res.content.decode("big5").encode("utf-8"), "html.parser"
                    )
                    courses = soup.find("table", {"border": "1"}).find_all("tr")
                    available_courses = [
                        x.find_all("td")
                        for x in courses
                        if x.find_all("td")[-1].find("a")
                           and int(x.find_all("td")[0].text) > 100
                    ]
                    tqdm_courses = tqdm.tqdm(
                        available_courses, total=len(available_courses), leave=False
                    )

                    for row in tqdm_courses:
                        course_id = "{}{}{}".format(
                            row[0].text, row[1].text, row[2].text
                        )
                        tqdm_courses.set_postfix_str("processing: {}".format(course_id))
                        if db.is_rate_exist(course_id):
                            continue
                        sleep(0.2)
                        rates = fetch_rate(
                            "http://newdoc.nccu.edu.tw/teaschm/{}/{}".format(
                                semester, row[-1].find("a")["href"]
                            )
                        )

                        # Write to database
                        tqdm_rates = tqdm.tqdm(rates, total=len(rates), leave=False)
                        for index, rate in enumerate(tqdm_rates):
                            # rateEn = translateRate(str(rate))
                            rateEn = ""
                            db.add_rate(index, course_id, teacher_id, str(rate), rateEn)

                except Exception as e:
                    logging.error(e)
                    continue

        print("Fetch Rates and Details done at {}".format(datetime.datetime.now()))
    else:
        print("Skipping Fetch Rate")

    # ==============================
    # \ 4. Course Result           \
    # ==============================
    if args.result:
        for sem in COURSERESULT_YEARSEM:
            row_count = sum(1 for line in open("./data/" + course_result_csv(sem), "r"))
            with open("./data/" + course_result_csv(sem), "r") as f:
                lines = [line for line in f]
                i = 0
                reader = tqdm.tqdm(csv.reader(lines), total=len(lines))
                for row in reader:
                    courseid = str(row[0])
                    try:
                        sleep(0.2)
                        res = requests.get(
                            "https://es.nccu.edu.tw/course/zh-TW/:sem="
                            + sem
                            + "%20"
                            + str(courseid)
                            + "%20/"
                        ).json()
                        db.add_result(
                            sem,
                            courseid,
                            res[0]["subNam"],
                            res[0]["teaNam"],
                            res[0]["subTime"],
                            int(row[3]),
                            int(row[4]),
                            -1 if row[5] == "" else int(row[5]),
                        )
                    except Exception as err:
                        logging.error(err)
                        continue
                    i += 1
