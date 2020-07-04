from flask import Flask, render_template, request, redirect, url_for, jsonify, flash, session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from datetime import datetime
import json
import math, random 
from pymsgbox import *
import easygui
from flask_mail import Mail, Message
import os
import string 
import random
from markupsafe import escape

app = Flask(__name__)

# CONFIGURATIONS FOR FLASK-MAIL-DO NOT MODIFY!!

app.config.update(dict(
    DEBUG = True,
    MAIL_SERVER = 'smtp.gmail.com',
    MAIL_PORT = 587,
    MAIL_USE_TLS = True,
    MAIL_USE_SSL = False,
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME'),
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD'),
))


mail = Mail(app)
app.secret_key = "super secret key"
DATABASE_URL="postgres://wainhlvxrgqwoo:9902be4ffc31450a1e9924f03879d1788cfb7fa659ae511f16223d4ef9c351c8@ec2-3-223-21-106.compute-1.amazonaws.com:5432/d5nru0s34hfo11"

# DATABASE_URL = os.getenv("DATABASE_URL")

# Check for environment variable
# if not os.getenv("DATABASE_URL"):
#     raise RuntimeError("DATABASE_URL is not set")


# Set up database
engine = create_engine(DATABASE_URL)
db = scoped_session(sessionmaker(bind=engine))
 

# brand = {
# 	'0'  : 'Select Brand',
# 	'1'  : 'Brand A',
# 	'2'  : 'Barnd B',
# 	'3'  : 'Brand C',
# 	'4'  : 'Brand D',
# 	'5'  : 'Barnd E',
# 	'6'  : 'Brand F',
# 	'7'  : 'Brand G',
# 	'8'  : 'Barnd H',
# 	'9'  : 'Brand I',
	
# }

category_items = {}

@app.route("/addproduct", methods = ["GET"])
def addproduct():

	if 'SuperUser_ID' in session:

		result = db.execute("SELECT * FROM category").fetchall()
		for r in result:
			category_code = r.category_code
			category_name = r.category_name
			category_items[str(category_code)] = category_name

		# FUNCTION CALL TO FIND NUMBER OF LOW AND CRITICAL ITEMS IN THE STORE
		low_items_count, critical_items_count = findItemsCount()

		return render_template('addproduct.html', category_items = category_items, low_items_count = low_items_count, critical_items_count = critical_items_count)

	else:
		return redirect(url_for('index'))	


@app.route("/addnewproduct",methods=["POST"])
def addnewproduct():

	if 'SuperUser_ID' in session:
	
		product_code = request.form.get('product_items_id')
		product_name = category_items[product_code]
		qty_available = request.form.get('Quantity')

		product_exists = db.execute("SELECT * FROM products WHERE product_code=:product_code ",
		{'product_code':product_code}).fetchall()

		if (product_exists):
			for r in product_exists:
				previous_qty = r.qty_available
				updated_qty = previous_qty + int(qty_available)

			db.execute("UPDATE products SET qty_available=:qty_available WHERE product_code=:product_code",
			{"product_code":product_code, "qty_available":updated_qty})
			db.commit()
			db.close()
			alert_type = 'success'
			flash( f"{ product_name } quantity has been successfully Updated. Now the available quantity is { updated_qty } units.")

			# FUNCTION CALL TO FIND NUMBER OF LOW AND CRITICAL ITEMS IN THE STORE
			low_items_count, critical_items_count = findItemsCount()

			return render_template('addproduct.html', alert_type = alert_type, category_items = category_items, low_items_count = low_items_count, critical_items_count = critical_items_count)


		elif (product_exists == []):
			result = db.execute("SELECT * FROM category WHERE category_code=:category_code ",
			{'category_code':product_code}).fetchall()

			for r in result:
				product_type = r.category_type,
				lowlevel_qty = r.lowlevel_qty,
				critical_level_qty = r.critical_level_qty
			
			db.execute("INSERT INTO products(product_name, product_code, qty_available, product_type, lowlevel_qty, critical_level_qty) VALUES(:product_name, :product_code, :qty_available, :product_type, :lowlevel_qty, :critical_level_qty)",
			{"product_name":product_name,"product_code":product_code,"qty_available":qty_available,"product_type":product_type, "lowlevel_qty":lowlevel_qty,"critical_level_qty":critical_level_qty})
			db.commit()
			db.close()
			alert_type = 'success'
			flash( f"{ product_name } has been successfully added with { qty_available } units.")

			# FUNCTION CALL TO FIND NUMBER OF LOW AND CRITICAL ITEMS IN THE STORE
			low_items_count, critical_items_count = findItemsCount()

			return render_template('addproduct.html', alert_type = alert_type, category_items = category_items, low_items_count = low_items_count, critical_items_count = critical_items_count)

		else:
			alert_type = 'error'
			flash (f"Oops, Something went wrong!")	

			# FUNCTION CALL TO FIND NUMBER OF LOW AND CRITICAL ITEMS IN THE STORE
			low_items_count, critical_items_count = findItemsCount()

			return render_template('addproduct.html', alert_type = alert_type, category_items = category_items, low_items_count = low_items_count, critical_items_count = critical_items_count)		


	else:
		return redirect(url_for('index'))
			


@app.route("/")
@app.route("/index")
def index():
	
	if 'User_ID' in session:  # IF USER IS ALREADY LOGGED IN THEN HE WILL NOT BE ABLE TO OPEN THE "index" PAGE

		person_phone_or_email = session['User_ID'] 

		result = db.execute("SELECT * FROM registrations WHERE phone=:person_phone_or_email OR email=:person_phone_or_email",
		{"person_phone_or_email":person_phone_or_email}).fetchall()
		for r in result:
			# registration_status = r.reg_status
			# phone = r.phone
			# email = r.email
			# password = r.password
			first_name = r.first_name
			last_name = r.last_name
			department = r.department
			registered_as = r.designation

		all_products = db.execute("SELECT * FROM products").fetchall()

		alert_type = 'info'
		flash (f" Hey { first_name }, You are already logged in!") 

		return render_template('allproductsuser.html', all_products = all_products, alert_type = alert_type, 
		first_name = first_name, last_name = last_name, department = department, registered_as = registered_as)


	elif 'SuperUser_ID' in session:  # IF SUPERUSER IS ALREADY LOGGED IN THEN HE WILL NOT BE ABLE TO OPEN THE "index" PAGE

		person_phone_or_email = session['SuperUser_ID'] 

		result = db.execute("SELECT * FROM superuser WHERE phone=:person_phone_or_email OR email=:person_phone_or_email",
		{"person_phone_or_email":person_phone_or_email}).fetchall()
		for r in result:
			first_name = r.first_name
			last_name = r.last_name
			designation = r.designation

		alert_type = 'info'

		flash (f" Hey { first_name }, You arecdbcdb already logged in FROM INDEX!") 

		if designation == 'Head':

			all_products = db.execute("SELECT * FROM products").fetchall()

			# FUNCTION CALL TO FIND NUMBER OF LOW AND CRITICAL ITEMS IN THE STORE
			low_items_count, critical_items_count = findItemsCount()	

			return render_template('allproductshead.html', all_products = all_products, alert_type = alert_type, low_items_count = low_items_count, critical_items_count = critical_items_count)


		elif designation == 'Store Manager':

			all_products = db.execute("SELECT * FROM products").fetchall()

			# FUNCTION CALL TO FIND NUMBER OF LOW AND CRITICAL ITEMS IN THE STORE
			low_items_count, critical_items_count = findItemsCount()

			return render_template('allproductsstoremanager.html', all_products = all_products, alert_type = alert_type , low_items_count = low_items_count, critical_items_count = critical_items_count)


		elif designation == 'Admin':

			all_registrations = db.execute("SELECT * FROM registrations").fetchall()

			# FUNCTION CALL TO FIND NUMBER OF LOW AND CRITICAL ITEMS IN THE STORE
			# low_items_count, critical_items_count = findItemsCount()

			# ADMIN WILL NOT SEE THE LIST OF PRODUCTS , IT WILL LAND ON THE allregistrations PAGE 
			# WHERE HE WILL BE ABLE TO APPROVE OR REJECT REGISTRATIONS

			return render_template('allregistrations.html', all_registrations = all_registrations, alert_type = alert_type)


	else:	# RUNS WHEN USER IS LOGGED OUT ,  # RUNS WHEN SUPERUSER IS LOGGED OUT
		return render_template('index.html')

@app.route("/signup",methods=['POST', 'GET'])
def signup():

	department = {
	'0' : 'B.Tech(IT)',
	'1' : 'B.Tech(CSE)',
	'2' : 'B.Tech(Mechanical)',
	'3' : 'B.Tech(ECE)',
	'4' : 'B.Tech(IN)',
	'5' : 'B.Sc(Chemistry)',
	'6' : 'B.Sc(Physics)',
	'7' : 'B.Sc(Microbiology)',
	'8' : 'M.Sc(Chemistry)',
	'9' : 'M.Sc(Physics)',
	'10' : 'M.Sc(Microbiology)',
	'11' : 'B.J.M.C.'
	
	}


	if 'SuperUser_ID' in session:  # MEANS SUPERUSER IS ALREADY LOGGED IN THEN HE WILL BE REDIRECTED TO HIS HOME PAGE

		person_phone_or_email = session['SuperUser_ID'] 

		result = db.execute("SELECT * FROM superuser WHERE phone=:person_phone_or_email OR email=:person_phone_or_email",
		{"person_phone_or_email":person_phone_or_email}).fetchall()
		for r in result:
			first_name = r.first_name
			last_name = r.last_name
			designation = r.designation

		alert_type = 'info'

		flash (f" Hey { first_name }, You are already logged in as { designation } FROM SIGNUP!") 

		if designation == 'Head':

			all_products = db.execute("SELECT * FROM products").fetchall()

			# FUNCTION CALL TO FIND NUMBER OF LOW AND CRITICAL ITEMS IN THE STORE
			low_items_count, critical_items_count = findItemsCount()	

			return render_template('allproductshead.html', all_products = all_products, alert_type = alert_type, low_items_count = low_items_count, critical_items_count = critical_items_count)


		elif designation == 'Store Manager':

			all_products = db.execute("SELECT * FROM products").fetchall()

			# FUNCTION CALL TO FIND NUMBER OF LOW AND CRITICAL ITEMS IN THE STORE
			low_items_count, critical_items_count = findItemsCount()

			return render_template('allproductsstoremanager.html', all_products = all_products, alert_type = alert_type , low_items_count = low_items_count, critical_items_count = critical_items_count)


		elif designation == 'Admin':

			all_registrations = db.execute("SELECT * FROM registrations").fetchall()

			# FUNCTION CALL TO FIND NUMBER OF LOW AND CRITICAL ITEMS IN THE STORE
			# low_items_count, critical_items_count = findItemsCount()

			# ADMIN WILL NOT SEE THE LIST OF PRODUCTS , IT WILL LAND ON THE allregistrations PAGE 
			# WHERE HE WILL BE ABLE TO APPROVE OR REJECT REGISTRATIONS

			return render_template('allregistrations.html', all_registrations = all_registrations, alert_type = alert_type)


	elif not 'User_ID' in session:
		
		return render_template('signup.html', department = department)   # WILL ALSO WORK FOR SUPERUSER			


	else: # IF USER IS ALREADY LOGGED IN THEN HE WILL NOT BE ABLE TO OPEN THE "signup" PAGE

		person_phone_or_email = session['User_ID'] 

		result = db.execute("SELECT * FROM registrations WHERE phone=:person_phone_or_email OR email=:person_phone_or_email",
		{"person_phone_or_email":person_phone_or_email}).fetchall()
		for r in result:
			# registration_status = r.reg_status
			# phone = r.phone
			# email = r.email
			# password = r.password
			first_name = r.first_name
			last_name = r.last_name
			department = r.department
			registered_as = r.designation

		all_products = db.execute("SELECT * FROM products").fetchall()

		alert_type = 'info'
		flash (f" Hey { first_name }, You are already logged in!") 

		return render_template('allproductsuser.html', all_products = all_products, alert_type = alert_type, 
		first_name = first_name, last_name = last_name, department = department, registered_as = registered_as)

	

@app.route("/newregistration",methods=["POST", "GET"])
def newregistration():

	if 'SuperUser_ID' in session:  # MEANS SUPERUSER IS ALREADY LOGGED IN

		person_phone_or_email = session['SuperUser_ID'] 

		result = db.execute("SELECT * FROM superuser WHERE phone=:person_phone_or_email OR email=:person_phone_or_email",
		{"person_phone_or_email":person_phone_or_email}).fetchall()
		for r in result:
			first_name = r.first_name
			last_name = r.last_name
			designation = r.designation

		alert_type = 'info'

		flash (f" Hey { first_name }, You are already logged in as { designation } FROM NEW REGISTRATION!") 

		if designation == 'Head':

			all_products = db.execute("SELECT * FROM products").fetchall()

			# FUNCTION CALL TO FIND NUMBER OF LOW AND CRITICAL ITEMS IN THE STORE
			low_items_count, critical_items_count = findItemsCount()	

			return render_template('allproductshead.html', all_products = all_products, alert_type = alert_type, low_items_count = low_items_count, critical_items_count = critical_items_count)


		elif designation == 'Store Manager':

			all_products = db.execute("SELECT * FROM products").fetchall()

			# FUNCTION CALL TO FIND NUMBER OF LOW AND CRITICAL ITEMS IN THE STORE
			low_items_count, critical_items_count = findItemsCount()

			return render_template('allproductsstoremanager.html', all_products = all_products, alert_type = alert_type , low_items_count = low_items_count, critical_items_count = critical_items_count)


		elif designation == 'Admin':

			all_registrations = db.execute("SELECT * FROM registrations").fetchall()

			# FUNCTION CALL TO FIND NUMBER OF LOW AND CRITICAL ITEMS IN THE STORE
			# low_items_count, critical_items_count = findItemsCount()

			# ADMIN WILL NOT SEE THE LIST OF PRODUCTS , IT WILL LAND ON THE allregistrations PAGE 
			# WHERE HE WILL BE ABLE TO APPROVE OR REJECT REGISTRATIONS

			return render_template('allregistrations.html', all_registrations = all_registrations, alert_type = alert_type)


	elif not 'User_ID' in session:  # MEANS USER IS NOT LOGGED IN

		if request.method == 'POST': 
	
			first_name = request.form.get('FirstName')
			last_name = request.form.get('LastName')
			department_id = request.form.get('department_id')
			department_name = department[department_id]
			email = request.form.get('Email')
			phone = request.form.get('Phone')
			password = request.form.get('Password')
			cpassword = request.form.get('CPassword')
			designation = request.form.get('Designation')

			now = datetime.now()
			registration_date = now.strftime("%d-%m-%Y")
			reg_time = now.strftime("%H:%M:%S")

			result = db.execute("SELECT * FROM registrations WHERE phone=:phone OR email=:email",
			{"phone":phone, "email":email}).fetchall() 

			if (result):
				for r in result:
					first_name = r.first_name
					last_name = r.last_name
					alert_type = 'warning'
					flash (f"Sorry, User { first_name } {last_name } already has a registration with these Credentials")
					return render_template('signup.html', alert_type = alert_type, department = department)

			elif (result == []):
				if( password == cpassword ):
					print(result)
					db.execute("INSERT INTO registrations(first_name, last_name, department, email, phone, password, registered_on, designation) VALUES(:first_name, :last_name, :department_name, :email, :phone, :password, :registered_on, :designation)",
					{"first_name":first_name,"last_name":last_name,"department_name":department_name,"email":email, "phone":phone,"password":password, "registered_on":registration_date, "designation":designation})
					db.commit()
					db.close()
					alert_type = 'success'
					flash( f"Your registration request has been successfully submitted")
					return render_template('signup.html', alert_type = alert_type, department = department)

				elif password != cpassword:
					alert_type = 'warning'
					flash( f"Please Confirn Your Pasword Properly!")
					return render_template('signup.html', alert_type = alert_type, department = department)
						
			else:
				alert_type = 'error'
				flash (f"Oops, Something went wrong!")	
				return render_template('signup.html', alert_type = alert_type, department = department)	

		else:  # IF A USER RUNS "newregistration" PATH THROUGH URL i.e. WITHOUT FILLING THE SIGNUP FORM
			return redirect(url_for('index'))	# WILL ALSO WORK FOR SUPERUSER					
			

	else:	# MEANS USER IS ALREADY LOGGED IN

		person_phone_or_email = session['User_ID'] 

		result = db.execute("SELECT * FROM registrations WHERE phone=:person_phone_or_email OR email=:person_phone_or_email",
		{"person_phone_or_email":person_phone_or_email}).fetchall()
		for r in result:
			# registration_status = r.reg_status
			# phone = r.phone
			# email = r.email
			# password = r.password
			first_name = r.first_name
			last_name = r.last_name
			department = r.department
			registered_as = r.designation

		all_products = db.execute("SELECT * FROM products").fetchall()

		alert_type = 'info'
		flash (f" Hey { first_name }, You are already logged in!") 

		return render_template('allproductsuser.html', all_products = all_products, alert_type = alert_type, 
		first_name = first_name, last_name = last_name, department = department, registered_as = registered_as)			


