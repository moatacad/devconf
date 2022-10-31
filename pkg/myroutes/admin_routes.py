from flask import render_template,request,flash,redirect,url_for,session
from sqlalchemy import desc
from pkg import app,db
from pkg.mymodels import User,Admin,Products,State
from pkg.forms import ProductForm
@app.route('/admin/login',methods=['POST','GET'])
def admin_login():
  if request.method == 'GET':
    return render_template('admin/admin_login.html')
  else:
    username=request.form.get('username')
    password=request.form.get('password')
    data = db.session.query(Admin).filter(Admin.admin_username==username).filter(Admin.admin_password==password).first()
    if data !=None:
      session['admin']=data.admin_id
      return redirect(url_for('admin_dashboard'))
    else:
      flash('Wrong Credentials')
      return redirect('/')
@app.route('/admin/dashboard')
def admin_dashboard():
  admin_user=session.get('admin')
  if admin_user:
    total_reg=db.session.query(User).all()
    return render_template('admin/admin_dashboard.html',total_reg=total_reg)
  else:
    return redirect(url_for('admin_login'))
@app.route('/admin/product')
def admin_addproduct():
  admin_user=session.get('admin')
  if admin_user:
    all_products=db.session.query(Products).all()
    return render_template('admin/product.html',all_products=all_products)
  else:
    return redirect(url_for('admin_login'))
@app.route('/admin/new-product',methods=['POST','GET'])
def new_product():
  admin_user=session.get('admin')
  if admin_user:
    frm=ProductForm()
    if request.method == 'GET':
      return render_template('admin/new_product.html',frm=frm)
    else:
      if frm.validate_on_submit():
        product_name=request.form.get('item_name')
        product_price=request.form.get('item_price')
        r=Products(product_name=product_name,product_price=product_price)
        db.session.add(r)
        db.session.commit()
        return redirect(url_for('admin_addproduct'))
      else:
        return render_template('admin/new_product.html',frm=frm)
  else:
    return redirect('/admin/login')
@app.route('/admin/all_registered')
def all_registered():
  admin_user=session.get('admin')
  if admin_user:
    regs=db.session.query(User,State).join(State).all()
    return render_template('admin/registrations.html',regs=regs)
  else:
    return redirect('/admin/login')
@app.route('/admin/delete/<id>')
def delete_user(id):
  admin_user=session.get('admin')
  if admin_user:
    user_del=db.session.query(User).get(id)
    db.session.delete(user_del)
    db.session.commit()
    return redirect(url_for('all_registered'))
  else:
    return redirect('/admin/login')
@app.route('/admin/details/<id>')
def details(id):
  admin_user=session.get('admin')
  if admin_user:
    user=db.session.query(User).filter(User.user_id==id).first()
    return render_template('admin/details.html',user=user)
  else:
    return redirect(url_for('admin_login'))
@app.route('/admin/logout')
def admin_logout():
  if session['admin'] !=None:
    session.pop('admin')
  return redirect(url_for('home'))