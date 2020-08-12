from flask import Flask, render_template, request, redirect, url_for, jsonify, flash
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from datetime import datetime
import math, random 
from pymsgbox import *
import easygui

app = Flask(__name__)
app.secret_key = "super secret key"
DATABASE_URL = "postgres://wainhlvxrgqwoo:9902be4ffc31450a1e9924f03879d1788cfb7fa659ae511f16223d4ef9c351c8@ec2-3-223-21-106.compute-1.amazonaws.com:5432/d5nru0s34hfo11"

# Set up database
engine = create_engine(DATABASE_URL)
db = scoped_session(sessionmaker(bind=engine))

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


brand = {
	'0'  : 'Select Brand',
	'1'  : 'Brand A',
	'2'  : 'Barnd B',
	'3'  : 'Brand C',
	'4'  : 'Brand D',
	'5'  : 'Barnd E',
	'6'  : 'Brand F',
	'7'  : 'Brand G',
	'8'  : 'Barnd H',
	'9'  : 'Brand I',
	
}

category_items = {}

@app.route("/addproduct")
def addproduct():
	result = db.execute("SELECT * FROM category").fetchall()
	for r in result:
		category_code = r.category_code
		category_name = r.category_name
		category_items[str(category_code)] = category_name
	return render_template('addproduct.html', category_items = category_items)


@app.route("/addnewproduct",methods=["POST"])
def addnewproduct():
	
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
		return render_template('addproduct.html', alert_type = alert_type, category_items = category_items)


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
		return render_template('addproduct.html', alert_type = alert_type, category_items = category_items)

	else:
		alert_type = 'error'
		flash (f"Oops, Something went wrong!")	
		return render_template('addproduct.html', alert_type = alert_type, category_items = category_items)		

@app.route("/")
def index():
	return render_template('index.html')

@app.route("/signup")
def signup():
	return render_template('signup.html', department = department)   

@app.route("/newregistration",methods=["POST"])
def newregistration():
	
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
			flash( f"Your rregistration request has been successfully submitted")
			return render_template('signup.html', alert_type = alert_type, department = department)

		elif password != cpassword:
			alert_type = 'warning'
			flash( f"Please Confirn Your Pasword Properly!")
			return render_template('signup.html', alert_type = alert_type, department = department)
				
	else:
		alert_type = 'error'
		flash (f"Oops, Something went wrong!")	
		return render_template('signup.html', alert_type = alert_type, department = department)			

@app.route("/allregistrations")
def allregistrations():
	all_registrations = db.execute("SELECT * FROM registrations").fetchall()
	return render_template('allregistrations.html', all_registrations = all_registrations)

@app.route("/acceptregistration/<person_phone_no>",methods=["GET", "POST"])
def acceptregistration(person_phone_no):

	now = datetime.now()
	confirmation_date = now.strftime("%d-%m-%Y")
	confirmation_time = now.strftime("%H:%M:%S")

	new_status = 'Approved'
	
	db.execute("UPDATE registrations SET reason = NULL, reg_status=:new_status, confirmed_on=:confirmed_on WHERE phone=:phone",
	{"new_status":new_status, "confirmed_on":confirmation_date, "phone":person_phone_no})
	db.commit()
	db.close()
	return redirect(url_for('allregistrations'))



@app.route("/rejectregistration",methods=["GET", "POST"])
def rejectregistration():

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


@app.route("/login")
def login():
	return render_template('login.html') 

@app.route("/newlogin",methods=["POST"])
def newlogin():

	person_phone_or_email = request.form.get('EPhone')
	person_password = request.form.get('Password')

	# DON'T FORGET TO ADD  DIFFERENT DESTINATIONS ON DIFFERENT LOGINS BASED ON "designation" VARIABLE
	login_as = request.form.get('Designation')

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
				# print(f"Check 5 {registration_status}")
				if ((person_phone_or_email == phone or person_phone_or_email == email) and person_password == password):
					alert_type = 'success'
					flash (f"Login Successfull! Welcome { first_name }") 
					# return render_template('login.html', alert_type = alert_type)
					all_products = db.execute("SELECT * FROM products").fetchall()
					return render_template('allproductsuser.html', all_products = all_products, alert_type = alert_type, first_name = first_name, last_name = last_name, department = department, registered_as = registered_as, userid = email)
					
		elif login_as != registered_as:
			alert_type = 'error'
			flash (f"Sorry { first_name }, you can not login as { login_as } because you are registered as { registered_as }.")
			return render_template('login.html', alert_type = alert_type)		

	alert_type = 'error'
	flash (f"Oops, User Id and Password do not match!")	
	return render_template('login.html', alert_type = alert_type)	