@app.route("/allregistrations")
def allregistrations():

	if 'SuperUser_ID' in session:

		all_registrations = db.execute("SELECT * FROM registrations").fetchall()
		return render_template('allregistrations.html', all_registrations = all_registrations)

	else:
		return redirect(url_for('index'))	


@app.route("/acceptregistration/<person_phone_no>",methods=["GET", "POST"])
def acceptregistration(person_phone_no):

	if 'SuperUser_ID' in session:

		now = datetime.now()
		confirmation_date = now.strftime("%d-%m-%Y")
		confirmation_time = now.strftime("%H:%M:%S")

		new_status = 'Approved'
		
		db.execute("UPDATE registrations SET reason = NULL, reg_status=:new_status, confirmed_on=:confirmed_on WHERE phone=:phone",
		{"new_status":new_status, "confirmed_on":confirmation_date, "phone":person_phone_no})
		db.commit()
		db.close()
		return redirect(url_for('allregistrations'))

	else:
		return redirect(url_for('index'))	


@app.route("/rejectregistration",methods=["POST", "GET"])
def rejectregistration():

	if 'SuperUser_ID' in session:

		now = datetime.now()
		confirmation_date = now.strftime("%d-%m-%Y")
		confirmation_time = now.strftime("%H:%M:%S")

		person_phone_no = request.args.get('Person_phone_no')
		rejection_reason = request.args.get('Reason')

		new_status = 'Not-Approved'

		db.execute("UPDATE registrations SET reg_status=:new_status, reason=:reason, confirmed_on=:confirmed_on WHERE phone=:person_phone_no",
		{"new_status":new_status, "reason":rejection_reason, "confirmed_on":confirmation_date, "person_phone_no":person_phone_no})
		db.commit()
		db.close()

		return redirect(url_for('allregistrations'))

	else:
		return redirect(url_for('index'))	


@app.route("/login", methods=['POST', 'GET'])
def login():

	if 'User_ID' in session:

		person_phone_or_email = session['User_ID'] 

		result = db.execute("SELECT * FROM registrations WHERE phone=:person_phone_or_email OR email=:person_phone_or_email",
		{"person_phone_or_email":person_phone_or_email}).fetchall()
		for r in result:
			# registration_status = r.reg_status
			# phone = r.phone
			# email = r.email
			# password = r.password
			first_name = r.first_name
			last_name = r.last_name
			department = r.department
			registered_as = r.designation

		all_products = db.execute("SELECT * FROM products").fetchall()

		alert_type = 'info'
		flash (f" Hey { first_name }, You are already logged in!") 

		return render_template('allproductsuser.html', all_products = all_products, alert_type = alert_type, 
		first_name = first_name, last_name = last_name, department = department, registered_as = registered_as)


	elif 'SuperUser_ID' in session:  # MEANS SUPERUSER IS ALREADY LOGGED IN

		person_phone_or_email = session['SuperUser_ID'] 

		result = db.execute("SELECT * FROM superuser WHERE phone=:person_phone_or_email OR email=:person_phone_or_email",
		{"person_phone_or_email":person_phone_or_email}).fetchall()
		for r in result:
			first_name = r.first_name
			last_name = r.last_name
			designation = r.designation

		alert_type = 'info'

		flash (f" Hey { first_name }, You are already logged in FROM LOGIN!") 

		if designation == 'Head':

			all_products = db.execute("SELECT * FROM products").fetchall()

			# FUNCTION CALL TO FIND NUMBER OF LOW AND CRITICAL ITEMS IN THE STORE
			low_items_count, critical_items_count = findItemsCount()	

			return render_template('allproductshead.html', all_products = all_products, alert_type = alert_type, low_items_count = low_items_count, critical_items_count = critical_items_count)


		elif designation == 'Store Manager':

			all_products = db.execute("SELECT * FROM products").fetchall()

			# FUNCTION CALL TO FIND NUMBER OF LOW AND CRITICAL ITEMS IN THE STORE
			low_items_count, critical_items_count = findItemsCount()

			return render_template('allproductsstoremanager.html', all_products = all_products, alert_type = alert_type , low_items_count = low_items_count, critical_items_count = critical_items_count)


		elif designation == 'Admin':

			all_registrations = db.execute("SELECT * FROM registrations").fetchall()

			# FUNCTION CALL TO FIND NUMBER OF LOW AND CRITICAL ITEMS IN THE STORE
			# low_items_count, critical_items_count = findItemsCount()

			# ADMIN WILL NOT SEE THE LIST OF PRODUCTS , IT WILL LAND ON THE allregistrations PAGE 
			# WHERE HE WILL BE ABLE TO APPROVE OR REJECT REGISTRATIONS

			return render_template('allregistrations.html', all_registrations = all_registrations, alert_type = alert_type)		


	else:
		return render_template('login.html')

	 

@app.route("/newlogin", methods=['POST', 'GET'])
def newlogin():


	if 'SuperUser_ID' in session:  # MEANS WHEN A SUPERUSER IS LOGGED IN AND TRIES TO RUN THIS PATH THROUGH URL
		
		person_phone_or_email = session['SuperUser_ID'] 

		result = db.execute("SELECT * FROM superuser WHERE phone=:person_phone_or_email OR email=:person_phone_or_email",
		{"person_phone_or_email":person_phone_or_email}).fetchall()
		for r in result:
			first_name = r.first_name
			last_name = r.last_name
			designation = r.designation

		alert_type = 'info'

		flash (f" Hey { first_name }, You are already logged in as { designation } FROM NEW LOGIN!") 

		if designation == 'Head':

			all_products = db.execute("SELECT * FROM products").fetchall()

			# FUNCTION CALL TO FIND NUMBER OF LOW AND CRITICAL ITEMS IN THE STORE
			low_items_count, critical_items_count = findItemsCount()	

			return render_template('allproductshead.html', all_products = all_products, alert_type = alert_type, low_items_count = low_items_count, critical_items_count = critical_items_count)


		elif designation == 'Store Manager':

			all_products = db.execute("SELECT * FROM products").fetchall()

			# FUNCTION CALL TO FIND NUMBER OF LOW AND CRITICAL ITEMS IN THE STORE
			low_items_count, critical_items_count = findItemsCount()

			return render_template('allproductsstoremanager.html', all_products = all_products, alert_type = alert_type , low_items_count = low_items_count, critical_items_count = critical_items_count)


		elif designation == 'Admin':

			all_registrations = db.execute("SELECT * FROM registrations").fetchall()

			# FUNCTION CALL TO FIND NUMBER OF LOW AND CRITICAL ITEMS IN THE STORE
			# low_items_count, critical_items_count = findItemsCount()

			# ADMIN WILL NOT SEE THE LIST OF PRODUCTS , IT WILL LAND ON THE allregistrations PAGE 
			# WHERE HE WILL BE ABLE TO APPROVE OR REJECT REGISTRATIONS

			return render_template('allregistrations.html', all_registrations = all_registrations, alert_type = alert_type)


	elif not 'User_ID' in session:  # MEANS USER IN NOT LOGGED IN

		if request.method == 'POST':

			# person_phone_or_email = request.form.get('EPhone')
			person_phone_or_email = request.form['EPhone']
			person_password = request.form.get('Password')

			login_as = request.form.get('Designation')
			print("!!!!!CHECKING STARTS HERE-PRINTING UDER ID!!!!!!")
			print(person_phone_or_email)
			print('NOW DATABASE QUERY WILL RUN')
			result = db.execute("SELECT * FROM registrations WHERE phone=:person_phone_or_email OR email=:person_phone_or_email",
			{"person_phone_or_email":person_phone_or_email}).fetchall()
			print("PRINTING RESULT AFTER DATABASE QUERY")
			print(result)
			for r in result:
				registration_status = r.reg_status
				phone = r.phone
				email = r.email
				password = r.password
				first_name = r.first_name
				last_name = r.last_name
				department = r.department
				registered_as = r.designation

			if login_as == registered_as:
				if registration_status == 'Pending':
					alert_type = 'info'
					flash (f"Sorry { first_name }, You can not login because your registration request has not yet been Approved!")
					return render_template('login.html', alert_type = alert_type)

				elif registration_status == 'Not-Approved':
					alert_type = 'warning'
					flash (f"Sorry { first_name }, You can not login because your registration request has been Rejected!")
					return render_template('login.html', alert_type = alert_type)

				elif registration_status == 'Approved':
					print('INSIDE CONDITION APPROVED')
					if request.method == 'POST':
						print('CHECKED METHOD = POST')
						if ((person_phone_or_email == phone or person_phone_or_email == email) and person_password == password):
							print('USER VERIFIED')
							# User_ID = request.form['EPhone']
							User_ID = person_phone_or_email
							session['User_ID'] = User_ID	 # CREATING A SESSION OBJECT FOR GENERAL USER

							print("PRINTING SESSION VARIABLE")
							print(User_ID)
							print('PRINTING COMPLETE')

							alert_type = 'success'
							flash (f"Login Successfull! Welcome { first_name }") 
							# return render_template('login.html', alert_type = alert_type)
							all_products = db.execute("SELECT * FROM products").fetchall()
							return render_template('allproductsuser.html', all_products = all_products, alert_type = alert_type, 
							first_name = first_name, last_name = last_name, department = department, registered_as = registered_as)
						
						else:	
							alert_type = 'error'
							flash (f"Oops, User Id and Password do not match!")	
							return render_template('login.html', alert_type = alert_type)	

					else:
						if 'User_ID' in session:

							alert_type = 'info'
							flash (f" Hey { first_name }, You are alreadyyyyyyy logged in!") 

							all_products = db.execute("SELECT * FROM products").fetchall()
							return render_template('allproductsuser.html', all_products = all_products, alert_type = alert_type, 
							first_name = first_name, last_name = last_name, department = department, registered_as = registered_as)
						
						else:
							return render_template('index.html')		

			elif login_as != registered_as:
				alert_type = 'error'
				flash (f"Sorry { first_name }, you can not login as { login_as } because you are registered as { registered_as }.")
				return render_template('login.html', alert_type = alert_type)		

			else:	
				alert_type = 'error'
				flash (f"Oops, Something went wrong!")	
				return render_template('login.html', alert_type = alert_type)


		else:  # IF A USER RUNS "newlogin" PATH THROUGH URL i.e. WITHOUT FILLING THE LOGIN FORM
			return redirect(url_for('index'))	# WILL ALSO WORK FOR SUPERUSER


	# elif not 'SuperUser_ID' in session:  # MEANS WHEN A SUPERUSER IS LOGGED OUT AND TRIES TO RUN THIS PATH THROUGH URL
	# 	return redirect(url_for('index'))


	else:	# MEANS USER IS ALREADY LOGGED IN

		person_phone_or_email = session['User_ID'] 

		result = db.execute("SELECT * FROM registrations WHERE phone=:person_phone_or_email OR email=:person_phone_or_email",
		{"person_phone_or_email":person_phone_or_email}).fetchall()
		for r in result:
			# registration_status = r.reg_status
			# phone = r.phone
			# email = r.email
			# password = r.password
			first_name = r.first_name
			last_name = r.last_name
			department = r.department
			registered_as = r.designation

		all_products = db.execute("SELECT * FROM products").fetchall()

		alert_type = 'info'
		flash (f" Hey { first_name }, You are already logged in!") 

		return render_template('allproductsuser.html', all_products = all_products, alert_type = alert_type, 
		first_name = first_name, last_name = last_name, department = department, registered_as = registered_as)		


# THE FOLLOWING PATH WILL RUN WHEN GENERAL USERS i.e. Clerk, Faculty etc WILL LOG OUT

@app.route('/logoutgeneraluser')
def logoutgeneraluser():
	session.pop('User_ID', None)
	return redirect(url_for('index')) 

# THE FOLLOWING PATH WILL RUN WHEN SUPER USERS i.e. Clerk, Faculty etc WILL LOG OUT

@app.route('/logoutsuperuser')
def logoutsuperuser():
	session.pop('SuperUser_ID', None)
	return redirect(url_for('index'))	

# THIS IS THE  DEFAULT PATH TO allproductsuser.html

@app.route("/homeredirect",methods=['POST', 'GET'])  # unlike paths of other links DEFAULT PATH TO allproductsuser.html is /homeredirect instead of 
def homeredirect():							  # /allproductsuser. And because we just can not allow all products to be seen by just anyone,
											  # therefore we require all this info such as email, first_name, last_name for allproductsuser.html

	if 'User_ID' in session:										  

		if request.method == 'POST':
			person_phone_or_email = request.form.get('user_email_or_phone')

			print('!!!!!!GETTING USER ID FROM NAV BAR SUBMISSION!!!!!!!')
			print('!')
			print('!')
		else:	
			person_phone_or_email = session['User_ID']

			print('!!!!!!GETTING USER ID IN BOTH CASES SUBMISSION!!!!!!!')
			print('!')
			print('!')

		result = db.execute("SELECT * FROM registrations WHERE phone=:person_phone_or_email OR email=:person_phone_or_email",
		{"person_phone_or_email":person_phone_or_email}).fetchall()
		for r in result:
			registration_status = r.reg_status
			phone = r.phone
			email = r.email
			password = r.password
			first_name = r.first_name
			last_name = r.last_name
			department = r.department
			registered_as = r.designation

		all_products = db.execute("SELECT * FROM products").fetchall()
		return render_template('allproductsuser.html', all_products = all_products, first_name = first_name, 
		last_name = last_name, department = department, registered_as = registered_as)	

	else:
		return redirect(url_for('index'))	




