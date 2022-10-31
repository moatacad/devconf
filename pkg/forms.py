from flask_wtf import FlaskForm
from wtforms import StringField,SubmitField,TextAreaField
from wtforms.validators import DataRequired,Length
class ProductForm(FlaskForm):
  item_name=StringField('Product Name')
  item_price = StringField('Product Price')
  submit= SubmitField('Submit')

class PostForm(FlaskForm):
  title=StringField('Post Title',validators=[DataRequired(message='your post must come with a title')])
  content = TextAreaField('Content',validators=[DataRequired(message='you must supply a content'),Length(min=10,message='the content cannot be less than 10 characters')])
  submit= SubmitField('Post')

