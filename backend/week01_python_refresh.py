students = [
{"id": "22000001", "name": "Nguyen Minh Anh", "major": "KHDL"},
{"id": "22000002", "name": "Tran Duc Long", "major": "KHDL"},
]
courses = [
{
"code": "INT2204",
"name": "Co so du lieu Web va he thong thong tin",
"capacity": 3,
"enrolled": 2,
},
{
"code": "INT2205",
"name": "Khai pha du lieu",
"capacity": 2,
"enrolled": 2,
},
]

enrollments = [
{"student_id": "22000001", "course_code": "INT2204"}
]

for course in courses:
 remaining = course["capacity"] - course["enrolled"]
 print(course["code"], "- con", remaining, "cho")

def find_course(course_code):
 for course in courses:



  if course["code"] == course_code:
   return course
 return None
print(find_course("INT2204"))

def can_enroll(student_id, course_code):
 course = find_course(course_code)
 
 if course is None:
  return False, "Hoc phan khong ton tai"
 
 if course["enrolled"] >= course["capacity"]:
  return False, "Lop da du so luong"

 duplicated = any(
  item["student_id"] == student_id and item["course_code"] == course_code
  for item in enrollments
)
 if duplicated:
  return False, "Sinh vien da dang ky hoc phan nay"
 return True, "Co the dang ky"
print(can_enroll("22000002", "INT2204"))

def search_courses(keyword):
 normalized = keyword.strip().lower()
 results = []
 
 for course in courses:
  code = course["code"].lower()
  name = course["name"].lower()
  
  if normalized in code or normalized in name:
    results.append(course)
 
 return results

print(search_courses("web"))

def enroll_student(student_id, course_code):
    student_exists = any(
        student["id"] == student_id
        for student in students
    )

    if not student_exists:
        return False, "Student does not exist"

    can_register, message = can_enroll(student_id, course_code)

    if not can_register:
        return False, message

    enrollments.append({
        "student_id": student_id,
        "course_code": course_code
    })

    course = find_course(course_code)
    course["enrolled"] += 1

    return True, "Apply successfully"

print("\n--- KIEM THU 1: Apply successfully ---")
print(enroll_student("22000002", "INT2204"))

print("\n--- KIEM THU 2: Duplicate registration ---")
print(enroll_student("22000001", "INT2204"))

print("\n--- KIEM THU 3: Class is full ---")
print(enroll_student("22000002", "INT2205"))

print("\n--- KIEM THU 4: Course code does not exist ---")
print(enroll_student("22000002", "INT4076"))

print("\n--- KIEM THU 5: Student does not exist ---")
print(enroll_student("24001544", "INT2204"))