@app.route("/resetpassworduser")
def resetpassworduser():
	return render_template('resetpassworduser.html') 


@app.route("/resetpasswordsuperuser")
def resetpasswordsuperuser():
	return render_template('resetpasswordsuperuser.html') 	


@app.route("/updatepassword", methods = ["GET"])
def updatepassword():

	if 'User_ID' in session:

		return render_template('updatepassword.html')

	else:
		return redirect(url_for('index'))	

@app.route("/passwordupdate",methods=["POST"])
def passwordupdate():

	if "User_ID" in session:

		email_or_phone = request.form.get('email_Or_Phone')
		current_password = request.form.get('oldpassword')
		new_password = request.form.get('newpassword')
		confirm_new_password = request.form.get('cnewpassword')

		old_password = db.execute("SELECT password FROM registrations WHERE phone=:email_or_phone OR email=:email_or_phone",
		{"email_or_phone":email_or_phone}).fetchone()[0]

		if old_password != current_password:
			alert_type = 'error'
			flash (f"Sorry, You entered the current password wrong!")
			return render_template('updatepassword.html', alert_type = alert_type)

		elif old_password == current_password:	
			if new_password == confirm_new_password:
				db.execute("UPDATE registrations SET password=:new_password WHERE phone=:email_or_phone OR email=:email_or_phone",
				{"new_password":new_password, "email_or_phone":email_or_phone})
				db.commit()
				db.close()
				alert_type = 'success'
				flash (f"Your password has been updated successfully !")
				return render_template('updatepassword.html', alert_type = alert_type)	
		
			elif new_password != confirm_new_password:
				alert_type = 'error'
				flash (f"Please Confirm your New password Properly!")	
				return render_template('updatepassword.html', alert_type = alert_type)	

		else:
			alert_type = 'error'
			flash (f"Oops, Something went wrong!")	
			return render_template('updatepassword.html', alert_type = alert_type)	

	else:
		return redirect(url_for('index'))	


@app.route("/addcategory",methods=["POST", "GET"])
def addcategory():

	if 'SuperUser_ID' in session:

		# FUNCTION CALL TO FIND NUMBER OF LOW AND CRITICAL ITEMS IN THE STORE
		low_items_count, critical_items_count = findItemsCount()

		return render_template('addcategory.html', low_items_count = low_items_count, critical_items_count = critical_items_count) 

	else:
		return redirect(url_for('index'))	

# @app.route("/generatecode",methods=["post"])
# def generatecode():
#   # Declare a digits variable 
#   # which stores all digits 
#   digits = "0123456789"
#   Unique_code = "" 

#   # length of unique code can be chaged 
#   # by changing value in range 
#   for i in range(4): 
#       Unique_code += digits[math.floor(random.random() * 10)] 
		

	# print('start-start')
	# print(Unique_code)
	# print('end-wdnjkdfjd')    


#   return render_template('addcategory.html', Unique_code = Unique_code) 

#     # newcat = request.form.get('Newcat')
#     # cattype = request.form.get('Cattype')



@app.route("/addnewcategory",methods=["POST"])
def addnewcategory():

	if 'SuperUser_ID' in session:
	
		category_name = request.form.get('Newcat')
		category_type = request.form.get('Cattype')
		lowlevel_qty = request.form.get('Lowlevel')
		critical_level_qty = request.form.get('Crilevel')
		category_code = request.form.get('Catcode')

		result = db.execute("SELECT * FROM category WHERE category_name=:category_name",
		{"category_name":category_name}).fetchall() 

		for r in result:
			category_code = r.category_code

			if (result):
				alert_type = 'warning'
				flash (f"Sorry, Item { category_name } already exists with Category code { category_code }")

				# FUNCTION CALL TO FIND NUMBER OF LOW AND CRITICAL ITEMS IN THE STORE
				low_items_count, critical_items_count = findItemsCount()

				return render_template('addcategory.html', alert_type = alert_type, low_items_count = low_items_count, critical_items_count = critical_items_count)
		
			elif(result == []):
				db.execute("INSERT INTO category(category_name, category_type, lowlevel_qty, critical_level_qty, category_code) VALUES(:category_name, :category_type, :lowlevel_qty, :critical_level_qty, :category_code)",
				{"category_name":category_name,"category_type":category_type,"lowlevel_qty":lowlevel_qty,"critical_level_qty":critical_level_qty,"category_code":category_code})
				db.commit()
				db.close()
				alert_type = 'success'
				flash( f"New category { category_name } has been successfully added!")

				# FUNCTION CALL TO FIND NUMBER OF LOW AND CRITICAL ITEMS IN THE STORE
				low_items_count, critical_items_count = findItemsCount()

				return render_template('addcategory.html', alert_type = alert_type, low_items_count = low_items_count, critical_items_count = critical_items_count)

		alert_type = 'error'
		flash (f"Oops, Something went wrong!")

		# FUNCTION CALL TO FIND NUMBER OF LOW AND CRITICAL ITEMS IN THE STORE
		low_items_count, critical_items_count = findItemsCount()

		return render_template('addcategory.html', alert_type = alert_type, low_items_count = low_items_count, critical_items_count = critical_items_count)

	else:
		return redirect(url_for('index'))	

@app.route("/admin")
def admin():
	return render_template('admin.html')

@app.route("/faculty")
def faculty():
	return render_template('faculty.html')

@app.route("/head")
def head():
	return render_template('head.html')        

@app.route("/test")
def test():
	return render_template('test.html')


@app.route("/allproductsstoremanager",methods=["POST", "GET"])
def allproductsstoremanager():

	if 'SuperUser_ID' in session:

		all_products = db.execute("SELECT * FROM products").fetchall()

		# FUNCTION CALL TO FIND NUMBER OF LOW AND CRITICAL ITEMS IN THE STORE
		low_items_count, critical_items_count = findItemsCount()

		return render_template('allproductsstoremanager.html', all_products = all_products, low_items_count = low_items_count, critical_items_count = critical_items_count)

	else:
		return redirect(url_for('index'))	


@app.route("/criticalitems",methods=["GET"])
def criticalitems():

	if 'SuperUser_ID' in session:

		critical_items = db.execute("SELECT * FROM products WHERE qty_available <= critical_level_qty").fetchall()

		# FUNCTION CALL TO FIND NUMBER OF LOW AND CRITICAL ITEMS IN THE STORE
		low_items_count, critical_items_count = findItemsCount()

		return render_template('criticalitems.html', critical_items = critical_items, low_items_count = low_items_count, critical_items_count = critical_items_count)

	else:
		return redirect(url_for('index'))	


@app.route("/lowitems",methods=["GET"])
def lowitems():

	if 'SuperUser_ID' in session:

		low_items = db.execute("SELECT * FROM products WHERE qty_available <= lowlevel_qty").fetchall()

		# FUNCTION CALL TO FIND NUMBER OF LOW AND CRITICAL ITEMS IN THE STORE
		low_items_count, critical_items_count = findItemsCount()

		return render_template('lowitems.html', low_items = low_items, low_items_count = low_items_count, critical_items_count = critical_items_count)	

	else:
		return redirect(url_for('index'))	

@app.route("/issueditems",methods=["GET"])
def issueditems():

	if 'SuperUser_ID' in session:

		issued_items = db.execute("SELECT * FROM requests WHERE product_issued_on != 'Not-issued'").fetchall()

		# FUNCTION CALL TO FIND NUMBER OF LOW AND CRITICAL ITEMS IN THE STORE
		low_items_count, critical_items_count = findItemsCount()

		return render_template('issueditems.html', issued_items = issued_items, low_items_count = low_items_count, critical_items_count = critical_items_count)	

	else:
		return redirect(url_for('index'))	


@app.route("/userissueditems",methods=["GET","POST"])
def userissueditems():

	if 'User_ID' in session:

		if request.method == 'POST':
			person_phone_or_email = request.form.get('email_Or_Phone')

			print('!!!!!!GETTING USER ID FROM NAV BAR SUBMISSION!!!!!!!')
			print('!')
			print('!')
		else:	
			person_phone_or_email = session['User_ID']

			print('!!!!!!GETTING USER ID IN BOTH CASES SUBMISSION!!!!!!!')
			print('!')
			print('!')

		# print('!!!!!!!!PRINTING START-ISSUED ITEMS!!!!!!!')
		# print(person_phone_or_email)
		# print('NOW QUERY WILL RUN')

		result = db.execute("SELECT * from registrations WHERE phone=:person_phone_or_email OR email=:person_phone_or_email",
		{"person_phone_or_email":person_phone_or_email}).fetchall()

		# print(result)

		for r in result:
			first_name = r.first_name
			last_name = r.last_name

		# print('PRINTING FIRST AND LAST NAME')
		# print(first_name)
		# print(last_name)	

		full_name = str(first_name)	+ " " + str(last_name)	

		issued_items = db.execute("SELECT * FROM requests WHERE product_issued_on != 'Not-issued' AND requested_by=:full_name",
		{"full_name":full_name}).fetchall()

		print('NOW THE REQUESTED TEMPLATE WILL BE RENDERED')
		# FUNCTION CALL TO FIND NUMBER OF LOW AND CRITICAL ITEMS IN THE STORE
		low_items_count, critical_items_count = findItemsCount()

		return render_template('userissueditems.html', issued_items = issued_items, low_items_count = low_items_count, critical_items_count = critical_items_count)

	else:
		return redirect(url_for('index'))	


@app.route("/returneditems",methods=["GET"])
def returneditems():
	returned_items = db.execute("SELECT * FROM requests WHERE product_type != 'Consumable' AND product_issued_on != 'Not-issued' ").fetchall()
	return render_template('returneditems.html', returned_items = returned_items)	

@app.route("/userreturneditems",methods=["GET","POST"])
def userreturneditems():

	if 'User_ID' in session:

		if request.method == 'POST':
			person_phone_or_email = request.form.get('email_Or_Phone')

			print('!!!!!!GETTING USER ID FROM NAV BAR SUBMISSION!!!!!!!')
			print('!')
			print('!')
		else:	
			person_phone_or_email = session['User_ID']

			print('!!!!!!GETTING USER ID IN BOTH CASES SUBMISSION!!!!!!!')
			print('!')
			print('!')

		result = db.execute("SELECT * from registrations WHERE phone=:person_phone_or_email OR email=:person_phone_or_email",
		{"person_phone_or_email":person_phone_or_email}).fetchall()

		for r in result:
			first_name = r.first_name
			last_name = r.last_name

		full_name = str(first_name)	+ " " + str(last_name)	

		returned_items = db.execute("SELECT * FROM requests WHERE product_type != 'Consumable' AND product_issued_on != 'Not-issued' AND requested_by=:full_name",
		{"full_name":full_name}).fetchall()

		return render_template('userreturneditems.html', returned_items = returned_items)

	else:
		return redirect(url_for('index'))	

@app.route("/userrequesteditems",methods=["POST", "GET"])
def userrequesteditems():

	if 'User_ID' in session:

		if request.method == 'POST':
			person_phone_or_email = request.form.get('email_Or_Phone')

			print('!!!!!!GETTING USER ID FROM NAV BAR SUBMISSION!!!!!!!')
			print('!')
			print('!')
		else:	
			person_phone_or_email = session['User_ID']

			print('!!!!!!GETTING USER ID IN BOTH CASES SUBMISSION!!!!!!!')
			print('!')
			print('!')

		result = db.execute("SELECT * from registrations WHERE phone=:person_phone_or_email OR email=:person_phone_or_email",
		{"person_phone_or_email":person_phone_or_email}).fetchall()

		for r in result:
			first_name = r.first_name
			last_name = r.last_name

		print(result)	
			
		full_name = str(first_name)	+ " " + str(last_name)

		requested_items = db.execute("SELECT * from requests WHERE requested_by=:full_name",
		{"full_name":full_name}).fetchall()

		return render_template('userrequesteditems.html', requested_items = requested_items)

	else:
		return redirect(url_for('index'))	

# @app.route("/addrequest",methods=["GET", "POST"])
# def addrequest():

# 	now = datetime.now()
# 	request_date = now.strftime("%d-%m-%Y")
# 	request_time = now.strftime("%H:%M:%S")

# 	first_name = request.form.get('first_name')
# 	last_name = request.form.get('last_name')

# 	requested_by = str(first_name) + " " + str(last_name)

# 	department = request.form.get('department')
# 	designation = request.form.get('registered_as')

# 	product_id = request.form.get('product_id')
# 	add_this_produt = db.execute("SELECT * FROM products WHERE id=:product_id",
# 	{"product_id":product_id}).fetchall()
# 	db.commit()
# 	db.close()

# 	for r in add_this_produt:
# 		product_name   = r.product_name
# 		product_code   = r.product_code
# 		qty_available  = r.qty_available
# 		product_type   = r.product_type
# 		lowlevel_qty   = r.lowlevel_qty
# 		critical_level_qty = r.critical_level_qty
# 		product_mark_status = r.mark_status
# 		max_issuable_qty  = r.max_issuable_qty


# 	if product_mark_status == 'Marked':
# 		permission = 'Pending'

# 	elif product_mark_status == 'Not-Marked':
# 		permission = 'Not-Needed'	

# 	requested_qty = request.form.get('Quantity')

# 	product_request_exists = db.execute("SELECT * FROM requests WHERE product_code=:product_code AND requested_by=:requested_by",
# 	{'product_code':product_code, "requested_by":requested_by}).fetchall()

# 	if (product_request_exists):
# 		print('START')
# 		print('inside product_request_exists')
# 		print('ENDDD')
# 		for r in product_request_exists:
# 			previous_requested_qty = r.requested_qty
# 			new_requested_qty = previous_requested_qty  + int(requested_qty)

# 		# GIVE A FLASH MESSAGE THAT PRODUCT REQUEST QUANTITY UPDATED 

# 		# DO NOT FORGET TO GIVE THE FLASH MESSAGE

# 		db.execute("UPDATE requests SET requested_qty=:requested_qty WHERE product_code=:product_code AND requested_by=:requested_by",
# 		{"requested_qty":new_requested_qty, "product_code":product_code, "requested_by":requested_by})
# 		db.commit()
# 		db.close()

# 	# !!!!!!!!!!!!!!!!!!!!!! CHECKING COMPLETE !!!!!!!!!!!!!!!!!!!!
	
# 	else:
# 		if requested_qty > max_issuable_qty:
# 			print('inside else CONDITION i.e.')
# 			print('warning will be issued')
# 			alert_type = 'warning'
# 			flash (f"Sorry, You can not request for more than { max_issuable_qty } units of this item!")

# 			all_products = db.execute("SELECT * FROM products").fetchall()
# 			return render_template('allproductsuser.html', all_products = all_products, first_name = first_name, 
# 			last_name = last_name, department = department, registered_as = designation, alert_type = alert_type)

# 		elif requested_qty <= max_issuable_qty:	
# 			print('inside elif CONDITION i.e.')
# 			print('warning will NOT be issued')

