from collections import namedtuple
from os import urandom
from flask import *
from flask_login import *
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from werkzeug.security import generate_password_hash, check_password_hash
from Login.User import User

db = SQLAlchemy()
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:hej123@localhost:3306/dbkursen'
app.config["SECRET_KEY"] = urandom(20)  # TEST
db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
user = User()


@login_manager.user_loader
def load_user(user_id):
    return User.getUser(user)


@app.route('/')
def home():
    data = {
        'title': 'Non-alcoholic Beer Store',
        'welcome_message': 'Welcome to the Non-alcoholic Beer Store!',
        'user': load_users(),
        'footer_text': 'Service for Non-alcoholic Beer Store. All rights reserved.'
    }
    return render_template('index.html', **data)


def load_users():
    if current_user.is_authenticated:
        return User.getFirstName(user) + ' ' + User.getLastName(user)
    else:
        return "Guest"


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == "POST":
        useremail = request.form.get("email")
        password = request.form.get("password")
        query = "SELECT * FROM user WHERE user.email = :useremail"
        connection = db.engine.connect()
        result = connection.execute(text(query), {'useremail': useremail})
        connection.close()
        for row in result:
            userid = row[0]
            firstname = row[1]
            lastname = row[2]
            email = row[3]
            dbpassword = row[4]
            if email and check_password_hash(dbpassword, password):
                # User.setUser lagrar lokalt i sessionshanteraren (User.py)
                User.setUser(self=user, id=userid, first_name=firstname, last_name=lastname, email=email)
                if request.form.get("RememberMe"):
                    login_user(user, remember=True)
                    print(text(query))
                    return redirect(url_for("home"))
                else:
                    login_user(user)
                    print(text(query))
                    return redirect(url_for("home"))
    return render_template("login.html")


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        firstname = request.form.get("firstname")
        lastname = request.form.get("lastname")
        hashed_password = generate_password_hash(password)
        # user = User(email=email, password=hashed_password, privilege="0")
        query = ("INSERT INTO user (email, password, first_name, last_name) VALUES (:email, :password, :first_name, "
                 ":last_name);")
        connection = db.engine.connect()
        result = connection.execute(text(query), {'email': email, 'password': hashed_password, 'first_name': firstname,
                                                  'last_name': lastname})
        connection.commit()
        connection.close()
        return redirect(url_for("login"))
    return render_template("register.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("home"))


@app.route("/settings", methods=['GET', 'POST'])
@login_required
def settings():
    if request.method == "POST":
        # Ifall inte information om användarens adress etc finns eller finns så uppdatera.
        uid = current_user.id
        address = request.form.get("StreetAddress")
        zipcode = request.form.get("zip_code")
        region = request.form.get("Region")
        city = request.form.get("City")
        query = ("INSERT INTO address (user_id, street_address, zip_code, region, city) VALUES (:user_id, "
                 ":street_address, :zip_code, :region, :city) ON DUPLICATE KEY UPDATE street_address = VALUES("
                 "street_address), zip_code = VALUES(zip_code), region = VALUES(region), city = VALUES(city);")
        connection = db.engine.connect()
        connection.execute(text(query),
                           {'user_id': uid, 'street_address': address, 'zip_code': zipcode, 'region': region,
                            'city': city})
        connection.commit()
        connection.close()
        return redirect(url_for("home"))
    else:
        # Detta gör så ifall det redan finns information om användarens adress etc så läggs det in automatiskt.
        uid = current_user.id
        query = "SELECT street_address, zip_code, region, city FROM address WHERE user_id = :user_id"
        connection = db.engine.connect()
        result = connection.execute(text(query), {'user_id': uid})
        connection.close()
        if result:
            print("Fanns ett id")
        user_info = result.fetchone()
        return render_template("settings.html", user_info=user_info)


if __name__ == '__main__':
    app.run(debug=True)
