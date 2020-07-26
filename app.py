from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField
from wtforms.validators import InputRequired, Email, Length
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from datetime import datetime
import stock

app = Flask(__name__)
app.config['SECRET_KEY'] = 'Thisissupposedtobesecret!'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
Bootstrap(app)
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(15), unique=True)
    email = db.Column(db.String(50), unique=True)
    password = db.Column(db.String(80))

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class LoginForm(FlaskForm):
    username = StringField('username', validators=[InputRequired(), Length(min=4, max=15)])
    password = PasswordField('password', validators=[InputRequired(), Length(min=8, max=80)])
    remember = BooleanField('remember me')

class RegisterForm(FlaskForm):
    email = StringField('email', validators=[InputRequired(), Email(message='Invalid email'), Length(max=50)])
    username = StringField('username', validators=[InputRequired(), Length(min=4, max=15)])
    password = PasswordField('password', validators=[InputRequired(), Length(min=8, max=80)])

class Stock(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    userName = db.Column(db.String(60))
    stockName = db.Column(db.String(15))
    stockPrice = db.Column(db.Float)
    numShares = db.Column(db.Float)

class Sold(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    userName = db.Column(db.String(60))
    stockID = db.Column(db.Integer)
    num_shares = db.Column(db.Float)
    stock_price = db.Column(db.Float)

class StopOrder(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    userName = db.Column(db.String(60))
    ticker = db.Column(db.String(10))
    startingPrice = db.Column(db.Float)
    currentPrice = db.Column(db.Float)
    desiredPrice = db.Column(db.Float)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user:
            if check_password_hash(user.password, form.password.data):
                login_user(user, remember=form.remember.data)
                return redirect(url_for('stocks'))
        return '<h1>Invalid login credentials</h1>'

    return render_template('login.html', form=form)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    form = RegisterForm()

    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data, method='sha256')
        new_user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('stocks'))
        
    return render_template('signup.html', form=form)

@app.route('/addStock', methods=['POST', 'GET'])
@login_required
def addStock():
    if request.method == 'POST':
        user_name = current_user.username
        stock_name = request.form['stockName']
        stock_price = request.form['stockPrice']
        num_shares = request.form['numShares']
        new_stock = Stock(userName=user_name, stockName=stock_name, stockPrice=stock_price, numShares=num_shares)

        try:
            db.session.add(new_stock)
            db.session.commit()
            return redirect(url_for('stocks'))
        except:
            return 'Issue adding stock'
    else:
        return render_template('addStock.html')

@app.route('/stocks', methods=['POST', 'GET'])
@login_required
def stocks():
    stockList = Stock.query.order_by(Stock.id).filter(Stock.userName == current_user.username)
    soldList = Sold.query.order_by(Sold.id).filter(Sold.userName == current_user.username)
    currentPriceList = []
    indexes = []
    i = 0
    for singleStock in stockList:
        currentPriceList.append(stock.getCurrentPrice(singleStock.stockName))
        indexes.append(i)
        i+=1
    return render_template('stocks.html', stock_list=stockList, currentPrices=currentPriceList, arrayIndexes=indexes, sold_list=soldList)
    
@app.route('/sellStock', methods=['POST', 'GET'])
@login_required
def sellStock():
    if request.method == 'POST':  
        user_name = current_user.username
        stockID = request.form['id']
        stock_price = request.form['priceSold']
        num_shares = request.form['numSharesSold']
        sell_stock = Sold(userName=user_name, stockID=stockID, stock_price=stock_price, num_shares=num_shares)
        try:
            db.session.add(sell_stock)
            db.session.commit()
            return redirect(url_for('stocks'))
        except:
            return 'Issue selling stock'
    else:
        return render_template('sellStock.html')

@app.route('/logout', methods=['POST', 'GET'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/account')
@login_required
def account():
    return render_template('account.html', username=current_user.username, email=current_user.email)

@app.route('/stopOrders', methods=['POST', 'GET'])
@login_required
def stopOrders():
    ordersList = StopOrder.query.order_by(StopOrder.id).filter(StopOrder.userName == current_user.username)
    return render_template('stopOrders.html', ordersList=ordersList)

@app.route('/stopOrder', methods=['POST', 'GET'])
@login_required
def stopOrder():
    if request.method == 'POST':
        user_name = current_user.username
        ticker = request.form['stockName']
        startingPrice = float(request.form['startPrice'])
        currentPrice = float(stock.getCurrentPrice(ticker))
        if request.form['posnev'] == 'positive':
            percent = float(request.form['percentage']) * .01
            desiredPrice = (startingPrice * percent) + startingPrice
        else:
            percent = float(request.form['percentage']) * .01
            desiredPrice = startingPrice - (startingPrice * percent)
            
        new_order = StopOrder(userName=user_name, ticker=ticker, startingPrice=startingPrice, currentPrice=currentPrice, desiredPrice=desiredPrice)

        try:
            db.session.add(new_order)
            db.session.commit()
            return redirect(url_for('stopOrders'))
        except:
            return 'Issue adding order'
    else:
        return render_template('stopOrder.html')

if __name__ == '__main__':
    app.run(debug=True)