# 			db.execute("INSERT INTO requests(product_name, product_code, qty_available, product_type, lowlevel_qty, critical_level_qty, requested_by, requested_qty, request_date, department, designation, product_mark_status, max_issuable_qty, permission) VALUES(:product_name, :product_code, :qty_available, :product_type, :lowlevel_qty, :critical_level_qty, :requested_by, :requested_qty, :request_date, :department, :designation, :product_mark_status, :max_issuable_qty, :permission)",
# 			{"product_name":product_name,"product_code":product_code,"qty_available":qty_available,"product_type":product_type, "lowlevel_qty":lowlevel_qty,"critical_level_qty":critical_level_qty, "requested_by":requested_by, "requested_qty":requested_qty, "request_date":request_date, "department":department, "designation":designation, "product_mark_status":product_mark_status, "max_issuable_qty":max_issuable_qty, "permission":permission})
# 			db.commit()
# 			db.close()    

# 	all_products = db.execute("SELECT * FROM products").fetchall()
# 	return render_template('allproductsuser.html', all_products = all_products, first_name = first_name, 
# 	last_name = last_name, department = department, registered_as = designation)





	#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! ADDING ADD REQUEST FEATURE AGAIN !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
	#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! ADDING ADD REQUEST FEATURE AGAIN !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

@app.route("/addrequest",methods=["GET", "POST"])
def addrequest():

	if 'User_ID' in session:

		now = datetime.now()
		request_date = now.strftime("%d-%m-%Y")
		request_time = now.strftime("%H:%M:%S")

		first_name = request.form.get('first_name')
		last_name = request.form.get('last_name')

		requested_by = str(first_name) + " " + str(last_name)

		department = request.form.get('department')
		designation = request.form.get('registered_as')

		requested_qty = request.form.get('Quantity')

		product_id = request.form.get('product_id')
		add_this_product = db.execute("SELECT * FROM products WHERE id=:product_id",
		{"product_id":product_id}).fetchall()
		db.commit()
		db.close()

		for r in add_this_product:
			product_name   = r.product_name
			product_code   = r.product_code
			qty_available  = r.qty_available
			product_type   = r.product_type
			lowlevel_qty   = r.lowlevel_qty
			critical_level_qty = r.critical_level_qty
			product_mark_status = r.mark_status
			max_issuable_qty  = r.max_issuable_qty

			
		product_request_exists = db.execute("SELECT * FROM requests WHERE product_code=:product_code AND requested_by=:requested_by",
		{'product_code':product_code, "requested_by":requested_by}).fetchall()

		print('start-start-start')
		print(max_issuable_qty)
		print(requested_qty)
		print('end-wdnjkdfjd-enddd')

		# THIS CODE WILL RUN WHEN THE max_issuable_qty IS Not-Specified FOR THE PRODUCT FOR WHICH REQUEST IS MADE

		if max_issuable_qty == 'Not-Specified':
			# CHECKING WHETHER PRODUCT REQUEST ALREADY EXISTS OR NOT

			if (product_request_exists):
				
				for r in product_request_exists:
					previous_requested_qty = r.requested_qty
					new_requested_qty = previous_requested_qty  + int(requested_qty)

				# GIVE A FLASH MESSAGE THAT PRODUCT REQUEST QUANTITY UPDATED 

				# DO NOT FORGET TO GIVE THE FLASH MESSAGE

				db.execute("UPDATE requests SET requested_qty=:requested_qty WHERE product_code=:product_code AND requested_by=:requested_by",
				{"requested_qty":new_requested_qty, "product_code":product_code, "requested_by":requested_by})
				db.commit()
				db.close()

				alert_type = 'success'
				flash (f"Your product request has been updated. Now the requested qty for { product_name } is { new_requested_qty } units.")

				all_products = db.execute("SELECT * FROM products").fetchall()
				return render_template('allproductsuser.html', all_products = all_products, first_name = first_name, 
				last_name = last_name, department = department, registered_as = designation, alert_type = alert_type)

			# !!!!!!!!!!!!!!!!!!!!!! CHECKING COMPLETE !!!!!!!!!!!!!!!!!!!!

			else:
				if product_mark_status == 'Marked':
					permission = 'Pending'

				else:
					permission = 'Not-Needed'

			
				db.execute("INSERT INTO requests(product_name, product_code, qty_available, product_type, lowlevel_qty, critical_level_qty, requested_by, requested_qty, request_date, department, designation, product_mark_status, permission) VALUES(:product_name, :product_code, :qty_available, :product_type, :lowlevel_qty, :critical_level_qty, :requested_by, :requested_qty, :request_date, :department, :designation, :product_mark_status, :permission)",
				{"product_name":product_name,"product_code":product_code,"qty_available":qty_available,"product_type":product_type, "lowlevel_qty":lowlevel_qty,"critical_level_qty":critical_level_qty, "requested_by":requested_by, "requested_qty":requested_qty, "request_date":request_date, "department":department, "designation":designation, "product_mark_status":product_mark_status, "permission":permission})
				db.commit()
				db.close()    

				all_products = db.execute("SELECT * FROM products").fetchall()
				return render_template('allproductsuser.html', all_products = all_products, first_name = first_name, 
				last_name = last_name, department = department, registered_as = designation)


		# THE ABOVE CODE RUNS WHEN THE REQUEST IS MADE FOR A PRODUCT WHOSE max_issuable_qty IS Not-Specified.

		# THIS CODE WILL RUN WHEN THE max_issuable_qty IS A SPECIFIED VALUE FOR THE PRODUCT FOR WHICH REQUEST IS MADE

		elif max_issuable_qty != 'Not-Specified':

			if int(requested_qty) > int(max_issuable_qty):
				alert_type = 'warning'
				flash (f"Sorry, You can not request for more than { max_issuable_qty } units of this item!")

				all_products = db.execute("SELECT * FROM products").fetchall()
				return render_template('allproductsuser.html', all_products = all_products, first_name = first_name, 
				last_name = last_name, department = department, registered_as = designation, alert_type = alert_type)

			elif int(requested_qty) <= int(max_issuable_qty):	

			# CHECKING WHETHER PRODUCT REQUEST ALREADY EXISTS OR NOT

				if (product_request_exists):
					
					for r in product_request_exists:
						previous_requested_qty = r.requested_qty
						new_requested_qty = previous_requested_qty  + int(requested_qty)

						remaining_issuable_qty = int(max_issuable_qty) - int(previous_requested_qty)


					if int(new_requested_qty) > int(max_issuable_qty):

						alert_type = 'warning'
						flash (f"Sorry, You can not request for more than { max_issuable_qty } units of this item! Since You have already requested for { previous_requested_qty } units, So you can request only for { remaining_issuable_qty } more units.")

						all_products = db.execute("SELECT * FROM products").fetchall()
						return render_template('allproductsuser.html', all_products = all_products, first_name = first_name, 
						last_name = last_name, department = department, registered_as = designation, alert_type = alert_type)

					elif int(new_requested_qty) <= int(max_issuable_qty):

						db.execute("UPDATE requests SET requested_qty=:new_requested_qty WHERE product_code=:product_code AND requested_by=:requested_by",
						{"new_requested_qty":new_requested_qty, "product_code":product_code, "requested_by":requested_by})
						db.commit()
						db.close()

						alert_type = 'success'
						flash (f"Your product request has been updated. Now the requested qty for { product_name }is { new_requested_qty } units.")

						all_products = db.execute("SELECT * FROM products").fetchall()
						return render_template('allproductsuser.html', all_products = all_products, first_name = first_name, 
						last_name = last_name, department = department, registered_as = designation, alert_type = alert_type)

				# !!!!!!!!!!!!!!!!!!!!!! CHECKING COMPLETE !!!!!!!!!!!!!!!!!!!!

				else:	

					if product_mark_status == 'Marked':
						permission = 'Pending'

					else:
						permission = 'Not-Needed'

			
					db.execute("INSERT INTO requests(product_name, product_code, qty_available, product_type, lowlevel_qty, critical_level_qty, requested_by, requested_qty, request_date, department, designation, product_mark_status, permission, max_issuable_qty) VALUES(:product_name, :product_code, :qty_available, :product_type, :lowlevel_qty, :critical_level_qty, :requested_by, :requested_qty, :request_date, :department, :designation, :product_mark_status, :permission, :max_issuable_qty)",
					{"product_name":product_name,"product_code":product_code,"qty_available":qty_available,"product_type":product_type, "lowlevel_qty":lowlevel_qty,"critical_level_qty":critical_level_qty, "requested_by":requested_by, "requested_qty":requested_qty, "request_date":request_date, "department":department, "designation":designation, "product_mark_status":product_mark_status, "permission":permission, "max_issuable_qty":max_issuable_qty})
					db.commit()
					db.close()    

					all_products = db.execute("SELECT * FROM products").fetchall()
					return render_template('allproductsuser.html', all_products = all_products, first_name = first_name, 
					last_name = last_name, department = department, registered_as = designation)


		# THE ABOVE CODE RUNS WHEN THE REQUEST IS MADE FOR A PRODUCT WHOSE max_issuable_qty IS A SPECIFIED VALUE.			


		else:
			alert_type = 'error'
			flash(f"Oops, Something went wrong!")
			all_products = db.execute("SELECT * FROM products").fetchall()
			return render_template('allproductsuser.html', all_products = all_products, first_name = first_name, 
			last_name = last_name, department = department, registered_as = designation, alert_type = alert_type)		

	else:
		return redirect(url_for('index'))		

	#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! ADD REQUEST FEATURE AGAIN ADDED!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
	#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! ADD REQUEST FEATURE AGAIN ADDED!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! 
	


@app.route("/deleterequest",methods=["GET", "POST"])
def deleterequest():

	if 'User_ID' in session:

		# now = datetime.now()
		# leaving_time = now.strftime("%H:%M:%S")

		first_name = request.form.get('first_name')
		last_name = request.form.get('last_name')

		requested_by = str(first_name) + " " + str(last_name)

		department = request.form.get('department')
		designation = request.form.get('registered_as')

		product_code = request.form.get('product_code')
		
		db.execute("DELETE from requests WHERE product_code=:product_code AND requested_by=:requested_by",
		{"product_code":product_code, "requested_by":requested_by})
		db.commit()
		db.close()

		all_products = db.execute("SELECT * FROM products").fetchall()
		return render_template('allproductsuser.html', all_products = all_products, first_name = first_name, 
		last_name = last_name, department = department, registered_as = designation)

	else:
		return redirect(url_for('index'))	



@app.route("/allcategories",methods=["POST", "GET"])
def allcategories():

	if 'SuperUser_ID' in session:

		all_categories = db.execute("SELECT * FROM category").fetchall()

		# FUNCTION CALL TO FIND NUMBER OF LOW AND CRITICAL ITEMS IN THE STORE
		low_items_count, critical_items_count = findItemsCount()

		return render_template('allcategories.html', all_categories = all_categories, low_items_count = low_items_count, critical_items_count = critical_items_count)

	else:
		return redirect(url_for('index'))	


@app.route("/allrequests", methods=['GET'])
def allrequests():

	if 'SuperUser_ID' in session:

		all_requests = db.execute("SELECT * FROM requests").fetchall()

		# FUNCTION CALL TO FIND NUMBER OF LOW AND CRITICAL ITEMS IN THE STORE
		low_items_count, critical_items_count = findItemsCount()

		return render_template('allrequests.html', all_requests = all_requests, low_items_count = low_items_count, critical_items_count = critical_items_count)  

	else:
		return redirect(url_for('index'))	


@app.route("/acceptrequest/<product_request_id>",methods=["GET", "POST"])
def acceptrequest(product_request_id):

	if 'SuperUser_ID' in session:

		new_status = 'Approved'

		result = db.execute("SELECT * from requests WHERE id=:product_request_id",
		{"product_request_id":product_request_id}).fetchall()

		for r in result:
			product_mark_status = r.product_mark_status
			permission = r.permission
			product_code = r.product_code	
			requested_qty = r.requested_qty	

		
		if product_mark_status == 'Not-Marked' or product_mark_status == 'Marked' and permission == 'Granted':

			requested_product = db.execute("SELECT * from products WHERE product_code=:product_code",
			{"product_code":product_code}).fetchall()

			for r in requested_product:
				qty_available = r.qty_available

			if requested_qty > qty_available:

				alert_type = 'warning'
				flash (f"Sorry, This request can not be accepted because requested quantity is greater than the available quantity")

				# FUNCTION CALL TO FIND NUMBER OF LOW AND CRITICAL ITEMS IN THE STORE
				low_items_count, critical_items_count = findItemsCount()

				all_requests = db.execute("SELECT * FROM requests").fetchall()
				return render_template('allrequests.html', all_requests = all_requests, low_items_count = low_items_count, critical_items_count = critical_items_count)
		

			elif requested_qty <= qty_available:
				
				db.execute("UPDATE requests SET reason = NULL, request_status=:new_status WHERE id=:product_request_id",
				{"product_request_id":product_request_id, "new_status":new_status})
				db.commit()
				db.close()

				# FUNCTION CALL TO FIND NUMBER OF LOW AND CRITICAL ITEMS IN THE STORE
				low_items_count, critical_items_count = findItemsCount()

				all_requests = db.execute("SELECT * FROM requests").fetchall()
				return render_template('allrequests.html', all_requests = all_requests, low_items_count = low_items_count, critical_items_count = critical_items_count)

		elif product_mark_status == 'Marked' and permission == 'Pending':
			alert_type = 'info'
			flash (f"Sorry, This request has not yet been accepted by the Head!")

			# FUNCTION CALL TO FIND NUMBER OF LOW AND CRITICAL ITEMS IN THE STORE
			low_items_count, critical_items_count = findItemsCount()

			all_requests = db.execute("SELECT * FROM requests").fetchall()
			return render_template('allrequests.html', all_requests = all_requests, alert_type = alert_type, low_items_count = low_items_count, critical_items_count = critical_items_count)

		elif product_mark_status == 'Marked' and permission == 'Denied':
			alert_type = 'warning'
			flash (f"Sorry, This request has been rejected by the Head!")

			# FUNCTION CALL TO FIND NUMBER OF LOW AND CRITICAL ITEMS IN THE STORE
			low_items_count, critical_items_count = findItemsCount()

			all_requests = db.execute("SELECT * FROM requests").fetchall()
			return render_template('allrequests.html', all_requests = all_requests, alert_type = alert_type, low_items_count = low_items_count, critical_items_count = critical_items_count)

		else:
			alert_type = 'error'
			flash (f"Oops, Something went wrong!")
			all_requests = db.execute("SELECT * FROM requests").fetchall()

			# FUNCTION CALL TO FIND NUMBER OF LOW AND CRITICAL ITEMS IN THE STORE
			low_items_count, critical_items_count = findItemsCount()

			return render_template('allrequests.html', all_requests = all_requests, alert_type = alert_type, low_items_count = low_items_count, critical_items_count = critical_items_count)
			
	else:
		return redirect(url_for('index'))		


@app.route("/rejectrequest",methods=["GET", "POST"])
def rejectrequest():

	if 'SuperUser_ID' in session:

		# now = datetime.now()
		# leaving_time = now.strftime("%H:%M:%S")

		product_request_id= request.args.get('Product_request_id')
		rejection_reason = request.args.get('Reason')
			
		new_status = 'Not-Approved'

		db.execute("UPDATE requests SET request_status=:new_status, reason=:reason WHERE id=:product_request_id",
		{"product_request_id":product_request_id, "new_status":new_status, "reason":rejection_reason})
		db.commit()
		db.close()

		# print('START')
		# print(product_code)
		# print(rejection_reason)
		# print('ENDDD')

		all_requests = db.execute("SELECT * FROM requests").fetchall()

		# FUNCTION CALL TO FIND NUMBER OF LOW AND CRITICAL ITEMS IN THE STORE
		low_items_count, critical_items_count = findItemsCount()

		return render_template('allrequests.html', all_requests = all_requests, low_items_count = low_items_count, critical_items_count = critical_items_count)

	else:
		return redirect(url_for('index'))	
   


