from calculate import Calculator
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.exceptions import BadRequest
from sqlalchemy import exc
import json
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DATABASE_URL']
app.debug = True
db = SQLAlchemy(app)

REG_HOUR = 8.00

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


def round_matrix(matrix, digits_count):
    for i in range(len(matrix)):
        for j in range(len(matrix[0])):
            matrix[i][j] = round(matrix[i][j], digits_count)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/process', methods=['POST'])
def process():
    start_date_str = request.form['start_date']
    start_date = datetime.strptime(start_date_str, '%Y/%m/%d')
    f = request.files['file']
    content = f.read().decode('utf8')
    calculator = Calculator(start_date)
    reports = calculator.calc(content)
    for alias, report in reports.items():
        existing_record = Report.query.get((start_date, alias))
        if existing_record:
            existing_record.schedule = json.dumps(report)
        else:
            report_record = Report()
            report_record.employee_id = alias
            report_record.start_date = start_date
            report_record.schedule = json.dumps(report)
            db.session.add(report_record)
    db.session.commit()
    return redirect(url_for('report_list', start_date=start_date))


@app.route('/history')
def history():
    result = db.session.query(Report.start_date).distinct()
    dates = []
    for item in result:
        dates.append(item[0])
    dates.sort(reverse=True)
    return render_template('history.html', dates=dates)


@app.route('/report_list')
def report_list():
    start_date = request.args.get('start_date')
    reports = Report.query.filter(Report.start_date == start_date)
    reports_data = []
    for report in reports:
        reports_data.append(report)
    reports_data.sort(key=lambda x : x.employee_id)
    return render_template('report_list.html', reports=reports_data)


@app.route('/report')
def report():
    start_date_str = request.args.get('start_date')
    alias = request.args.get('alias').strip()
    record = Report.query.get((start_date_str, alias))

    if not record:
        return "No report for " + alias + " on " + start_date_str

    dates = []
    start_date = datetime.strptime(start_date_str.split(' ')[0], '%Y-%m-%d')
    for i in range(14):
        dates.append(start_date + timedelta(i))

    schedule = json.loads(record.schedule)

    stats = []
    for _ in range(14):
        # columns are total, regular, overtime, sick, holiday, vacation
        stats.append([0] * 6)
    for i in range(len(schedule)):
        if len(schedule[i]) < 2:
            continue
        total = 0
        for j in range(1, len(schedule[i]), 2):
            last_time = datetime.strptime(schedule[i][j - 1], '%H:%M:%S')
            cur_time = datetime.strptime(schedule[i][j], '%H:%M:%S')
            total += ((cur_time - last_time).seconds / 3600)
        stats[i][0] = total
        stats[i][1] = min(stats[i][0], REG_HOUR)
        if stats[i][0] > REG_HOUR:
            stats[i][2] = stats[i][0] - REG_HOUR
    
    totals = []
    # totals for two weeks and a sum of both 
    for _ in range(3):
        # columns are regular, overtime, sick, holiday, vacation
        totals.append([0] * 5)

    for i in range(7):
        totals[0][0] += stats[i][1]
        totals[0][1] += stats[i][2]
    for i in range(7, 14):
        totals[1][0] += stats[i][1]
        totals[1][1] += stats[i][2]
    totals[2][0] = totals[0][0] + totals[1][0]
    totals[2][1] = totals[0][1] + totals[1][1]

    # fill in employee information
    employee = Employee.query.get(alias)
    if not employee:
        employee = Employee()
        employee.employee_id = alias
        employee.employee_name = ''
        employee.employee_org = ''

    # formatting
    for row in schedule:
        while len(row) < 4:
            row.append('')
    round_matrix(stats, 2)
    round_matrix(totals, 2)

    return render_template(
        'report.html', dates=dates, schedule=schedule, stats=stats, totals=totals, employee=employee)

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


@app.route('/save', methods=['POST'])
def save():
    alias = request.args.get('alias')
    start_date = request.args.get('start_date')
    record = Report.query.get((start_date, alias))

    schedule = []
    for i in range(14):
        schedule.append([])
        for j in range(4):
            val = request.form['schedule_' + str(i) + '_' + str(j)]
            if not val:
                continue
            try:
                datetime.strptime(val, '%H:%M:%S')
            except:
                return "Time entry on row " + str(i) + " column " + str(j) + " is not in the valid format of %H:%M:%S"
            schedule[i].append(val)
    record.schedule = json.dumps(schedule)
    db.session.commit()

    employee = Employee.query.get(alias)
    if employee:
        employee.employee_name = request.form['employee_name']
        employee.employee_org = request.form['employee_org']
    else:
        new_employee = Employee()
        new_employee.employee_id = alias
        new_employee.employee_name = request.form['employee_name']
        new_employee.employee_org = request.form['employee_org']
        db.session.add(new_employee)
    db.session.commit()
    return redirect(url_for('report', alias=alias, start_date=start_date))


if __name__ == '__main__':
    app.run()
