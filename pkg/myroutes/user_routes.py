import os,random,string,requests
from flask import render_template,request,flash,redirect,make_response,url_for,session,jsonify,json
from werkzeug.security import generate_password_hash,check_password_hash
from pkg import app,db
from sqlalchemy import asc
from pkg.forms import PostForm
from pkg.mymodels import Comments, Post, Purchases, User,State,Products,Lga,Transaction
@app.route('/')
def home():
  # response=requests.get('http://127.0.0.1:8085/api/v1/listall')
  return render_template('user/home.html')
@app.route('/dashboard')
def user_dashboard():
  loggedin=session.get('loggedin')
  if loggedin!=None:
    records=db.session.query(User).filter(User.user_id==loggedin).first()
    name=f'{records.user_fname} {records.user_lname}'
    email=f'{records.user_email}'
    return render_template('user/user_dashboard.html',records=records,name=name,email=email)
  else:
    return redirect(url_for('user_login'))
@app.route('/paystack_reponse')
def paystack_response():
    '''This is the callback_url we set in our paystack dashboard for paystack to send us response'''
    userid = session.get('loggedin')
    if userid != None:
        refno = session.get('tref')

        headers = {"Content-Type": "application/json","Authorization":"Bearer sk_test_3c5244cfb8965dd000f07a4cfa97185aab2e88d5"}

        response = requests.get(f"https://api.paystack.co/transaction/verify/{refno}",headers=headers)
               
        '''Pick the JSON within the response object above '''
        rspjson = response.json()
        '''UPDATE YOUR TABLES. THE END''' 
        if rspjson['data']['status'] =='success':
            amt = rspjson['data']['amount']
            ipaddress = rspjson['data']['ip_address']
            t = Transaction.query.filter(Transaction.trx_refno==refno).first()
            t.trx_status = 'paid'
            db.session.add(t)
            db.session.commit()
            return "Payment Was Successful"  #update database and redirect them to the feedback page
        else:
            t = Transaction.query.filter(Transaction.trx_refno==refno).first()
            t.trx_status = 'failed'
            db.session.add(t)
            db.session.commit()
            return "Payment Failed" 
    else:
        return redirect('/login')
@app.route('/login',methods=['POST','GET'])
def user_login():
  if request.method=='GET':
    return render_template('user/user_login.html')
  else:
    email=request.form.get('email')
    password=request.form.get('password')
    records=db.session.query(User).filter(User.user_email==email).first()
    if records and check_password_hash(records.user_pass,password):
      session['loggedin']=records.user_id
      return redirect(url_for('user_dashboard'))
    else:
      flash('Wrong Credentials')
      return redirect(url_for('user_login'))
@app.route('/signup',methods=['POST','GET'])
def user_signup():
  if request.method=='GET':
    return render_template('user/regform.html')
  else:
    firstname=request.form.get('fname')
    lastname=request.form.get('lname')
    emailadd=request.form.get('email')
    password=request.form.get('pwd')
    hashed_p=generate_password_hash(password)
    u =User(user_email=emailadd,user_fname=firstname,user_lname=lastname,user_pass=hashed_p)
    db.session.add(u)
    db.session.commit()
    return redirect(url_for('user_login'))
@app.route('/user_logout')
def user_logout():
  if session.get('loggedin')!=None:
    session.pop('loggedin')
  return redirect(url_for('home'))
@app.route('/user_buy',methods=['GET','POST'])
def user_buy():
  records=db.session.query(User).filter(User.user_id==session.get('loggedin')).first()
  if session.get('loggedin') != None:
        if request.method =="GET":
            prods=Products.query.all()
            loggedin = session.get('loggedin')
            return render_template('user/store.html',prods=prods,loggedin=loggedin)
        else:
            '''Retrieve form data, and insert into purchases table'''
            userid = session.get('loggedin')
            
            '''Generate a transation ref no and keep it in a session variable'''
            refno = int(random.random() * 1000000000)
            session['tref'] = refno

            '''Insert into Transaction Table'''
            trans = Transaction(trx_user=userid,trx_refno=refno,trx_status='pending',trx_method='cash')            
            db.session.add(trans) 
            db.session.commit()
            '''Get the id from transaction table and insert into purchases table'''
            id = trans.trx_id
           
            productid = request.form.getlist('productid') #[1,2,3]
            total_amt = 0
            for p in productid:
                pobj = Purchases(pur_userid=userid,pur_productid=p,pur_trxid=id)
                db.session.add(pobj)
                db.session.commit() 
                product_amt = pobj.proddeets.product_price
                total_amt = total_amt+ product_amt

            '''UPDATE the total amount on transaction table with product_amt'''

            trans.trx_totalamt = total_amt
            db.session.commit()
           
            return redirect('/confirm') 
  else:
        return redirect('/login')