@app.route("/issueproduct/<product_request_id>",methods=["GET", "POST"])
def issueproduct(product_request_id):

	if 'SuperUser_ID' in session:

		now = datetime.now()
		product_issue_date = now.strftime("%d-%m-%Y")
		product_issue_time= now.strftime("%H:%M:%S")

		result = db.execute("SELECT * from requests WHERE id=:product_request_id",
		{"product_request_id":product_request_id}).fetchall()


		for r in result:
			request_status = r.request_status
			product_code = r.product_code
			requested_qty = r.requested_qty


		requested_product = db.execute("SELECT * from products WHERE product_code=:product_code",
		{"product_code":product_code}).fetchall()

		for r in requested_product:
			qty_available = r.qty_available	

		if request_status == 'Approved':

			if requested_qty > qty_available:

				alert_type = 'warning'
				flash (f"Sorry, This item can not be issued because requested quantity is greater than the available quantity")
				all_requests = db.execute("SELECT * FROM requests").fetchall()

				# FUNCTION CALL TO FIND NUMBER OF LOW AND CRITICAL ITEMS IN THE STORE
				low_items_count, critical_items_count = findItemsCount()

				return render_template('allrequests.html', all_requests = all_requests, low_items_count = low_items_count, critical_items_count = critical_items_count)

			elif requested_qty <= qty_available:

				#PROCESS OF ISSUING PRODUCT INVOLVES 3 STEPS:

				#STEP-1->REDUCE THE AVAILABLE QUANTITY OF REQUESTED PRODUCT IN THE PRODUCTS TABLE

				updated_qty_available = qty_available - requested_qty    # REMAINING QUANTITY OF THE REQUESTED PRODUCT

				db.execute("UPDATE products SET qty_available=:updated_qty_available WHERE product_code=:product_code",
				{"updated_qty_available":updated_qty_available, "product_code":product_code})
				db.commit()
				db.close()

				#STEP-2->UPDATE THE VALUE OF product_issued_on COLUMN OF requests TABLE WITH THE DATE ON WHICH PRODUCT IS BEING ISSUED

				db.execute("UPDATE requests SET product_issued_on=:product_issued_on WHERE id=:product_request_id",
				{"product_issued_on":product_issue_date, "product_request_id":product_request_id})
				db.commit()
				db.close()

				#STEP-3->UPDATE THE NEW AVAILABLE QUANTITY OF THE ISSUED PRODUCT FOR ALL REQUESTS CORRESPONDING TO THAT PARTICULAR PRODUCT 

				db.execute("UPDATE requests SET qty_available=:updated_qty_available WHERE product_code=:product_code",
				{"updated_qty_available":updated_qty_available, "product_code":product_code})
				db.commit()
				db.close()

				all_requests = db.execute("SELECT * FROM requests").fetchall()

				# FUNCTION CALL TO FIND NUMBER OF LOW AND CRITICAL ITEMS IN THE STORE
				low_items_count, critical_items_count = findItemsCount()

				return render_template('allrequests.html', all_requests = all_requests, low_items_count = low_items_count, critical_items_count = critical_items_count)

		elif request_status == 'Not-Approved':
			alert_type = 'error'
			flash (f"Sorry, This request has been Rejected!")
			all_requests = db.execute("SELECT * FROM requests").fetchall()

			# FUNCTION CALL TO FIND NUMBER OF LOW AND CRITICAL ITEMS IN THE STORE
			low_items_count, critical_items_count = findItemsCount()

			return render_template('allrequests.html', all_requests = all_requests, alert_type = alert_type, low_items_count = low_items_count, critical_items_count = critical_items_count)

		elif request_status == 'Pending':
			alert_type = 'warning'
			flash (f"Sorry, This request has not been approved yet!")
			all_requests = db.execute("SELECT * FROM requests").fetchall()

			# FUNCTION CALL TO FIND NUMBER OF LOW AND CRITICAL ITEMS IN THE STORE
			low_items_count, critical_items_count = findItemsCount()

			return render_template('allrequests.html', all_requests = all_requests, alert_type = alert_type, low_items_count = low_items_count, critical_items_count = critical_items_count)

		else:
			alert_type = 'error'
			flash (f"Oops, Something went wrong!")	
			all_requests = db.execute("SELECT * FROM requests").fetchall()

			# FUNCTION CALL TO FIND NUMBER OF LOW AND CRITICAL ITEMS IN THE STORE
			low_items_count, critical_items_count = findItemsCount()

			return render_template('allrequests.html', all_requests = all_requests, alert_type = alert_type, low_items_count = low_items_count, critical_items_count = critical_items_count)

	else:
		return redirect(url_for('index'))		


@app.route("/returnproduct/<product_request_id>/<product_issued_on>",methods=["GET", "POST"])
def returnproduct(product_request_id,product_issued_on):

	if 'SuperUser_ID' in session:

		now = datetime.now()
		product_return_date = now.strftime("%d-%m-%Y")
		product_return_time= now.strftime("%H:%M:%S")

		if product_issued_on == 'Not-issued':
			alert_type = 'error'
			flash (f"Sorry, This product was never issued!")	
			all_requests = db.execute("SELECT * FROM requests").fetchall()

			# FUNCTION CALL TO FIND NUMBER OF LOW AND CRITICAL ITEMS IN THE STORE
			low_items_count, critical_items_count = findItemsCount()

			return render_template('allrequests.html', all_requests = all_requests, alert_type = alert_type, low_items_count = low_items_count, critical_items_count = critical_items_count)

		elif product_issued_on != 'Not-issued':

			result = db.execute("SELECT * from requests WHERE id=:product_request_id",
			{"product_request_id":product_request_id}).fetchall()

			for r in result:
				product_code = r.product_code
				requested_qty = r.requested_qty

			requested_product = db.execute("SELECT * from products WHERE product_code=:product_code",
			{"product_code":product_code}).fetchall()

			for r in requested_product:
				qty_available = r.qty_available		

			#PROCESS OF RECEIEVING BACK A PRODUCT INVOLVES 3 STEPS:

			#STEP-1->INCREASE THE AVAILABLE QUANTITY OF REQUESTED PRODUCT IN THE PRODUCTS TABLE WHEN PRODUCT IS RETURNED

			updated_qty_available = qty_available + requested_qty    # NEW INCREASED QUANTITY OF THE REQUESTED PRODUCT

			db.execute("UPDATE products SET qty_available=:updated_qty_available WHERE product_code=:product_code",
			{"updated_qty_available":updated_qty_available, "product_code":product_code})
			db.commit()
			db.close()

			#STEP-2->UPDATE THE VALUE OF returned_on COLUMN OF requests TABLE WITH THE DATE ON WHICH PRODUCT IS BEING RETURNED

			db.execute("UPDATE requests SET returned_on=:product_returned_on WHERE id=:product_request_id",
			{"product_returned_on":product_return_date, "product_request_id":product_request_id})
			db.commit()
			db.close()

			#STEP-3->UPDATE THE NEW AVAILABLE QUANTITY OF THE RETURNED PRODUCT FOR ALL REQUESTS CORRESPONDING TO THAT PARTICULAR PRODUCT 

			db.execute("UPDATE requests SET qty_available=:updated_qty_available WHERE product_code=:product_code",
			{"updated_qty_available":updated_qty_available, "product_code":product_code})
			db.commit()
			db.close()


			all_requests = db.execute("SELECT * FROM requests").fetchall()

			# FUNCTION CALL TO FIND NUMBER OF LOW AND CRITICAL ITEMS IN THE STORE
			low_items_count, critical_items_count = findItemsCount()
			
			return render_template('allrequests.html', all_requests = all_requests, low_items_count = low_items_count, critical_items_count = critical_items_count)	

		else:
			alert_type = 'error'
			flash (f"Oops, Something went wrong!")	
			all_requests = db.execute("SELECT * FROM requests").fetchall()

			# FUNCTION CALL TO FIND NUMBER OF LOW AND CRITICAL ITEMS IN THE STORE
			low_items_count, critical_items_count = findItemsCount()

			return render_template('allrequests.html', all_requests = all_requests, alert_type = alert_type, low_items_count = low_items_count, critical_items_count = critical_items_count)

	else:
		return redirect(url_for('index'))		


# THIS IS A VERY IMPORTANT FUNCTION THAT FINDS THE NUMBER OF CRITICAL AND LOW ITEMS IN THE STORE
# THESE VALUES ARE THEN SHOWN IN THE NAVIGATION BAR OF STORE MANAGER AND HEAD

def findItemsCount():
	low_items = db.execute("SELECT * FROM products WHERE qty_available <= lowlevel_qty").fetchall()

	# COUNTING THE NUMBER OF ITEMS BELOW LOW LEVEL
	i = 0
	count = 0
	for item in low_items:
		i += 1

	low_items_count = i

	critical_items = db.execute("SELECT * FROM products WHERE qty_available <= critical_level_qty").fetchall()

	# COUNTING THE NUMBER OF ITEMS BELOW CRITICAL LEVEL
	i = 0
	count = 0
	for item in critical_items:
		i += 1

	critical_items_count = i

	return low_items_count, critical_items_count

@app.route("/allproductshead")
def allproductshead():

	if 'SuperUser_ID' in session:

		all_products = db.execute("SELECT * FROM products").fetchall()

		# FUNCTION CALL TO FIND NUMBER OF LOW AND CRITICAL ITEMS IN THE STORE
		low_items_count, critical_items_count = findItemsCount()	

		return render_template('allproductshead.html', all_products = all_products, low_items_count = low_items_count, critical_items_count = critical_items_count)

	else:
		return redirect(url_for('index'))	


@app.route("/setmaxissuableqty",methods=["GET", "POST"])
def setmaxissuableqty():

	if 'SuperUser_ID' in session:

		product_code = request.form.get('product_code')
		max_issuable_qty = request.form.get('Quantity')

		db.execute("UPDATE products SET max_issuable_qty=:max_issuable_qty WHERE product_code=:product_code",
		{"max_issuable_qty":max_issuable_qty, "product_code":product_code})
		db.commit()
		db.close()

		# UPDATING max_issuable_qty COLUMN VALUE IN REQUESTS TABLE WHEN THE UPPERLIMIT ON max_issuable_qty IS SET 
		db.execute("UPDATE requests SET max_issuable_qty=:max_issuable_qty WHERE product_code=:product_code",
		{"max_issuable_qty":max_issuable_qty, "product_code":product_code})
		db.commit()
		db.close()

		# FUNCTION CALL TO FIND NUMBER OF LOW AND CRITICAL ITEMS IN THE STORE
		low_items_count, critical_items_count = findItemsCount()

		all_products = db.execute("SELECT * FROM products").fetchall()
		return render_template('allproductshead.html', all_products = all_products, low_items_count = low_items_count, critical_items_count = critical_items_count)

	else:
		return redirect(url_for('index'))	

@app.route("/removemaxissuableqty/<product_code>",methods=["GET", "POST"])
def removemaxissuableqty(product_code):

	if 'SuperUser_ID' in session:

		db.execute("UPDATE products SET max_issuable_qty = DEFAULT WHERE product_code=:product_code",
		{"product_code":product_code})
		db.commit()
		db.close()

		# UPDATING max_issuable_qty COLUMN VALUE IN REQUESTS TABLE WHEN THE UPPERLIMIT ON max_issuable_qty IS REMOVED
		db.execute("UPDATE requests SET max_issuable_qty = DEFAULT WHERE product_code=:product_code",
		{"product_code":product_code})
		db.commit()
		db.close()

		# FUNCTION CALL TO FIND NUMBER OF LOW AND CRITICAL ITEMS IN THE STORE
		low_items_count, critical_items_count = findItemsCount()

		all_products = db.execute("SELECT * FROM products").fetchall()
		return render_template('allproductshead.html', all_products = all_products, low_items_count = low_items_count, critical_items_count = critical_items_count)

	else:
		return redirect(url_for('index'))	


@app.route("/markitems/<product_code>",methods=["GET", "POST"])
def markitems(product_code):

	if 'SuperUser_ID' in session:

		mark_status = "Marked"

		db.execute("UPDATE products SET mark_status=:mark_status WHERE product_code=:product_code",
		{"mark_status":mark_status, "product_code":product_code})
		db.commit()
		db.close()

		# UPDATING product_mark_status AND permission COLUMN VALUE IN REQUESTS TABLE WHEN AN ITEM IS MARKED
		updated_permission = "Pending"
		db.execute("UPDATE requests SET product_mark_status=:mark_status, permission=:updated_permission WHERE product_code=:product_code",
		{"mark_status":mark_status,"updated_permission":updated_permission, "product_code":product_code})
		db.commit()
		db.close()


		# FUNCTION CALL TO FIND NUMBER OF LOW AND CRITICAL ITEMS IN THE STORE
		low_items_count, critical_items_count = findItemsCount()

		all_products = db.execute("SELECT * FROM products").fetchall()
		return render_template('allproductshead.html', all_products = all_products, low_items_count = low_items_count, critical_items_count = critical_items_count)

	else:
		return redirect(url_for('index'))	


@app.route("/unmarkitems/<product_code>",methods=["GET", "POST"])
def unmarkitems(product_code):

	if 'SuperUser_ID' in session:

		db.execute("UPDATE products SET mark_status = DEFAULT WHERE product_code=:product_code",
		{"product_code":product_code})
		db.commit()
		db.close()

		# UPDATING product_mark_status AND permission COLUMN VALUE IN REQUESTS TABLE WHEN AN ITEM IS UNMARKED
		db.execute("UPDATE requests SET product_mark_status = DEFAULT, permission = DEFAULT WHERE product_code=:product_code",
		{"product_code":product_code})
		db.commit()
		db.close()

		# FUNCTION CALL TO FIND NUMBER OF LOW AND CRITICAL ITEMS IN THE STORE
		low_items_count, critical_items_count = findItemsCount()

		all_products = db.execute("SELECT * FROM products").fetchall()
		return render_template('allproductshead.html', all_products = all_products, low_items_count = low_items_count, critical_items_count = critical_items_count)	

	else:
		return redirect(url_for('index'))	


@app.route("/allrequestshead", methods = ["GET"])
def allrequestshead():

	if 'SuperUser_ID' in session:

		all_requests = db.execute("SELECT * FROM requests").fetchall()

		# FUNCTION CALL TO FIND NUMBER OF LOW AND CRITICAL ITEMS IN THE STORE
		low_items_count, critical_items_count = findItemsCount()

		return render_template('allrequestshead.html', all_requests = all_requests, low_items_count = low_items_count, critical_items_count = critical_items_count)	

	else:
		return redirect(url_for('index'))	


@app.route("/issueditemshead",methods=["GET"])
def issueditemshead():

	if 'SuperUser_ID' in session:

		issued_items = db.execute("SELECT * FROM requests WHERE product_issued_on != 'Not-issued'").fetchall()

		# FUNCTION CALL TO FIND NUMBER OF LOW AND CRITICAL ITEMS IN THE STORE
		low_items_count, critical_items_count = findItemsCount()

		return render_template('issueditemshead.html', issued_items = issued_items, low_items_count = low_items_count, critical_items_count = critical_items_count)	

	else:
		return redirect(url_for('index'))	