@app.route("/homeredirect",methods=["POST"])
def homeredirect():

	user_email_or_phone = request.form.get('user_email_or_phone')

	result = db.execute("SELECT * FROM registrations WHERE phone=:user_email_or_phone OR email=:user_email_or_phone",
	{"user_email_or_phone":user_email_or_phone}).fetchall()
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
	last_name = last_name, department = department, registered_as = registered_as, userid = email)	




@app.route("/updatepass")
def updatepass():
	return render_template('updatepass.html') 


@app.route("/updatepassword")
def updatepassword():
	return render_template('updatepassword.html')

@app.route("/passwordupdate",methods=["POST"])
def passwordupdate():
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


@app.route("/storemanager",methods=["POST", "GET"])
def storemanager():
	return render_template('store-mgr.html') 


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


#   return render_template('store-mgr.html', Unique_code = Unique_code) 

#     # newcat = request.form.get('Newcat')
#     # cattype = request.form.get('Cattype')



@app.route("/addnewcategory",methods=["POST"])
def addnewcategory():
	
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
			return render_template('store-mgr.html', alert_type = alert_type)
	
		elif(result == []):
			db.execute("INSERT INTO category(category_name, category_type, lowlevel_qty, critical_level_qty, category_code) VALUES(:category_name, :category_type, :lowlevel_qty, :critical_level_qty, :category_code)",
			{"category_name":category_name,"category_type":category_type,"lowlevel_qty":lowlevel_qty,"critical_level_qty":critical_level_qty,"category_code":category_code})
			db.commit()
			db.close()
			alert_type = 'success'
			flash( f"New category { category_name } has been successfully added!")
			return render_template('store-mgr.html', alert_type = alert_type)

	alert_type = 'error'
	flash (f"Oops, Something went wrong!")	
	return render_template('store-mgr.html', alert_type = alert_type)


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

@app.route("/allproducts",methods=["POST", "GET"])
def allproducts():
	all_products = db.execute("SELECT * FROM products").fetchall()
	return render_template('allproducts.html', all_products = all_products)


@app.route("/criticalitems",methods=["GET"])
def criticalitems():
	critical_items = db.execute("SELECT * FROM products WHERE qty_available <= critical_level_qty").fetchall()
	return render_template('criticalitems.html', critical_items = critical_items)


@app.route("/lowitems",methods=["GET"])
def lowitems():
	low_items = db.execute("SELECT * FROM products WHERE qty_available <= lowlevel_qty").fetchall()
	return render_template('lowitems.html', low_items = low_items)	


@app.route("/issueditems",methods=["GET"])
def issueditems():
	issued_items = db.execute("SELECT * FROM requests WHERE product_issued_on != 'Not-issued'").fetchall()
	return render_template('issueditems.html', issued_items = issued_items)	

@app.route("/userissueditems",methods=["GET","POST"])
def userissueditems():

	person_phone_or_email = request.form.get('email_Or_Phone')

	result = db.execute("SELECT * from registrations WHERE phone=:person_phone_or_email OR email=:person_phone_or_email",
	{"person_phone_or_email":person_phone_or_email}).fetchall()

	for r in result:
		first_name = r.first_name
		last_name = r.last_name

	full_name = str(first_name)	+ " " + str(last_name)	

	issued_items = db.execute("SELECT * FROM requests WHERE product_issued_on != 'Not-issued' AND requested_by=:full_name",
	{"full_name":full_name}).fetchall()

	return render_template('userissueditems.html', issued_items = issued_items)


@app.route("/returneditems",methods=["GET"])
def returneditems():
	returned_items = db.execute("SELECT * FROM requests WHERE product_type != 'Consumable' AND product_issued_on != 'Not-issued' ").fetchall()
	return render_template('returneditems.html', returned_items = returned_items)	

@app.route("/userreturneditems",methods=["GET","POST"])
def userreturneditems():

	person_phone_or_email = request.form.get('email_Or_Phone')

	result = db.execute("SELECT * from registrations WHERE phone=:person_phone_or_email OR email=:person_phone_or_email",
	{"person_phone_or_email":person_phone_or_email}).fetchall()

	for r in result:
		first_name = r.first_name
		last_name = r.last_name

	full_name = str(first_name)	+ " " + str(last_name)	

	returned_items = db.execute("SELECT * FROM requests WHERE product_type != 'Consumable' AND product_issued_on != 'Not-issued' AND requested_by=:full_name",
	{"full_name":full_name}).fetchall()

	return render_template('userreturneditems.html', returned_items = returned_items)

