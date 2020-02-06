from calculate import Calculator
from datetime import datetime
from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy
from werkzeug.exceptions import BadRequest
from sqlalchemy import exc
import datetime
import json
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI']=os.environ['DATABASE_URL']
db = SQLAlchemy(app)


class Employee(db.Model):
    __tablename__ = 'employee'
    employee_id = db.Column(db.String(100), primary_key=True)
    employee_name = db.Column(db.String(100))
    employee_org = db.Column(db.String(200))


class Report(db.Model):
    __tablename__ = 'report'
    start_date = db.Column(db.TIMESTAMP, primary_key=True)
    employee_id = db.Column(db.String(100), primary_key=True)
    schedule = db.Column(db.String(5000))


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/process', methods=['POST'])
def process():
    start_date_str = request.form['start_date']
    start_date = date_elem = datetime.strptime(start_date_str, '%Y/%m/%d')
    f = request.files['file']
    content = f.read()
    calculator = Calculator(start_date)
    reports = calculator.calc(content)
    for alias, report in reports:
        existing_record = Report.query.get(start_date=start_date, employee_id=alias)
        if existing_record:
            existing_record.schedule = json.dumps(report.__dict__)
        else:
            report_record = Report()
            report_record.employee_id = alias
            report_record.start_date = start_date
            report_record.schedule = json.dumps(report.__dict__)
            db.session.add(report_record)
    db.session.commit()

    # TODO: return the date page
    return "processed"


@app.route('/employee')
def employee():
    employees = Employee.query.order_by(Employee.employee_id.asc())
    return render_template('employee.html', employees=employees)


@app.route('/add_employee')
def add_employee():
    return render_template("add_employee.html")


@app.route('/post_employee', methods=['POST'])
def post_employee():
    try:
        employee = Employee()
        employee.employee_id = request.form['alias']
        employee.employee_name = request.form['name']
        employee.employee_org = request.form['department']
        db.session.add(employee)
        db.session.commit()
        employees = Employee.query.order_by(Employee.employee_id.asc())
        return render_template('employee.html', employees=employees)
    except exc.IntegrityError as ex:
        return 'Error: The employee alias ' + \
            request.form['alias'] + \
            ' already exists. Multiple employees with the same alias is not allowed.'


@app.route('/remove_employee')
def remove_employee():
    employee_id = request.args.get('employee_id')
    Employee.query.filter(Employee.employee_id == employee_id).delete()
    db.session.commit()
    employees = Employee.query.order_by(Employee.employee_id.asc())
    return render_template('employee.html', employees=employees)


if __name__ == '__main__':
    app.run()