@app.route("/criticalitemshead",methods=["GET"])
def criticalitemshead():

	if 'SuperUser_ID' in session:

		critical_items = db.execute("SELECT * FROM products WHERE qty_available <= critical_level_qty").fetchall()

		# FUNCTION CALL TO FIND NUMBER OF LOW AND CRITICAL ITEMS IN THE STORE
		low_items_count, critical_items_count = findItemsCount()

		return render_template('criticalitemshead.html', critical_items = critical_items, low_items_count = low_items_count, critical_items_count = critical_items_count)

	else:
		return redirect(url_for('index'))	


@app.route("/lowitemshead",methods=["GET"])
def lowitemshead():

	if 'SuperUser_ID' in session:

		low_items = db.execute("SELECT * FROM products WHERE qty_available <= lowlevel_qty").fetchall()

		# FUNCTION CALL TO FIND NUMBER OF LOW AND CRITICAL ITEMS IN THE STORE
		low_items_count, critical_items_count = findItemsCount()

		return render_template('lowitemshead.html', low_items = low_items, low_items_count = low_items_count, critical_items_count = critical_items_count)

	else:
		return redirect(url_for('index'))	

@app.route("/returneditemshead",methods=["GET"])
def returneditemshead():

	if 'SuperUser_ID' in session:

		returned_items = db.execute("SELECT * FROM requests WHERE product_type != 'Consumable' AND product_issued_on != 'Not-issued' ").fetchall()

		# FUNCTION CALL TO FIND NUMBER OF LOW AND CRITICAL ITEMS IN THE STORE
		low_items_count, critical_items_count = findItemsCount()

		return render_template('returneditemshead.html', returned_items = returned_items, low_items_count = low_items_count, critical_items_count = critical_items_count)

	else:
		return redirect(url_for('index'))	


@app.route("/updatepasswordhead",methods=["GET"])
def updatepasswordhead():

	if 'SuperUser_ID' in session:

		# FUNCTION CALL TO FIND NUMBER OF LOW AND CRITICAL ITEMS IN THE STORE
		low_items_count, critical_items_count = findItemsCount()

		return render_template('updatepasswordhead.html', low_items_count = low_items_count, critical_items_count = critical_items_count)

	else:
		return redirect(url_for('index'))	


@app.route("/updatepasswordstoremanager",methods=["GET"])
def updatepasswordstoremanager():

	if 'SuperUser_ID' in session:

		# FUNCTION CALL TO FIND NUMBER OF LOW AND CRITICAL ITEMS IN THE STORE
		low_items_count, critical_items_count = findItemsCount()

		return render_template('updatepasswordstoremanager.html', low_items_count = low_items_count, critical_items_count = critical_items_count)

	else:
		return redirect(url_for('index'))	
	
@app.route("/updatepasswordadmin",methods=["GET"])
def updatepasswordadmin():

	if 'SuperUser_ID' in session:

		return render_template('updatepasswordadmin.html')

	else:
		return redirect(url_for('index'))	


@app.route("/grantissuepermission/<product_request_id>",methods=["GET", "POST"])
def grantissuepermission(product_request_id):

	if 'SuperUser_ID' in session:

		updated_permission = 'Granted'

		db.execute("UPDATE requests SET permission=:updated_permission WHERE id=:product_request_id",
		{"updated_permission":updated_permission, "product_request_id":product_request_id})
		db.commit()
		db.close()

		# FUNCTION CALL TO FIND NUMBER OF LOW AND CRITICAL ITEMS IN THE STORE
		low_items_count, critical_items_count = findItemsCount()

		all_requests = db.execute("SELECT * FROM requests").fetchall()
		return render_template('allrequestshead.html', all_requests = all_requests, low_items_count = low_items_count, critical_items_count = critical_items_count)

	else:
		return redirect(url_for('index'))	

@app.route("/denyissuepermission/<product_request_id>",methods=["GET", "POST"])
def denyissuepermission(product_request_id):

	if 'SuperUser_ID' in session: 

		updated_permission = 'Denied'

		db.execute("UPDATE requests SET permission=:updated_permission WHERE id=:product_request_id",
		{"updated_permission":updated_permission, "product_request_id":product_request_id})
		db.commit()
		db.close()

		# FUNCTION CALL TO FIND NUMBER OF LOW AND CRITICAL ITEMS IN THE STORE
		low_items_count, critical_items_count = findItemsCount()

		all_requests = db.execute("SELECT * FROM requests").fetchall()
		return render_template('allrequestshead.html', all_requests = all_requests, low_items_count = low_items_count, critical_items_count = critical_items_count)

	else:
		return redirect(url_for('index'))	


@app.route("/resetpassword",methods=["GET", "POST"])
def resetpassword():
	destination_email = request.form.get('email')

	user_name = db.execute("SELECT first_name FROM registrations WHERE email=:destination_email",
	{"destination_email":destination_email}).fetchone()[0]

	# initializing size of string to be used as the new password for login 
	N = 7
	  
	# using random.choices() 
	# generating random strings  
	random_string = ''.join(random.choices(string.ascii_uppercase +
	                             string.digits, k = N)) 

	new_password = str(random_string)

	db.execute("UPDATE registrations SET password=:new_password WHERE email=:destination_email",
	{"new_password":new_password, "destination_email":destination_email})
	db.commit()
	db.close()

	msg = Message(subject="Inventory-Mgmt-System:Password Reset Request",
	sender=app.config.get("MAIL_USERNAME"),
	recipients = [destination_email],
	body = "Hey " + user_name + "," + " You requested for a password Reset for your account.\n"
	"Your new password is: " + new_password + "\nYou can now login using your new Password." 
	"\nHave a nice day!" +"\n\n\n" + "Regards" + "\nVikrant Arora" + "\nDeveloper-Inventory Management System" )

	mail.send(msg)	

	alert_type = 'success'
	flash (f"Your New Password has been sent to Your email address { destination_email }")	
	return render_template('resetpassworduser.html', alert_type = alert_type)



#	THIS CODE IS USED TO RESET THE PASSWORD OF SUPERUSERS AND SEND THEM THE UPDATED PASSWORD THROUGH EMAIL

@app.route("/superuserresetpassword",methods=["GET", "POST"])
def superuserresetpassword():
	destination_email = request.form.get('email')

	superuser_name = db.execute("SELECT first_name FROM superuser WHERE email=:destination_email",
	{"destination_email":destination_email}).fetchone()[0]

	# initializing size of string to be used as the new password for login 
	N = 7
	  
	# using random.choices() 
	# generating random strings  
	random_string = ''.join(random.choices(string.ascii_uppercase +
	                             string.digits, k = N)) 

	new_password = str(random_string)

	db.execute("UPDATE superuser SET password=:new_password WHERE email=:destination_email",
	{"new_password":new_password, "destination_email":destination_email})
	db.commit()
	db.close()

	msg = Message(subject="Inventory-Mgmt-System:Password Reset Request",
	sender=app.config.get("MAIL_USERNAME"),
	recipients = [destination_email],
	body = "Hey " + superuser_name + "," + " You requested for a password Reset for your account.\n"
	"Your new password is: " + new_password + "\nYou can now login using your new Password." 
	"\nHave a nice day!" +"\n\n\n" + "Regards" + "\nVikrant Arora" + "\nDeveloper-Inventory Management System" )

	mail.send(msg)	

	alert_type = 'success'
	flash (f"Your New Password has been sent to Your email address { destination_email }")	
	return render_template('resetpassworduser.html', alert_type = alert_type)

#	RESET PASSWORD CODE FOR SUPERUSER ENDS HERE 
		

@app.route("/superuserlogin", methods=['POST', 'GET'])
def superuserlogin():

	if 'SuperUser_ID' in session:  # MEANS SUPERUSER IS ALREADY LOGGED IN

		person_phone_or_email = session['SuperUser_ID'] 

		result = db.execute("SELECT * FROM superuser WHERE phone=:person_phone_or_email OR email=:person_phone_or_email",
		{"person_phone_or_email":person_phone_or_email}).fetchall()
		for r in result:
			first_name = r.first_name
			last_name = r.last_name
			designation = r.designation

		alert_type = 'info'

		flash (f" Hey { first_name }, You are already logged in FROM SUPERUSER LOGIN PAGE!") 

		if designation == 'Head':

			all_products = db.execute("SELECT * FROM products").fetchall()

			# FUNCTION CALL TO FIND NUMBER OF LOW AND CRITICAL ITEMS IN THE STORE
			low_items_count, critical_items_count = findItemsCount()	

			return render_template('allproductshead.html', all_products = all_products, alert_type = alert_type, low_items_count = low_items_count, critical_items_count = critical_items_count)


		elif designation == 'Store Manager':

			all_products = db.execute("SELECT * FROM products").fetchall()

			# FUNCTION CALL TO FIND NUMBER OF LOW AND CRITICAL ITEMS IN THE STORE
			low_items_count, critical_items_count = findItemsCount()

			return render_template('allproductsstoremanager.html', all_products = all_products, alert_type = alert_type , low_items_count = low_items_count, critical_items_count = critical_items_count)


		elif designation == 'Admin':

			all_registrations = db.execute("SELECT * FROM registrations").fetchall()

			# FUNCTION CALL TO FIND NUMBER OF LOW AND CRITICAL ITEMS IN THE STORE
			# low_items_count, critical_items_count = findItemsCount()

			# ADMIN WILL NOT SEE THE LIST OF PRODUCTS , IT WILL LAND ON THE allregistrations PAGE 
			# WHERE HE WILL BE ABLE TO APPROVE OR REJECT REGISTRATIONS

			return render_template('allregistrations.html', all_registrations = all_registrations, alert_type = alert_type)

	else:  # MEANS SUPERUSER IS NOT LOGGED IN
		return render_template('superuserlogin.html')	


@app.route("/newsuperuserlogin", methods=['POST', 'GET'])
def newsuperuserlogin():

	if not 'SuperUser_ID' in session:  # MEANS SUPERUSER IS NOT LOGGED IN

		if request.method == 'POST':

			person_phone_or_email = request.form['EPhone']
			person_password = request.form.get('Password')

			designation = request.form.get('Designation')

			print('start-start-BEFORE QUERY ')
			
			print('end-wdnjkdfjd BEFORE QUERY')

			result = db.execute("SELECT * FROM superuser WHERE designation=:designation",
			{"designation":designation}).fetchall()

			print('start-start-AFTER QUERY')
			print(result)
			print('end-wdnjkdfjd')

			for r in result:
				phone = r.phone
				email = r.email
				password = r.password
				first_name = r.first_name
				last_name = r.last_name	


			if ((person_phone_or_email == phone or person_phone_or_email == email) and person_password == password):
				print(f"inside the if condition i,e, CONDITION TRUE")
				alert_type = 'success'
				flash (f"Login Successfull! Welcome { first_name }") 

				SuperUser_ID = person_phone_or_email
				session['SuperUser_ID'] = SuperUser_ID   # CREATING A SESSION OBJECT FOR SUPERUSER

				if designation == 'Head':

					all_products = db.execute("SELECT * FROM products").fetchall()

					# FUNCTION CALL TO FIND NUMBER OF LOW AND CRITICAL ITEMS IN THE STORE
					low_items_count, critical_items_count = findItemsCount()	

					return render_template('allproductshead.html', all_products = all_products, alert_type = alert_type, low_items_count = low_items_count, critical_items_count = critical_items_count)


				elif designation == 'Store Manager':

					all_products = db.execute("SELECT * FROM products").fetchall()

					# FUNCTION CALL TO FIND NUMBER OF LOW AND CRITICAL ITEMS IN THE STORE
					low_items_count, critical_items_count = findItemsCount()

					return render_template('allproductsstoremanager.html', all_products = all_products, alert_type = alert_type , low_items_count = low_items_count, critical_items_count = critical_items_count)


				elif designation == 'Admin':

					all_registrations = db.execute("SELECT * FROM registrations").fetchall()

					# FUNCTION CALL TO FIND NUMBER OF LOW AND CRITICAL ITEMS IN THE STORE
					# low_items_count, critical_items_count = findItemsCount()

					# ADMIN WILL NOT SEE THE LIST OF PRODUCTS , IT WILL LAND ON THE allregistrations PAGE 
					# WHERE HE WILL BE ABLE TO APPROVE OR REJECT REGISTRATIONS

					return render_template('allregistrations.html', all_registrations = all_registrations, alert_type = alert_type)

			else:
				alert_type = 'error'
				flash (f"Oops, User Id and Password do not match!")
				return render_template('superuserlogin.html', alert_type = alert_type)

		else:  # IF A USER RUNS "newsuperuserlogin" PATH THROUGH URL i.e. WITHOUT FILLING THE SUPERUSER LOGIN FORM 
			return redirect(url_for('index'))


	else:  # MEANS SUPERUSER IS ALREADY LOGGED IN

		person_phone_or_email = session['SuperUser_ID'] 

		result = db.execute("SELECT * FROM superuser WHERE phone=:person_phone_or_email OR email=:person_phone_or_email",
		{"person_phone_or_email":person_phone_or_email}).fetchall()
		for r in result:
			first_name = r.first_name
			last_name = r.last_name
			designation = r.designation

		alert_type = 'info'

		flash (f" Hey { first_name }, You are already logged in FROM NEW SUPERUSER LOGIN!") 

		if designation == 'Head':

			all_products = db.execute("SELECT * FROM products").fetchall()

			# FUNCTION CALL TO FIND NUMBER OF LOW AND CRITICAL ITEMS IN THE STORE
			low_items_count, critical_items_count = findItemsCount()	

			return render_template('allproductshead.html', all_products = all_products, alert_type = alert_type, low_items_count = low_items_count, critical_items_count = critical_items_count)


		elif designation == 'Store Manager':

			all_products = db.execute("SELECT * FROM products").fetchall()

			# FUNCTION CALL TO FIND NUMBER OF LOW AND CRITICAL ITEMS IN THE STORE
			low_items_count, critical_items_count = findItemsCount()

			return render_template('allproductsstoremanager.html', all_products = all_products, alert_type = alert_type , low_items_count = low_items_count, critical_items_count = critical_items_count)


		elif designation == 'Admin':

			all_registrations = db.execute("SELECT * FROM registrations").fetchall()

			# FUNCTION CALL TO FIND NUMBER OF LOW AND CRITICAL ITEMS IN THE STORE
			# low_items_count, critical_items_count = findItemsCount()

			# ADMIN WILL NOT SEE THE LIST OF PRODUCTS , IT WILL LAND ON THE allregistrations PAGE 
			# WHERE HE WILL BE ABLE TO APPROVE OR REJECT REGISTRATIONS

			return render_template('allregistrations.html', all_registrations = all_registrations, alert_type = alert_type)
	
				



# THE ROUTE /superuserinfoupdate UPDATES THE ENTIRE BIO OF THE SUPERUSER 
# DEPENDING ON THE designation OF THE SUPERUSER