@app.route("/userrequesteditems",methods=["POST", "GET"])
def userrequesteditems():

	person_phone_or_email = request.form.get('email_Or_Phone')

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

@app.route("/addrequest",methods=["GET", "POST"])
def addrequest():

	now = datetime.now()
	request_date = now.strftime("%d-%m-%Y")
	request_time = now.strftime("%H:%M:%S")

	first_name = request.form.get('first_name')
	last_name = request.form.get('last_name')

	requested_by = str(first_name) + " " + str(last_name)

	department = request.form.get('department')
	designation = request.form.get('registered_as')

	product_id = request.form.get('product_id')
	add_this_produt = db.execute("SELECT * FROM products WHERE id=:product_id",
	{"product_id":product_id}).fetchall()
	db.commit()
	db.close()

	for r in add_this_produt:
		product_name   = r.product_name
		product_code   = r.product_code
		qty_available  = r.qty_available
		product_type   = r.product_type
		lowlevel_qty   = r.lowlevel_qty
		critical_level_qty = r.critical_level_qty




	# DON'T FORGET TO ADD THE NAME OF PERSON MAKING THE REQUEST AND THE  QTY REQUESTED

	requested_qty = request.form.get('Quantity')
	# requested_by = ?????

	# NAME OF PERSON REQUESTING ITEM AND QUQNTITY TO BE ADDED BETWEEN THESE COMMENTS

	# if int(requested_qty) > qty_available:
	# 	alert(text='Requested quantity can not be more than Available quantity!', title='Warning!', button='OK')
	# 	easygui.msgbox('This is a basic message box.', 'Title Goes Here')
	# 	<script>
	# 	alert("Requested quantity can not be more than Available quantity!")
	# 	</script>

	# print('STARTTTTT')
	# print(requested_by)
	# print(department)
	# print(designation)
	# print('ENDDD')
	
	db.execute("INSERT INTO requests(product_name, product_code, qty_available, product_type, lowlevel_qty, critical_level_qty, requested_by, requested_qty, request_date, department, designation) VALUES(:product_name, :product_code, :qty_available, :product_type, :lowlevel_qty, :critical_level_qty, :requested_by, :requested_qty, :request_date, :department, :designation)",
	{"product_name":product_name,"product_code":product_code,"qty_available":qty_available,"product_type":product_type, "lowlevel_qty":lowlevel_qty,"critical_level_qty":critical_level_qty, "requested_by":requested_by, "requested_qty":requested_qty, "request_date":request_date, "department":department, "designation":designation})
	db.commit()
	db.close()    

	# return f"Product Request Added"
	all_products = db.execute("SELECT * FROM products").fetchall()
	return render_template('allproductsuser.html', all_products = all_products, first_name = first_name, last_name = last_name, department = department, registered_as = designation)
	


@app.route("/deleterequest/<product_code>",methods=["GET", "POST"])
def deleterequest(product_code):

	# now = datetime.now()
	# leaving_time = now.strftime("%H:%M:%S")

	# DELETE QUERY MUST ALSO INCLUDE THE NAME OF PERSON MAKING THE DELETE REQUEST
	#NAME OF PERSON WILL BE TAKEN AT LOGIN TIME FROM HIS PHONE NUMBER
	
	db.execute("DELETE from requests WHERE product_code=:product_code",
	{"product_code":product_code})
	db.commit()
	db.close()
	return redirect(url_for('allproducts'))

	# DON'T FORGET TO ADD THE NAME OF PERSON MAKING THE DELETE REQUEST


@app.route("/allcategories",methods=["POST", "GET"])
def allcategories():
	all_categories = db.execute("SELECT * FROM category").fetchall()
	return render_template('allcategories.html', all_categories = all_categories)


@app.route("/allrequests")
def allrequests():
	all_requests = db.execute("SELECT * FROM requests").fetchall()
	return render_template('allrequests.html', all_requests = all_requests)  