@app.route('/confirm')
def confirm_purchases():
    """The button here takes them to Paystack"""
    userid = session.get('loggedin')
    transaction_ref = session.get('tref')
    if userid !=None:
        '''Retrieve all the things this user has selected from Purchases table
        save it in a variable and Then send it to the template'''        
        data = db.session.query(Purchases).join(Transaction).filter(Transaction.trx_refno==transaction_ref).all()       
        return render_template('user/confirm_purchases.html',data=data)
    else:
        return redirect('/login')
@app.route('/paystack_step1',methods=['POST'])
def paystack():
  if session.get('loggedin')!=None:
    url='https://api.paystack.co/transaction/initialize'
    userdeets=User.query.get(session.get('loggedin'))
    deets=Transaction.query.filter(Transaction.trx_refno==session.get('tref')).first()
    data={'email':userdeets.user_email,'amount':deets.trx_totalamt*100,'reference':deets.trx_refno}
    headers={'Content_Type':'application/json','Authorization':'Bearer sk_test_fb58555bf41a08607aca1beff850bae08805faa7'}
    response = requests.post(url, headers=headers, data=json.dumps(data))
    rspjson = json.loads(response.text) 

    return redirect(rspjson['data']['authorization_url'])
  else:
    return redirect(url_for('user_login'))
@app.route('/social')
def social():
  if session.get('loggedin')!=None:
    records=db.session.query(User).filter(User.user_id==session.get('loggedin')).first()
    allposts=db.session.query(Post).all()
    return render_template('user/conversations.html',allposts=allposts,records=records)
  else:
    return redirect(url_for('user_login'))
@app.route('/makepost',methods=['POST','GET'])
def makepost():
  if session.get('loggedin')!=None:
    p=PostForm()
    if request.method=='GET':
      records=db.session.query(User).filter(User.user_id==session.get('loggedin')).first()
      allposts=db.session.query(Post).all()
      return render_template('user/makepost.html',p=p,records=records)
    else:
      if p.validate_on_submit()== True:
        title=p.title.data
        content=p.content.data
        records=Post(post_content=content,post_title=title,post_userid=session.get('loggedin'))
        db.session.add(records)
        x=db.session.commit()
        if records.post_id:
          flash('Post Successfully Created')
          return redirect(url_for('social'))
        else:
          flash('oops Something Happened')
      else:
        return render_template('user/makepost.html')
  else:
    return redirect(url_for('user_login'))
@app.route('/user_profile',methods=['POST','GET'])
def user_profile():
  if session.get('loggedin')!=None:
    if request.method=='GET':
      records=db.session.query(User).filter(User.user_id==session.get('loggedin')).first()
      states=db.session.query(State).all()
      return render_template('user/user_update_profile.html',records=records,state=states)
    else:
      file_obj=request.files['file']
      allowed=['.jpg','.png','.jpeg']
      newfilename=''
      if file_obj.filename!='':
        original_name=file_obj.filename
        filename,ext=os.path.splitext(original_name)
        if ext.lower() in allowed:
          xter_list=random.sample(string.ascii_letters,12)
          newfilename=''.join(xter_list)+ext
          file_obj.save('pkg/static/uploads/'+newfilename)
      fname=request.form.get('fname')
      lname=request.form.get('lname')
      state=request.form.get('state')
      phone=request.form.get('phone')
      user=db.session.query(User).filter(User.user_id==session.get('loggedin')).first()
      user.user_fname=fname
      user.user_lname=lname
      user.user_state=state
      user.user_phone=phone
      user.user_image=newfilename
      db.session.commit()
      flash('Update has been successful')
      return redirect(url_for('user_profile'))
  else:
    return redirect(url_for('user_login'))
@app.route('/getlga')
def getlga():
  stateid = request.args.get('stateid')
  rows=db.session.query(Lga).filter(Lga.state_id==stateid).all()
  if rows:
    lgalist=''
    for i in rows:
      lgalist=lgalist +f"<option class='{i.lga_id}'>{i.lga_name}</option>"
    return lgalist
  else:
    return ' no value'
@app.route('/comments/<id>',methods=['GET','POST'])
def comments_details(id):
  if request.method == 'GET':
    records=db.session.query(User).filter(User.user_id==session.get('loggedin')).first()
    post=db.session.query(Post).get_or_404(id)
    comment=db.session.query(Comments).filter(Comments.comment_postid==id).all()
    return render_template('user/commentdetails.html',post=post,records=records,comment=comment)
  else:
    com=request.form.get('comment')
    userid=session.get('loggedin')
    comment=Comments(comment_by=userid,comment_content=com,comment_postid=id)
    db.session.add(comment)
    db.session.commit()
    data2return={'madeby':comment.userdeets.user_fname,'comment':com}
    data_json=jsonify(data2return)
    return data_json

@app.route('/ajax/chk_email_form')
def chk_email_form():
  records=db.session.query(User).filter(User.user_id==session.get('loggedin')).first()
  return render_template('user/check_email.html',records=records)
@app.route('/ajax/chk_email',methods=['POST','GET'])
def chk_email():
  useremail=request.form.get('email')
  row=db.session.query(User).filter(User.user_email==useremail).first()
  if row:
    return 'email address in use already'
  else:
    return 'email address available'