@app.route("/superuserinfoupdate",methods=["POST"])
def superuserinfoupdate():

	if 'SuperUser_ID' in session:

		first_name = request.form.get('FirstName')
		last_name = request.form.get('LastName')
		email = request.form.get('Email')
		phone = request.form.get('Phone')

		password = request.form.get('newpassword')
		confirm_password = request.form.get('cnewpassword')

		designation = request.form.get('email_Or_Phone_Or_designation')

		# FUNCTION CALL TO FIND NUMBER OF LOW AND CRITICAL ITEMS IN THE STORE
		low_items_count, critical_items_count = findItemsCount()

		if password == confirm_password:
			db.execute("UPDATE superuser SET first_name=:first_name, last_name=:last_name, email=:email, phone=:phone, password=:password WHERE designation=:designation",
			{"first_name":first_name, "last_name":last_name, "email":email, "phone":phone, "password":password, "designation":designation})
			db.commit()
			db.close()

			alert_type = 'success'
			flash (f"Your Information Has been successfully Updated { first_name }")

			if designation == 'Head':
				return render_template('updatepasswordhead.html', alert_type = alert_type, low_items_count = low_items_count, critical_items_count = critical_items_count) 
		
			elif designation == 'Store Manager':
				return render_template('updatepasswordstoremanager.html', alert_type = alert_type, low_items_count = low_items_count, critical_items_count = critical_items_count)	

			elif designation == 'Admin':
				return render_template('updatepasswordadmin.html',  alert_type = alert_type, low_items_count = low_items_count, critical_items_count = critical_items_count)	


		elif password != confirm_password:

			alert_type = 'warning'
			flash (f"Please Confirm Your Password Properly!")

			if designation == 'Head':
				return render_template('updatepasswordhead.html', alert_type = alert_type, low_items_count = low_items_count, critical_items_count = critical_items_count) 
		
			elif designation == 'Store Manager':
				return render_template('updatepasswordstoremanager.html', alert_type = alert_type, low_items_count = low_items_count, critical_items_count = critical_items_count)	

			elif designation == 'Admin':
				return render_template('updatepasswordadmin.html',  alert_type = alert_type, low_items_count = low_items_count, critical_items_count = critical_items_count)		

		else:
			alert_type = 'error'
			flash (f"OOps, Something went wrong!")

			if designation == 'Head':
				return render_template('updatepasswordhead.html', alert_type = alert_type, low_items_count = low_items_count, critical_items_count = critical_items_count) 
		
			elif designation == 'Store Manager':
				return render_template('updatepasswordstoremanager.html', alert_type = alert_type, low_items_count = low_items_count, critical_items_count = critical_items_count)	

			elif designation == 'Admin':
				return render_template('updatepasswordadmin.html',  alert_type = alert_type, low_items_count = low_items_count, critical_items_count = critical_items_count)		

	else:
		return redirect(url_for('index'))			

# THE ROUTE /superuserpasswordupdate UPDATES ONLY USER ID(email and/or phone) OF THE SUPERUSER 
# DEPENDING ON THE designation OF THE SUPERUSER

@app.route("/superuserpasswordupdate",methods=["POST"])
def superuserpasswordupdate():

	if 'SuperUser_ID' in session:

		current_password = request.form.get('current_password')

		password = request.form.get('newpassword')
		confirm_password = request.form.get('cnewpassword')

		designation = request.form.get('email_Or_Phone_Or_designation')

		# FUNCTION CALL TO FIND NUMBER OF LOW AND CRITICAL ITEMS IN THE STORE
		low_items_count, critical_items_count = findItemsCount()

		result = db.execute("SELECT * FROM superuser WHERE designation=:designation",
		{"designation":designation}).fetchall()

		for r in result:
			old_password = r.password
			first_name = r.first_name


		if old_password != current_password:
			alert_type = 'error'
			flash (f"Sorry, You entered the current password wrong!")

			if designation == 'Head':
				return render_template('updatepasswordhead.html', alert_type = alert_type, low_items_count = low_items_count, critical_items_count = critical_items_count) 
		
			elif designation == 'Store Manager':
				return render_template('updatepasswordstoremanager.html', alert_type = alert_type, low_items_count = low_items_count, critical_items_count = critical_items_count)	

			elif designation == 'Admin':
				return render_template('updatepasswordadmin.html',  alert_type = alert_type, low_items_count = low_items_count, critical_items_count = critical_items_count)

		elif old_password == current_password:		
			if password == confirm_password:

				db.execute("UPDATE superuser SET password=:password WHERE designation=:designation",
				{"password":password, "designation":designation})
				db.commit()
				db.close()

				alert_type = 'success'
				flash (f"Your Password Has been successfully Updated { first_name }")

				if designation == 'Head':
					return render_template('updatepasswordhead.html', alert_type = alert_type, low_items_count = low_items_count, critical_items_count = critical_items_count) 
			
				elif designation == 'Store Manager':
					return render_template('updatepasswordstoremanager.html', alert_type = alert_type, low_items_count = low_items_count, critical_items_count = critical_items_count)	

				elif designation == 'Admin':
					return render_template('updatepasswordadmin.html',  alert_type = alert_type, low_items_count = low_items_count, critical_items_count = critical_items_count)	


			elif password != confirm_password:

				alert_type = 'warning'
				flash (f"Please Confirm Your Password Properly!")

				if designation == 'Head':
					return render_template('updatepasswordhead.html', alert_type = alert_type, low_items_count = low_items_count, critical_items_count = critical_items_count) 
			
				elif designation == 'Store Manager':
					return render_template('updatepasswordstoremanager.html', alert_type = alert_type, low_items_count = low_items_count, critical_items_count = critical_items_count)	

				elif designation == 'Admin':
					return render_template('updatepasswordadmin.html',  alert_type = alert_type, low_items_count = low_items_count, critical_items_count = critical_items_count)		

		else:
			alert_type = 'error'
			flash (f"Oops, Something went wrong!")

			if designation == 'Head':
				return render_template('updatepasswordhead.html', alert_type = alert_type, low_items_count = low_items_count, critical_items_count = critical_items_count) 
		
			elif designation == 'Store Manager':
				return render_template('updatepasswordstoremanager.html', alert_type = alert_type, low_items_count = low_items_count, critical_items_count = critical_items_count)	

			elif designation == 'Admin':
				return render_template('updatepasswordadmin.html',  alert_type = alert_type, low_items_count = low_items_count, critical_items_count = critical_items_count)

	else:
		return redirect(url_for('index'))			

# WORK FOR ADMIN PANEL STARTS FROM HERE AND FOLLOWING CODE IS RELATED TO ADMIN PANEL

@app.route("/allfacultymembers", methods=['GET'])
def allfacultymembers():

	if 'SuperUser_ID' in session:

		all_faculty_members = db.execute(" SELECT * FROM registrations WHERE designation = 'Faculty' AND reg_status = 'Approved' ").fetchall()
		return render_template('allfacultymembers.html', all_faculty_members = all_faculty_members)

	else:
		return redirect(url_for('index'))	

# THIS IS A VERY IMPORTANT FUNCTION THAT COUNTS THE NUMBER OF FACULTY MEMBERS CURRENTLY ASSIGNED AS THE 
# TEMPORARY HEAD, FUNCTION RETURNS EITHER 0 OR 1

def temporaryHeadCount():

	temporary_head = db.execute("SELECT * FROM update_records where designation = 'Faculty' AND removed_on = 'Not-Removed'").fetchall()

	# DOING THE ACTUAL COUNTING, SINCE QUERY RETURNS ROWS
	i = 0
	count = 0
	for item in temporary_head:
		i += 1

	temporary_head_count = i

	return temporary_head_count


@app.route("/assigntemporaryhead/<faculty_phone_no>",methods=["GET", "POST"])
def assigntemporaryhead(faculty_phone_no):

	if 'SuperUser_ID' in session:

		count = temporaryHeadCount()

		if count == 1:

			temporary_head_info = db.execute("SELECT * FROM update_records where designation = 'Faculty' AND removed_on = 'Not-Removed'").fetchall()

			for r in temporary_head_info:
				temporary_head_name = r.name
				temporary_head_phone = r.phone

			alert_type = 'warning'
			flash (f"Sorry, You can not assign a new Head because { temporary_head_name } is alredy currently assigned as the Temporary head.")
			temporary_head_assignment_status = 'Currently-Assigned'

			all_faculty_members = db.execute(" SELECT * FROM registrations WHERE designation = 'Faculty' AND reg_status = 'Approved' ").fetchall()
			return render_template('allfacultymembers.html', all_faculty_members = all_faculty_members, alert_type = alert_type, temporary_head_phone = temporary_head_phone, temporary_head_assignment_status = temporary_head_assignment_status)


		elif count == 0:

			#EXTRACTING Original-Head INFORMATION TO LATER UPDATE IT AGAIN WHEN THE TEMPORARY HEAD IS REMOVED

			original_head = db.execute("SELECT * FROM superuser WHERE designation = 'Head' ").fetchall()

			for r in original_head:
				head_first_name = r.first_name
				head_last_name = r.last_name
				head_email = r.email
				head_phone = r.phone
				head_password = r.password

			#SAVING Original-Head's INFORMATION TO LATER UPDATE IT AGAIN WHEN THE TEMPORARY HEAD IS REMOVED 

			db.execute("UPDATE superuser SET first_name=:first_name, last_name=:last_name, email=:email, phone=:phone, password=:password WHERE designation = 'Original-Head' ",
			{"first_name":head_first_name,"last_name":head_last_name,"email":head_email,"phone":head_phone, "password":head_password})
			db.commit()
			db.close()	

			#EXTRACTING FACULTY'S DATA FROM regiatrations TABLE TO UPDATE HEAD'S INFO IN THE SUPERUSER TABLE

			temporary_head = db.execute("SELECT * FROM registrations WHERE phone=:faculty_phone_no",
			{"faculty_phone_no":faculty_phone_no}).fetchall()

			for r in temporary_head:
				faculty_first_name = r.first_name
				faculty_last_name = r.last_name
				faculty_email = r.email
				faculty_password = r.password

				faculty_department = r.department
				faculty_designation = r.designation

			assigned_as = 'Head'
			now = datetime.now()
			assigned_on = now.strftime("%d-%m-%Y")
			reg_time = now.strftime("%H:%M:%S")

			full_name = str(faculty_first_name) + " " + str(faculty_last_name)


			# THIS QUERY UPDATES THE superuser TABLE WITH THE DATA OF THE FACULTY BEING ASSIGNED AS HEAD

			db.execute("UPDATE superuser SET first_name=:first_name, last_name=:last_name, email=:email, phone=:phone, password=:password WHERE designation = 'Head' ",
			{"first_name":faculty_first_name,"last_name":faculty_last_name,"email":faculty_email,"phone":faculty_phone_no, "password":faculty_password})
			db.commit()
			db.close()	

			# THIS QUERY CREATES AND SAVES A NEW RECORD IN THE update_records TABLE EVERY TIME 
			# A FACULTY MEMBER IS ASSIGNED AS HEAD

			db.execute("INSERT INTO update_records(name, department, designation, email, phone, assigned_as, assigned_on) VALUES(:name, :department, :designation, :email, :phone, :assigned_as, :assigned_on)",
			{"name":full_name,"department":faculty_department,"designation":faculty_designation,"email":faculty_email, "phone":faculty_phone_no,"assigned_as":assigned_as,"assigned_on":assigned_on})
			db.commit()
			db.close()

			temporary_head_assignment_status = 'Currently-Assigned'
			temporary_head_phone = faculty_phone_no

			alert_type = 'success'
			flash (f"Success, { faculty_first_name } has been assigned as the new head!")

			all_faculty_members = db.execute(" SELECT * FROM registrations WHERE designation = 'Faculty' AND reg_status = 'Approved' ").fetchall()
			return render_template('allfacultymembers.html', all_faculty_members = all_faculty_members, alert_type = alert_type, temporary_head_phone = temporary_head_phone, temporary_head_assignment_status = temporary_head_assignment_status)


		else:
			alert_type = 'error'
			flash (f"Oops. Something went wrong!")	

			# PASSING THE FOLLOWING INFORMATION TO MAKE SURE THAT Assignment Status REMAINS CONSISTENT 
			# IF THERE IS A TEMPORARY HEAD CURRENTLY ASSIGNED

			temporary_head_info = db.execute("SELECT * FROM update_records where designation = 'Faculty' AND removed_on = 'Not-Removed'").fetchall()

			for r in temporary_head_info:
				temporary_head_name = r.name    # Name Not Needed Here Actually.
				temporary_head_phone = r.phone

			temporary_head_assignment_status = 'Currently-Assigned'	

			all_faculty_members = db.execute(" SELECT * FROM registrations WHERE designation = 'Faculty' AND reg_status = 'Approved' ").fetchall()
			return render_template('allfacultymembers.html', all_faculty_members = all_faculty_members, alert_type = alert_type, temporary_head_phone = temporary_head_phone, temporary_head_assignment_status = temporary_head_assignment_status)

	else:
		return redirect(url_for('index'))		


@app.route("/removetemporaryhead/<faculty_phone_no>",methods=["GET", "POST"])
def removetemporaryhead(faculty_phone_no):

	if 'SuperUser_ID' in session:

		count = temporaryHeadCount()

		if count == 0:

			alert_type = 'warning'
			flash (f"Sorry, No Faculty Member is Currently assigned as temporary Head as of Now!")

			all_faculty_members = db.execute(" SELECT * FROM registrations WHERE designation = 'Faculty' AND reg_status = 'Approved' ").fetchall()
			return render_template('allfacultymembers.html', all_faculty_members = all_faculty_members, alert_type = alert_type)

		elif count == 1:

			temporary_head_info = db.execute("SELECT * FROM update_records where designation = 'Faculty' AND removed_on = 'Not-Removed'").fetchall()

			for r in temporary_head_info:
				temporary_head_name = r.name    # Name Not Needed Here Actually.
				temporary_head_phone = r.phone

			if temporary_head_phone != faculty_phone_no:

				alert_type = 'warning'
				flash (f"Sorry, This Faculty Member is not Currently assigned as the temporary Head!")

				temporary_head_info = db.execute("SELECT * FROM update_records where designation = 'Faculty' AND removed_on = 'Not-Removed'").fetchall()

				for r in temporary_head_info:
					temporary_head_name = r.name    # Name Not Needed Here Actually.
					temporary_head_phone = r.phone

				temporary_head_assignment_status = 'Currently-Assigned'

				all_faculty_members = db.execute(" SELECT * FROM registrations WHERE designation = 'Faculty' AND reg_status = 'Approved' ").fetchall()
				return render_template('allfacultymembers.html', all_faculty_members = all_faculty_members, alert_type = alert_type, temporary_head_phone = temporary_head_phone, temporary_head_assignment_status = temporary_head_assignment_status)

			elif temporary_head_phone == faculty_phone_no:	

				original_head = db.execute("SELECT * FROM superuser WHERE designation = 'Original-Head'").fetchall()
				
				for r in original_head:
					head_first_name = r.first_name
					head_last_name = r.last_name
					head_email = r.email
					head_phone = r.phone
					head_password = r.password	

				#THIS QUERY UPDATES THE superuser TABLE WITH THE DATA OF THE Original-Head IN COLUMN OF Head

				db.execute("UPDATE superuser SET first_name=:first_name, last_name=:last_name, email=:email, phone=:phone, password=:password WHERE designation = 'Head' ",
				{"first_name":head_first_name,"last_name":head_last_name,"email":head_email,"phone":head_phone, "password":head_password})
				db.commit()
				db.close()	

				#THIS QUERY UPDATES THE removed_on COLUMN OF update_records TABLE WITH THE DATE 
				# ON WHICH THE FACULTY IS REMOVED FROM ITS STATUS OF TEMPORARY HEAD

				now = datetime.now()
				removed_on = now.strftime("%d-%m-%Y")
				reg_time = now.strftime("%H:%M:%S")

				db.execute("UPDATE update_records SET removed_on=:removed_on WHERE phone=:faculty_phone_no",
				{"removed_on":removed_on, "faculty_phone_no":faculty_phone_no})
				db.commit()
				db.close()

				temporary_head_assignment_status = 'Not-Assigned'
				temporary_head_phone = faculty_phone_no

				alert_type = 'success'
				flash (f"Success, { head_first_name } has been Re-Assigned as the new head!")

				all_faculty_members = db.execute(" SELECT * FROM registrations WHERE designation = 'Faculty' AND reg_status = 'Approved' ").fetchall()
				return render_template('allfacultymembers.html', all_faculty_members = all_faculty_members, alert_type = alert_type, temporary_head_phone = temporary_head_phone, temporary_head_assignment_status = temporary_head_assignment_status)

		else:
			alert_type = 'error'
			flash (f"Oops. Something went wrong!")	

			# PASSING THE FOLLOWING INFORMATION TO MAKE SURE THAT Assignment Status REMAINS CONSISTENT 
			# IF THERE IS A TEMPORARY HEAD CURRENTLY ASSIGNED AND IF CONTROL DOES NOT ENTER EITHER OF if and elif SO
			# THE PERSON WHO WAS ASSIGNED AS TEMPORARY HEAD, HIS Assignment status SHOULD STILL APPEAR 
			# AS 'currently-Assigned' BECAUSE REMOVE QUERY DID NOT RUN 

			temporary_head_info = db.execute("SELECT * FROM update_records where designation = 'Faculty' AND removed_on = 'Not-Removed'").fetchall()

			for r in temporary_head_info:
				temporary_head_name = r.name    # Name Not Needed Here Actually.
				temporary_head_phone = r.phone

			temporary_head_assignment_status = 'Currently-Assigned'	

			all_faculty_members = db.execute(" SELECT * FROM registrations WHERE designation = 'Faculty' AND reg_status = 'Approved' ").fetchall()
			return render_template('allfacultymembers.html', all_faculty_members = all_faculty_members, alert_type = alert_type, temporary_head_phone = temporary_head_phone, temporary_head_assignment_status = temporary_head_assignment_status)

	else:
		return redirect(url_for('index'))		