@app.route("/acceptrequest/<product_request_id>",methods=["GET", "POST"])
def acceptrequest(product_request_id):

	# UPDATE QUERY MUST ALSO INCLUDE THE NAME OF PERSON MAKING THE UPDATE REQUEST
	# NAME OF PERSON WILL BE TAKEN AT LOGIN TIME FROM HIS PHONE NUMBER

	new_status = 'Approved'
	
	db.execute("UPDATE requests SET reason = NULL, request_status=:new_status WHERE id=:product_request_id",
	{"product_request_id":product_request_id, "new_status":new_status})
	db.commit()
	db.close()
	return redirect(url_for('allrequests'))


@app.route("/rejectrequest",methods=["GET", "POST"])
def rejectrequest():

	# now = datetime.now()
	# leaving_time = now.strftime("%H:%M:%S")

	product_request_id= request.args.get('Product_request_id')
	rejection_reason = request.args.get('Reason')

	# DELETE QUERY MUST ALSO INCLUDE THE NAME OF PERSON MAKING THE DELETE REQUEST
	#NAME OF PERSON WILL BE TAKEN AT LOGIN TIME FROM HIS PHONE NUMBER
	
	
	new_status = 'Not-Approved'

	db.execute("UPDATE requests SET request_status=:new_status, reason=:reason WHERE id=:product_request_id",
	{"product_request_id":product_request_id, "new_status":new_status, "reason":rejection_reason})
	db.commit()
	db.close()

	# print('START')
	# print(product_code)
	# print(rejection_reason)
	# print('ENDDD')

	return redirect(url_for('allrequests'))

	# DON'T FORGET TO ADD THE NAME OF PERSON MAKING THE DELETE REQUEST    


@app.route("/issueproduct/<product_request_id>",methods=["GET", "POST"])
def issueproduct(product_request_id):

	now = datetime.now()
	product_issue_date = now.strftime("%d-%m-%Y")
	product_issue_time= now.strftime("%H:%M:%S")

	result = db.execute("SELECT * from requests WHERE id=:product_request_id",
	{"product_request_id":product_request_id}).fetchall()

	for r in result:
		request_status = r.request_status
		print(request_status)

	if request_status == 'Approved':
		db.execute("UPDATE requests SET product_issued_on=:product_issued_on WHERE id=:product_request_id",
		{"product_issued_on":product_issue_date, "product_request_id":product_request_id})
		db.commit()
		db.close()
		return redirect(url_for('allrequests'))

	elif request_status == 'Not-Approved':
		alert_type = 'error'
		flash (f"Sorry, This request has been Rejected!")
		all_requests = db.execute("SELECT * FROM requests").fetchall()
		return render_template('allrequests.html', all_requests = all_requests, alert_type = alert_type)

	elif request_status == 'Pending':
		alert_type = 'warning'
		flash (f"Sorry, This request has not been approved yet!")
		all_requests = db.execute("SELECT * FROM requests").fetchall()
		return render_template('allrequests.html', all_requests = all_requests, alert_type = alert_type)

	else:
		alert_type = 'error'
		flash (f"Oops, Something went wrong!")	
		all_requests = db.execute("SELECT * FROM requests").fetchall()
		return render_template('allrequests.html', all_requests = all_requests, alert_type = alert_type)


@app.route("/returnproduct/<product_request_id>/<product_issued_on>",methods=["GET", "POST"])
def returnproduct(product_request_id,product_issued_on):

	now = datetime.now()
	product_return_date = now.strftime("%d-%m-%Y")
	product_return_time= now.strftime("%H:%M:%S")

	if product_issued_on == 'Not-issued':
		alert_type = 'error'
		flash (f"Sorry, This product was never issued!")	
		all_requests = db.execute("SELECT * FROM requests").fetchall()
		return render_template('allrequests.html', all_requests = all_requests, alert_type = alert_type)

	elif product_issued_on != 'Not-issued':
		db.execute("UPDATE requests SET returned_on=:product_returned_on WHERE id=:product_request_id",
		{"product_returned_on":product_return_date, "product_request_id":product_request_id})
		db.commit()
		db.close()
		return redirect(url_for('allrequests'))	

	else:
		alert_type = 'error'
		flash (f"Oops, Something went wrong!")	
		all_requests = db.execute("SELECT * FROM requests").fetchall()
		return render_template('allrequests.html', all_requests = all_requests, alert_type = alert_type)				

# @app.route("/test")
# def test():
#     return render_template('test.html')    
# @app.route("/students")
# def students():
#     result = db.execute("SELECT * FROM student").fetchall()
#     return render_template('students.html', result = result) 