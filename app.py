from os import urandom
from flask import *
from flask_login import *
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from werkzeug.security import generate_password_hash, check_password_hash
from Login.User import User

db = SQLAlchemy()
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:root@localhost:3306/dbkursen'
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
    # Index sida / Start-sida.
    data = {
        'title': 'Non-alcoholic Beer Store',
        'welcome_message': 'Non-alcoholic Beer Store',
        'user': load_users(),
        'footer_text': 'Service for Non-alcoholic Beer Store. All rights reserved.'
    }
    return render_template('index.html', **data)


def load_users():
    # För att visa den inloggade användarens för och efternamn.
    if current_user.is_authenticated:
        return User.getFirstName(user) + ' ' + User.getLastName(user)
    else:
        return "Guest"


@app.route('/login', methods=['GET', 'POST'])
def login():
    data = {
        'welcome_message': 'Non-alcoholic Beer Store',
        'footer_text': 'Service for Non-alcoholic Beer Store. All rights reserved.'
    }
    # Login funktion, genom att kontrollera att användarens email, hashadelösenord och lösenord matchar så
    # hanteras inloggningen genom sessions-hanteraren skött av Flask-login.
    if request.method == "POST":
        useremail = request.form.get("email")
        password = request.form.get("password")
        query = "SELECT * FROM users WHERE users.email = :useremail"
        connect = db.engine.connect()
        result = connect.execute(text(query), {'useremail': useremail})
        connect.close()
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
    return render_template("login.html", **data)


@app.route('/register', methods=['GET', 'POST'])
def register():
    data = {
        'welcome_message': 'Non-alcoholic Beer Store',
        'footer_text': 'Service for Non-alcoholic Beer Store. All rights reserved.'
    }
    # Registreringsfunktion, registrerar ett konto genom information som man uppger
    # på sidan, hashar lösenordet.
    # TODO: Hantera eventuell duplicerad uppgifter
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        firstname = request.form.get("firstname")
        lastname = request.form.get("lastname")
        hashed_password = generate_password_hash(password)
        # user = User(email=email, password=hashed_password, privilege="0")
        query = (
            "INSERT INTO users (email, password, first_name, last_name, privilege) VALUES (:email, :password, "
            ":first_name,"
            ":last_name, :privilege);")
        connect = db.engine.connect()
        connect.execute(text(query), {'email': email, 'password': hashed_password, 'first_name': firstname,
                                      'last_name': lastname, 'privilege': 0})
        connect.commit()
        connect.close()
        return redirect(url_for("login"))
    return render_template("register.html", **data)


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("home"))


@app.route("/settings", methods=['GET', 'POST'])
@login_required
def settings():
    data = {
        'welcome_message': 'Non-alcoholic Beer Store',
        'footer_text': 'Service for Non-alcoholic Beer Store. All rights reserved.'
    }
    # Inställningar, där användaren kan lägga in mer uppgifter så som adress och dylikt.
    # Ifall duplicerade uppgifter skulle finnas så tas det itu med i samma query.
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
        connect = db.engine.connect()
        connect.execute(text(query),
                        {'user_id': uid, 'street_address': address, 'zip_code': zipcode, 'region': region,
                         'city': city})
        connect.commit()
        connect.close()
        return redirect(url_for("home"))
    else:
        # Detta gör så ifall det redan finns information om användarens adress etc så läggs det in automatiskt
        # genom att hämta det från databasen.
        uid = current_user.id
        query = "SELECT street_address, zip_code, region, city FROM address WHERE user_id = :user_id"
        connect = db.engine.connect()
        result = connect.execute(text(query), {'user_id': uid})
        connect.close()
        if result:
            print("Fanns ett id")
        user_info = result.fetchone()
        return render_template("settings.html", user_info=user_info, **data)


@app.route("/store")
def store():
    data = {
        'welcome_message': 'Non-alcoholic Beer Store',
        'footer_text': 'Service for Non-alcoholic Beer Store. All rights reserved.'
    }
    # Denna sida visar alla product_categories, genom att iterera med en for loop igenom hela product_categories
    # så genereras länkar till alla product_categories i html:en.
    productcategory = []
    cat_id = []
    query = "SELECT categories, id FROM product_categories"
    connect = db.engine.connect()
    result = connect.execute(text(query))
    connect.close()
    for row in result:
        productcategory.append(row[0])
        cat_id.append(row[1])
    # categories blir en tuple med kategori och id, för att kunna generera url med id:et
    categories = zip(productcategory, cat_id)
    return render_template("store.html", categories=categories, user=User.getFirstName(user), **data)


@app.route("/category/<int:category_id>")
def category(category_id):
    data = {
        'welcome_message': 'Non-alcoholic Beer Store',
        'footer_text': 'Service for Non-alcoholic Beer Store. All rights reserved.'
    }
    # Denna sida visar alla products med samma category_id och fungerar likadant som store
    productname = []
    prod_id = []
    price = []
    query = "SELECT item_name, id, price FROM products WHERE category_id = :category_id"
    connect = db.engine.connect()
    result = connect.execute(text(query), {'category_id': category_id})
    connect.close()
    for row in result:
        formatdeci = f"\t{str(row[2]).replace('.', ',')}"
        productname.append(row[0])
        prod_id.append(row[1])
        price.append(formatdeci)
    products = zip(productname, prod_id, price)
    return render_template("products.html", products=products, **data)


