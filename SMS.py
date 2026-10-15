import csv
import json
from pathlib import Path
import streamlit as st

DATA_FILE = Path(__file__).with_name('students.json')
SUBJECTS = ('Python', 'Database', 'Networking')  # tuple

class Student:
    def __init__(self, student_id, name, age, department, marks):
        self.student_id = student_id
        self.name = name
        self.age = age
        self.department = department
        self.__marks = marks  # encapsulation

    @property
    def marks(self):
        return self.__marks.copy()

    def average(self):
        return sum(self.__marks.values()) / len(self.__marks)

    def grade(self):
        score = self.average()
        if score >= 80:
            return 'A'
        elif score >= 65:
            return 'B'
        elif score >= 50:
            return 'C'
        return 'F'

    def get_details(self):
        return f'{self.name} ({self.student_id}) — Grade {self.grade()}'

    def to_dict(self):
        return {'student_id': self.student_id, 'name': self.name,
                'age': self.age, 'department': self.department,
                'marks': self.marks, 'type': 'Regular'}

class ScholarshipStudent(Student):  # inheritance
    def __init__(self, student_id, name, age, department, marks, scholarship):
        super().__init__(student_id, name, age, department, marks)
        self.scholarship = scholarship

    def get_details(self):  # polymorphism
        return f'{super().get_details()} — Scholarship: {self.scholarship}'

    def to_dict(self):
        result = super().to_dict()
        result.update(type='Scholarship', scholarship=self.scholarship)
        return result

class StudentManager:
    def __init__(self):
        self.students = []  # list

    def add(self, student):
        if any(s.student_id == student.student_id for s in self.students):
            raise ValueError('Student ID already exists.')
        self.students.append(student)

    def save(self):
        DATA_FILE.write_text(json.dumps([s.to_dict() for s in self.students], indent=2), encoding='utf-8')

    def load(self):
        if not DATA_FILE.exists():
            return
        records = json.loads(DATA_FILE.read_text(encoding='utf-8'))
        if not isinstance(records, list):
            raise ValueError('Invalid JSON format.')
        for record in records:
            fields = [record[k] for k in ('student_id', 'name', 'age', 'department', 'marks')]
            if record.get('type') == 'Scholarship':
                self.add(ScholarshipStudent(*fields, record.get('scholarship', 'Merit')))
            else:
                self.add(Student(*fields))

    def rows(self):
        return [{**s.to_dict(), 'average': round(s.average(), 2), 'grade': s.grade()}
                for s in self.students]

    def export_csv(self):
        import io
        buffer = io.StringIO()
        writer = csv.DictWriter(buffer, fieldnames=['ID', 'Name', 'Age', 'Department', *SUBJECTS, 'Average', 'Grade'])
        writer.writeheader()
        for s in self.students:
            writer.writerow({'ID': s.student_id, 'Name': s.name, 'Age': s.age,
                             'Department': s.department, **s.marks,
                             'Average': round(s.average(), 2), 'Grade': s.grade()})
        return buffer.getvalue()

def factorial(n):  # recursion
    if n < 0:
        raise ValueError('Enter a non-negative integer.')
    return 1 if n <= 1 else n * factorial(n - 1)

@st.cache_resource
def get_manager():
    manager = StudentManager()
    try:
        manager.load()
    except (OSError, ValueError, KeyError, TypeError) as exc:
        st.error(f'Unable to load saved data: {exc}')
    return manager

st.set_page_config(page_title='Python Concepts Lab', page_icon='🎓', layout='wide')
st.title('🎓 Student Management System')
st.caption('Python basics • OOP • Functional programming • Data structures • File handling')
manager = get_manager()
page = st.sidebar.radio('Navigate', ['Add Student', 'View Students', 'Search & Filter', 'Statistics', 'Functional Programming Demo'])

if page == 'Add Student':
    st.header('Add a student')
    with st.form('student_form', clear_on_submit=True):
        student_id = st.text_input('Student ID')
        name = st.text_input('Student name')
        age = st.number_input('Age', min_value=5, max_value=100, value=20)
        department = st.selectbox('Department', ['Computer Science', 'IT', 'Engineering', 'Business'])
        marks = {subject: st.number_input(f'{subject} marks', 0, 100, 50) for subject in SUBJECTS}
        is_scholarship = st.checkbox('Scholarship student')
        scholarship = st.text_input('Scholarship name', value='Merit') if is_scholarship else ''
        submitted = st.form_submit_button('Add and save')
    if submitted:
        try:
            if not student_id.strip() or not name.strip():
                raise ValueError('Student ID and name are required.')
            args = (student_id.strip(), name.strip(), int(age), department, marks)
            student = ScholarshipStudent(*args, scholarship) if is_scholarship else Student(*args)
            manager.add(student)
            manager.save()
            st.success(student.get_details())
        except (ValueError, OSError) as exc:
            st.error(str(exc))

elif page == 'View Students':
    st.header('Student records')
    if manager.students:
        st.dataframe(manager.rows(), use_container_width=True)
        st.download_button('Download CSV', manager.export_csv(), 'students.csv', 'text/csv')
        st.download_button('Download JSON', json.dumps([s.to_dict() for s in manager.students], indent=2), 'students.json', 'application/json')
    else:
        st.info('No records yet. Add a student first.')

elif page == 'Search & Filter':
    st.header('Search, sort and filter')
    query = st.text_input('Search by name or student ID').lower()
    minimum = st.slider('Minimum average mark', 0, 100, 0)
    records = list(filter(lambda s: (query in s.name.lower() or query in s.student_id.lower()) and s.average() >= minimum, manager.students))
    descending = st.checkbox('Highest marks first', value=True)
    records = sorted(records, key=lambda s: s.average(), reverse=descending)  # lambda
    st.dataframe([{'ID': s.student_id, 'Name': s.name, 'Average': round(s.average(), 2), 'Grade': s.grade()} for s in records], use_container_width=True)

elif page == 'Statistics':
    st.header('Class statistics')
    if manager.students:
        averages = list(map(lambda s: s.average(), manager.students))  # map
        passed = list(filter(lambda s: s.average() >= 50, manager.students))  # filter
        grades = {grade: sum(s.grade() == grade for s in manager.students) for grade in ('A', 'B', 'C', 'F')}  # dictionary
        departments = {s.department for s in manager.students}  # set
        a, b, c = st.columns(3)
        a.metric('Students', len(manager.students))
        b.metric('Class average', f'{sum(averages) / len(averages):.1f}%')
        c.metric('Passed', len(passed))
        st.subheader('Grade distribution')
        st.bar_chart(grades)
        st.write('Unique departments (set):', ', '.join(sorted(departments)))
    else:
        st.info('Add student records to view statistics.')

else:
    st.header('Functional programming demonstration')
    n = st.number_input('Enter a number for factorial (recursion)', 0, 15, 5)
    st.code('def factorial(n):\n    return 1 if n <= 1 else n * factorial(n - 1)', language='python')
    st.write(f'{n}! = {factorial(n)}')
    numbers = [12, 45, 67, 80, 92]  # list
    st.write('Original list:', numbers)
    st.write('map (double each number):', list(map(lambda x: x * 2, numbers)))
    st.write('filter (numbers >= 50):', list(filter(lambda x: x >= 50, numbers)))
    st.write('sorted + lambda (descending):', sorted(numbers, key=lambda x: x, reverse=True))
    st.write('Tuple of subjects:', SUBJECTS)
    st.write('Dictionary of subject example marks:', dict(zip(SUBJECTS, [75, 85, 90])))
