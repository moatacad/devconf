'''Import Flask'''
from flask import Flask
from flask_wtf.csrf import CSRFProtect
from flask_sqlalchemy import SQLAlchemy
'''Instantiate Flask Object'''
app=Flask(__name__,instance_relative_config=True)
csrf=CSRFProtect(app)
app.config.from_pyfile('config.py')

db=SQLAlchemy(app)

from pkg import mymodels
from pkg.myroutes import user_routes,admin_routes