# THE FOLLOWING CODE FOCUSES ON THE AUTHORITY UPDATE FEATURE OF CLERK TO STORE MANAGER

@app.route("/allclerks", methods=['GET'])
def allclerks():

	if 'SuperUser_ID' in session:

		all_clerks = db.execute(" SELECT * FROM registrations WHERE designation = 'Clerk' AND reg_status = 'Approved' ").fetchall()
		return render_template('allclerks.html', all_clerks = all_clerks)

	else:
		return redirect(url_for('index'))	


# THIS IS A VERY IMPORTANT FUNCTION THAT COUNTS THE NUMBER OF CLERKS CURRENTLY ASSIGNED AS THE 
# TEMPORARY STORE MANAGER, FUNCTION RETURNS EITHER 0 OR 1

def temporaryStoreManagerCount():

	temporary_store_manager = db.execute("SELECT * FROM update_records where designation = 'Clerk' AND removed_on = 'Not-Removed'").fetchall()

	# DOING THE ACTUAL COUNTING, SINCE QUERY RETURNS ROWS
	i = 0
	count = 0
	for item in temporary_store_manager:
		i += 1

	temporary_store_manager_count = i

	return temporary_store_manager_count


@app.route("/assigntemporarystoremanager/<clerk_phone_no>",methods=["GET", "POST"])
def assigntemporarystoremanager(clerk_phone_no):

	if 'SuperUser_ID' in session:

		count = temporaryStoreManagerCount()

		if count == 1:

			temporary_store_manager_info = db.execute("SELECT * FROM update_records where designation = 'Clerk' AND removed_on = 'Not-Removed'").fetchall()

			for r in temporary_store_manager_info:
				temporary_store_manager_name = r.name
				temporary_store_manager_phone = r.phone

			alert_type = 'warning'
			flash (f"Sorry, You can not assign a new Store Manager because { temporary_store_manager_name } is already currently assigned as the Temporary Store Manager.")
			temporary_store_manager_assignment_status = 'Currently-Assigned'

			all_clerks = db.execute(" SELECT * FROM registrations WHERE designation = 'Clerk' AND reg_status = 'Approved' ").fetchall()
			return render_template('allclerks.html', all_clerks = all_clerks, alert_type = alert_type, temporary_store_manager_phone = temporary_store_manager_phone, temporary_store_manager_assignment_status = temporary_store_manager_assignment_status)


		elif count == 0:

			#EXTRACTING Original-Store-Manager INFORMATION TO LATER UPDATE IT AGAIN WHEN THE TEMPORARY STORE MANAGER IS REMOVED

			original_store_manager = db.execute("SELECT * FROM superuser WHERE designation = 'Store Manager' ").fetchall()

			for r in original_store_manager:
				store_manager_first_name = r.first_name
				store_manager_last_name = r.last_name
				store_manager_email = r.email
				store_manager_phone = r.phone
				store_manager_password = r.password

			#SAVING Original-Store-Manager's INFORMATION TO LATER UPDATE IT AGAIN WHEN THE TEMPORARY STORE MANAGER IS REMOVED 

			db.execute("UPDATE superuser SET first_name=:first_name, last_name=:last_name, email=:email, phone=:phone, password=:password WHERE designation = 'Original-Store-Manager' ",
			{"first_name":store_manager_first_name,"last_name":store_manager_last_name,"email":store_manager_email,"phone":store_manager_phone, "password":store_manager_password})
			db.commit()
			db.close()	

			#EXTRACTING CLERK'S DATA FROM regiatrations TABLE TO UPDATE STORE MANAGER'S INFO IN THE SUPERUSER TABLE

			temporary_store_manager = db.execute("SELECT * FROM registrations WHERE phone=:clerk_phone_no",
			{"clerk_phone_no":clerk_phone_no}).fetchall()

			for r in temporary_store_manager:
				clerk_first_name = r.first_name
				clerk_last_name = r.last_name
				clerk_email = r.email
				clerk_password = r.password

				clerk_department = r.department
				clerk_designation = r.designation

			assigned_as = 'Store Manager'
			now = datetime.now()
			assigned_on = now.strftime("%d-%m-%Y")
			# reg_time = now.strftime("%H:%M:%S")

			full_name = str(clerk_first_name) + " " + str(clerk_last_name)


			# THIS QUERY UPDATES THE superuser TABLE WITH THE DATA OF THE CLERK BEING ASSIGNED AS STORE MANAGER

			db.execute("UPDATE superuser SET first_name=:first_name, last_name=:last_name, email=:email, phone=:phone, password=:password WHERE designation = 'Store Manager' ",
			{"first_name":clerk_first_name,"last_name":clerk_last_name,"email":clerk_email,"phone":clerk_phone_no, "password":clerk_password})
			db.commit()
			db.close()	

			# THIS QUERY CREATES AND SAVES A NEW RECORD IN THE update_records TABLE EVERY TIME 
			# A CLERK IS ASSIGNED AS STORE MANAGER

			db.execute("INSERT INTO update_records(name, department, designation, email, phone, assigned_as, assigned_on) VALUES(:name, :department, :designation, :email, :phone, :assigned_as, :assigned_on)",
			{"name":full_name,"department":clerk_department,"designation":clerk_designation,"email":clerk_email, "phone":clerk_phone_no,"assigned_as":assigned_as,"assigned_on":assigned_on})
			db.commit()
			db.close()

			temporary_store_manager_assignment_status = 'Currently-Assigned'
			temporary_store_manager_phone = clerk_phone_no

			alert_type = 'success'
			flash (f"Success, { full_name } has been assigned as the new store manager!")

			all_clerks = db.execute(" SELECT * FROM registrations WHERE designation = 'Clerk' AND reg_status = 'Approved' ").fetchall()
			return render_template('allclerks.html', all_clerks = all_clerks, alert_type = alert_type, temporary_store_manager_phone = temporary_store_manager_phone, temporary_store_manager_assignment_status = temporary_store_manager_assignment_status)


		else:
			alert_type = 'error'
			flash (f"Oops. Something went wrong!")	

			# PASSING THE FOLLOWING INFORMATION TO MAKE SURE THAT Assignment Status REMAINS CONSISTENT 
			# IF THERE IS A TEMPORARY STORE MANAGER CURRENTLY ASSIGNED

			temporary_store_manager_info = db.execute("SELECT * FROM update_records where designation = 'Clerk' AND removed_on = 'Not-Removed'").fetchall()

			for r in temporary_store_manager_info:
				temporary_store_manager_name = r.name    # Name Not Needed Here Actually.
				temporary_store_manager_phone = r.phone

			temporary_store_manager_assignment_status = 'Currently-Assigned'	

			all_clerks= db.execute(" SELECT * FROM registrations WHERE designation = 'Clerk' AND reg_status = 'Approved' ").fetchall()
			return render_template('allclerks.html', all_clerks = all_clerks, alert_type = alert_type, temporary_store_manager_phone = temporary_store_manager_phone, temporary_store_manager_assignment_status = temporary_store_manager_assignment_status)

	else:
		return redirect(url_for('index'))		


@app.route("/removetemporarystoremanager/<clerk_phone_no>",methods=["GET", "POST"])
def removetemporarystoremanager(clerk_phone_no):

	if 'SuperUser_ID' in session:

		count = temporaryStoreManagerCount()

		if count == 0:

			alert_type = 'warning'
			flash (f"Sorry, No Clerk is Currently assigned as temporary Store Manager as of Now!")

			all_clerks = db.execute(" SELECT * FROM registrations WHERE designation = 'Clerk' AND reg_status = 'Approved' ").fetchall()
			return render_template('allclerks.html', all_clerks = all_clerks, alert_type = alert_type)

		elif count == 1:

			temporary_store_manager_info = db.execute("SELECT * FROM update_records where designation = 'Clerk' AND removed_on = 'Not-Removed'").fetchall()

			for r in temporary_store_manager_info:
				temporary_store_manager_name = r.name    # Name Not Needed Here Actually.
				temporary_store_manager_phone = r.phone

			if temporary_store_manager_phone != clerk_phone_no:

				alert_type = 'warning'
				flash (f"Sorry, This Clerk is not Currently assigned as the temporary Store Manager!")

				temporary_store_manager_info = db.execute("SELECT * FROM update_records where designation = 'Clerk' AND removed_on = 'Not-Removed'").fetchall()

				for r in temporary_store_manager_info:
					temporary_store_manager_name = r.name    # Name Not Needed Here Actually.
					temporary_store_manager_phone = r.phone

				temporary_store_manager_assignment_status = 'Currently-Assigned'

				all_clerks = db.execute(" SELECT * FROM registrations WHERE designation = 'Clerk' AND reg_status = 'Approved' ").fetchall()
				return render_template('allclerks.html', all_clerks = all_clerks, alert_type = alert_type, temporary_store_manager_phone = temporary_store_manager_phone, temporary_store_manager_assignment_status = temporary_store_manager_assignment_status)

			elif temporary_store_manager_phone == clerk_phone_no:	

				original_store_manager = db.execute("SELECT * FROM superuser WHERE designation = 'Original-Store-Manager' ").fetchall()
				
				for r in original_store_manager:
					store_manager_first_name = r.first_name
					store_manager_last_name = r.last_name
					store_manager_email = r.email
					store_manager_phone = r.phone
					store_manager_password = r.password	

				#THIS QUERY UPDATES THE superuser TABLE WITH THE DATA OF THE Original-Store-Manager IN COLUMN OF STORE MANAGER

				db.execute("UPDATE superuser SET first_name=:first_name, last_name=:last_name, email=:email, phone=:phone, password=:password WHERE designation = 'Store Manager' ",
				{"first_name":store_manager_first_name,"last_name":store_manager_last_name,"email":store_manager_email,"phone":store_manager_phone, "password":store_manager_password})
				db.commit()
				db.close()	

				#THIS QUERY UPDATES THE removed_on COLUMN OF update_records TABLE WITH THE DATE 
				# ON WHICH THE CLERK IS REMOVED FROM ITS STATUS OF TEMPORARY STORE MANAGER

				now = datetime.now()
				removed_on = now.strftime("%d-%m-%Y")
				reg_time = now.strftime("%H:%M:%S")

				db.execute("UPDATE update_records SET removed_on=:removed_on WHERE phone=:clerk_phone_no",
				{"removed_on":removed_on, "clerk_phone_no":clerk_phone_no})
				db.commit()
				db.close()

				temporary_store_manager_assignment_status = 'Not-Assigned'
				temporary_store_manager_phone = clerk_phone_no

				alert_type = 'success'
				flash (f"Success, { store_manager_first_name } has been Re-Assigned as the new store manager!")

				all_clerks = db.execute(" SELECT * FROM registrations WHERE designation = 'Clerk' AND reg_status = 'Approved' ").fetchall()
				return render_template('allclerks.html', all_clerks = all_clerks, alert_type = alert_type, temporary_store_manager_phone = temporary_store_manager_phone, temporary_store_manager_assignment_status = temporary_store_manager_assignment_status)

		else:
			alert_type = 'error'
			flash (f"Oops. Something went wrong!")	

			# PASSING THE FOLLOWING INFORMATION TO MAKE SURE THAT Assignment Status REMAINS CONSISTENT 
			# IF THERE IS A TEMPORARY STORE MANAGER CURRENTLY ASSIGNED AND IF CONTROL DOES NOT ENTER EITHER OF if and elif SO
			# THE PERSON WHO WAS ASSIGNED AS TEMPORARY STORE MANAGER, HIS Assignment status SHOULD STILL APPEAR 
			# AS 'currently-Assigned' BECAUSE REMOVE QUERY DID NOT RUN 

			temporary_store_manager_info = db.execute("SELECT * FROM update_records where designation = 'Clerk' AND removed_on = 'Not-Removed'").fetchall()

			for r in temporary_store_manager_info:
				temporary_store_manager_name = r.name    # Name Not Needed Here Actually.
				temporary_store_manager_phone = r.phone

			temporary_store_manager_assignment_status = 'Currently-Assigned'	

			all_clerks = db.execute(" SELECT * FROM registrations WHERE designation = 'Clerk' AND reg_status = 'Approved' ").fetchall()
			return render_template('allclerks.html', all_clerks = all_clerks, alert_type = alert_type, temporary_store_manager_phone = temporary_store_manager_phone, temporary_store_manager_assignment_status = temporary_store_manager_assignment_status)

	else:
		return redirect(url_for('index'))		



@app.route("/authorizationupdaterecords", methods=["GET"])
def authorizationupdaterecords():

	authorization_update_records = db.execute(" SELECT * FROM update_records ").fetchall()
	return render_template('authorizationupdaterecords.html', authorization_update_records = authorization_update_records)

# @app.route("/test")
# def test():
#     return render_template('test.html')    
# @app.route("/students")
# def students():
#     result = db.execute("SELECT * FROM student").fetchall()
#     return render_template('students.html', result = result) 