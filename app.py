from flask import Flask, render_template, request
from werkzeug.exceptions import BadRequest
from flask_sqlalchemy import SQLAlchemy
import datetime
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI']=os.environ['DATABASE_URL']
app.debug = True
db = SQLAlchemy(app)

class Employee(db.Model):
    __tablename__='employee'
    employee_id=db.Column(db.String(100), primary_key=True)
    employee_name=db.Column(db.String(100))
    employee_org=db.Column(db.String(200))

class Report(db.Model):
    __tablename__='report'
    start_date=db.Column(db.Date(), primary_key=True)
    employee_id=db.Column(db.String(100), primary_key=True)
    schedule=db.Column(db.String(5000))

@app.route('/')
def index():
    return render_template('index.html')
    
@app.route('/employee')
def employee():
    employees=Employee.query.order_by(Employee.employee_id.asc())
    return render_template('employee.html', employees=employees)

@app.route('/add_employee')
def add_item():
    return render_template("add_employee.html")

@app.route('/post_employee',methods=['POST'])
def post_item():
    try:
        employee = Employee()
        employee.employee_id = request.form['alias']
        employee.employee_name = request.form['name']
        employee.employee_org = request.form['department']
        db.session.add(employee)
        db.session.commit()
        employees=Employee.query.order_by(Employee.employee_id.asc())
        return render_template('employee.html', employees=employees)
    except Exception as ex:
        return ex
   
@app.route('/remove_employee')
def remove_employee():
    employee_id = request.args.get('employee_id')
    Employee.query.filter(Employee.employee_id == employee_id).delete()
    db.session.commit()
    employees=Employee.query.order_by(Employee.employee_id.asc())
    return render_template('employee.html', employees=employees)


if __name__ == '__main__':
    app.run()