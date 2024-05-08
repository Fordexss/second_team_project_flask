from flask import Flask, render_template, redirect, url_for, flash, request, make_response
from datetime import timedelta
from db.db import User, Session
from helpers import get_crypto_data, get_crypto_news, get_crypto_price, get_top_crypto, custom_enumerate, ConverterForm, \
    RegistrationForm, LoginForm, UpdateProfileForm

app = Flask(__name__)
session = Session()

app.config['SECRET_KEY'] = 'CryptoInformer'


# Основний функціонал

@app.route('/')
def index():
    news = get_crypto_news()
    if news:
        news_f_temp = []
        for article in news:
            title = article['title']
            url = article['url']
            news_f_temp.append((title, url))
    top_crypto = get_top_crypto()
    if top_crypto:
        for crypto in top_crypto:
            crypto['name'] = f"{crypto['name']} ({crypto['symbol']})"
        return render_template('index.html', top_crypto=top_crypto, enumerate=custom_enumerate, news=news_f_temp)
    else:
        return 'Не вдалося отримати дані про топ-100 криптовалют'


@app.route('/news')
def crypto_news():
    news = get_crypto_news()
    if news:
        news_f_temp = []
        for article in news:
            title = article['title']
            url = article['url']
            news_f_temp.append((title, url))
        print(news_f_temp)
        return render_template('news.html', news=news_f_temp)
    else:
        return 'На жаль, не вдалося отримати новини'


@app.route('/login/', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = session.query(User).filter_by(email=email).first()
        if user:
            if request.cookies.get('user_id') == str(user.id):
                flash('Ви вже увійшли в обліковий запис. Будь ласка, вийдіть перед спробою знову увійти.', 'info')
                return render_template('login.html', form=form)
            if user.password == password:
                flash('Ви успішно увійшли в обліковий запис', 'success')
                response = make_response(redirect(url_for('index')))
                cookie_max_age = timedelta(days=3).total_seconds()
                response.set_cookie('user_id', str(user.id), max_age=cookie_max_age)
                return response
            else:
                flash('Неправильний пароль або електронна пошта', 'error')
        else:
            flash('Неправильний пароль або електронна пошта', 'error')

    return render_template('login.html', form=form)


@app.route('/registration/', methods=['GET', 'POST'])
def registration():
    if request.method == 'POST':
        username = request.form.get('nickname')
        email = request.form.get('email')
        password = request.form.get('password')

        existing_username = session.query(User).filter_by(nickname=username).first()
        if existing_username:
            flash("Користувач з таким ім'ям вже існує", category='error')
            return redirect(url_for('registration'))

        existing_email = session.query(User).filter_by(email=email).first()
        if existing_email:
            flash("Користувач з такою поштою вже існує", category='error')
            return redirect(url_for('registration'))

        new_user = User(nickname=username, email=email, password=password)
        session.add(new_user)
        session.commit()

        flash('Реєстрація пройшла успішно!', 'success')
        return redirect(url_for('login'))

    form = RegistrationForm()
    return render_template('registration.html', form=form)


@app.route('/profile', methods=['GET', 'POST'])
def profile():
    form = UpdateProfileForm()
    user_id = request.cookies.get('user_id')
    if user_id:
        user = session.query(User).filter_by(id=user_id).first()
        if user:
            if form.validate_on_submit():
                user.nickname = form.nickname.data
                user.email = form.email.data
                if form.password.data:
                    user.password = form.password.data
                session.commit()
                flash('Профіль успішно оновлено', 'success')
                return redirect(url_for('profile'))
            form.nickname.data = user.nickname
            form.email.data = user.email
            return render_template('profile.html', form=form)
    flash('Будь ласка, увійдіть у свій аккаунт', 'error')
    return redirect(url_for('login'))


@app.route('/update_profile', methods=['POST'])
def update_profile():
    form = UpdateProfileForm(request.form)
    user_id = request.cookies.get('user_id')
    if user_id:
        user = session.query(User).filter_by(id=user_id).first()
        if user and form.validate():
            user.nickname = form.nickname.data
            user.email = form.email.data
            if form.password.data:
                user.password = form.password.data
            session.commit()
            flash('Профіль успішно оновлено', 'success')
            return redirect(url_for('profile'))
    flash('Щось пішло не так, спробуйте ще раз', 'error')
    return redirect(url_for('profile'))


@app.route('/converter/', methods=['GET', 'POST'])
def converter():
    form = ConverterForm()
    if request.method == 'GET':
        top_crypto = get_top_crypto()
        if top_crypto:
            form.from_crypto.choices = []
            form.to_crypto.choices = []
            for crypto in top_crypto:
                form.from_crypto.choices.append((crypto['symbol'], crypto['symbol']))
                form.to_crypto.choices.append((crypto['symbol'], crypto['symbol']))
        return render_template('converter.html', form=form)
    else:
        from_crypto = request.form.get('from_crypto')
        amount = int(request.form.get('amount'))
        to_crypto = request.form.get('to_crypto')
        price = get_crypto_price(from_crypto, to_crypto)
        if price:
            price_f = price * amount
        return render_template('converted.html', from_crypto=from_crypto, amount=amount, to_crypto=to_crypto,
                               price_f=price_f)


# Додатково

@app.route('/<pair>')
def get_symbol_price(pair):
    currencies = pair.split('_')
    if len(currencies) == 2:
        base = currencies[0]
        symbol = currencies[1]
        price = get_crypto_price(base, symbol)
        if price:
            return f'Ціна {base.upper()} до {symbol.upper()}: {price} {symbol.upper()}'
    return 'Даних не знайдено'


@app.route('/<symbol>')
def get_crypto_info(symbol):
    crypto_data = get_crypto_data(symbol)
    if crypto_data:
        symbol = crypto_data['symbol']
        name = crypto_data['name']
        price = crypto_data['quote']['USD']['price']
        percent_change_1h = crypto_data['quote']['USD']['percent_change_1h']
        percent_change_24h = crypto_data['quote']['USD']['percent_change_24h']
        percent_change_7d = crypto_data['quote']['USD']['percent_change_7d']
        return render_template('crypto_info.html', symbol=symbol, name=name, price=price,
                               percent_change_1h=percent_change_1h, percent_change_24h=percent_change_24h,
                               percent_change_7d=percent_change_7d)
    else:
        return 'Дані не знайдено'


if __name__ == '__main__':
    app.run(debug=True)