@app.route("/product/<int:prod_id>", methods=['GET', 'POST'])
def product(prod_id):
    data = {
        'welcome_message': 'Non-alcoholic Beer Store',
        'footer_text': 'Service for Non-alcoholic Beer Store. All rights reserved.'
    }
    # Självaste produktsidan. Här visas information om produkten så som hur många produkter i lager, pris
    # och ger möjlighet att lägga till i kundvagn.
    query = "SELECT * FROM products WHERE id = :prod_id"
    connect = db.engine.connect()
    result = connect.execute(text(query), {'prod_id': prod_id})
    connect.close()
    for row in result:
        productID = row[0]
        # categoryID = row[1]
        productname = row[2]
        stock = row[3]
        price = row[4]
        rate = rating(productID)
    # Detta sker när man lägger till shopping cart.
    if request.method == "POST":
        cart_items(productID, 1)  # TODO: Gör att man kan ändra kvantiteten.
        return redirect(url_for("product", prod_id=prod_id))
    return render_template("productpage.html", productname=productname, stock=stock, price=price, rating=rate, **data)


@app.route("/shoppingcart")
@login_required
def shoppingcart():
    data = {
        'welcome_message': 'Non-alcoholic Beer Store',
        'footer_text': 'Service for Non-alcoholic Beer Store. All rights reserved.'
    }
    uid = current_user.id
    cart_query = "SELECT product_id, quantity FROM cart_items WHERE user_id = :current_user"
    product_query = "SELECT item_name, price FROM products WHERE id = :product_id"
    connect = db.engine.connect()
    cart_result = connect.execute(text(cart_query), {'current_user': uid})

    shopping_results = []
    # (product_name, price, quantity)

    for item in cart_result:
        product_id = item[0]
        quantity = item[1]
        product_result = connect.execute(text(product_query), {'product_id': product_id})
        for product in product_result:
            shopping_results.append((product[0], str(product[1]), quantity))

    connect.close()

    return render_template("shoppingcart.html", shopping_results=shopping_results, **data)


def cart_items(prod_id, quantity):
    # Lägga in items i cart_items
    query = "INSERT INTO cart_items (user_id,product_id, quantity) VALUES (:user_id, :product_id, :quantity)"
    connect = db.engine.connect()
    connect.execute(text(query), {'user_id': current_user.id, 'product_id': prod_id, 'quantity': quantity})
    print("Lade till i cart_items: ", prod_id, " antal: " + str(quantity))
    connect.commit()
    connect.close()


@app.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    data = {
        'welcome_message': 'Non-alcoholic Beer Store',
        'footer_text': 'Service for Non-alcoholic Beer Store. All rights reserved.'
    }
    uid = current_user.id
    sum_query = ("SELECT quantity, product_id FROM cart_items WHERE user_id = :current_user")
    connect = db.engine.connect()
    sum_result = connect.execute(text(sum_query), {'current_user': uid})
    sum_total = 0
    for quanprod in sum_result:
        price_query = ("SELECT price FROM products WHERE id = :product_id")
        connect = db.engine.connect()
        price_result = connect.execute(text(price_query), {'product_id': quanprod[1]})
        for result in price_result:
            # something something multiply with quantity...
            sum_total += float(result[0])

    connect.close()
    if request.method == "POST":
        # Ifall inte information om användarens adress etc finns eller finns så uppdatera.
        uid = current_user.id
        address = request.form.get("StreetAddress")
        zipcode = request.form.get("zip_code")
        region = request.form.get("Region")
        city = request.form.get("City")
        phone_nr = request.form.get("PhoneNumber")
        query = ("INSERT INTO shipping_address (id, street_address, zip_code, region, city, phone_nr) VALUES (:user_id, "
                 ":street_address, :zip_code, :region, :city, :phone_nr) ON DUPLICATE KEY UPDATE street_address = VALUES("
                 "street_address), zip_code = VALUES(zip_code), region = VALUES(region), city = VALUES(city), phone_nr = VALUES(phone_nr);")
        connect = db.engine.connect()
        connect.execute(text(query),
                        {'user_id': uid, 'street_address': address, 'zip_code': zipcode, 'region': region,
                         'city': city, 'phone_nr': phone_nr})
        connect.commit()
        query = ("DELETE FROM cart_items WHERE user_id = :user_id;")
        connect = db.engine.connect()
        connect.execute(text(query), {'user_id': uid})
        connect.close()
        return redirect(url_for("thankyou"))
    else:
        # Detta gör så ifall det redan finns information om användarens adress etc så läggs det in automatiskt
        # genom att hämta det från databasen.
        uid = current_user.id
        query = "SELECT street_address, zip_code, region, city, phone_nr FROM address WHERE user_id = :user_id"
        connect = db.engine.connect()
        result = connect.execute(text(query), {'user_id': uid})
        connect.close()
        user_info = result.fetchone()
        return render_template("checkout.html", user_info=user_info, sum_total=sum_total, **data)

@app.route('/thankyou')
def thankyou():
    data = {
        'title': 'Non-alcoholic Beer Store',
        'welcome_message': 'Thank you for shopping Non-alcoholic Beer!',
        'footer_text': 'Service for Non-alcoholic Beer Store. All rights reserved.'
    }
    return render_template("thankyou.html", **data)

def rating(prod_id):
    query = "SELECT * FROM ratings WHERE id = :prod_id"
    connect = db.engine.connect()
    result = connect.execute(text(query), {'prod_id': prod_id})
    rows = result.fetchall()
    connect.close()
    if not rows:
        return "0"
    else:
        for row in rows:
            return row[0]


if __name__ == '__main__':
    app.run(debug=True)
