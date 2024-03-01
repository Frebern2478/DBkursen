from os import urandom
from flask import *
from flask_login import *
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from werkzeug.security import generate_password_hash, check_password_hash
from Login.User import User, AnonymousUser

db = SQLAlchemy()
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:hej123@localhost:3306/dbkursen'
app.config["SECRET_KEY"] = urandom(20)  # TEST
db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.anonymous_user = AnonymousUser
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
        rate = getrating(productID)
        comment = getcomment(productID)
    # Detta sker när man lägger till shopping cart.
    if request.method == "POST":
        quantity = request.form.get("quantity")
        if not quantity:
            quantity = 1
        else:
            quantity = int(quantity)
        if quantity >= int(stock):
            flash("Du kan inte handla fler än som finns i lager.")
            return redirect(url_for("product", prod_id=prod_id))
        else:
            cart_items(productID, quantity)  # TODO: Gör att man kan ändra kvantiteten.
            return redirect(url_for("product", prod_id=prod_id))
    return render_template("productpage.html", prod_id=prod_id, productname=productname, stock=stock, price=price,
                           rating=rate, comment=comment, **data)


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

    # TODO: Fixa shopping cart.
    return render_template("shoppingcart.html", shopping_results=shopping_results, **data)


def cart_items(prod_id, quantity):
    # Lägga in items i cart_items
    query = ("INSERT INTO cart_items (user_id, product_id, quantity) VALUES (:user_id, :product_id, :quantity) ON "
             "DUPLICATE KEY UPDATE quantity = quantity + :quantity")
    connect = db.engine.connect()
    connect.execute(text(query), {'user_id': current_user.id, 'product_id': prod_id, 'quantity': quantity})
    print("Lade till i cart_items: ", prod_id, " antal: " + str(quantity))
    connect.commit()
    connect.close()


def getUserName(userid):
    query = "SELECT first_name, last_name FROM users WHERE id = :id"
    connect = db.engine.connect()
    result = connect.execute(text(query), {'id': userid})
    return result.fetchone()


@app.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    data = {
        'welcome_message': 'Non-alcoholic Beer Store',
        'footer_text': 'Service for Non-alcoholic Beer Store. All rights reserved.'
    }
    uid = current_user.id
    summa = sumtotal(uid)

    if request.method == "POST":
        # Ifall inte information om användarens adress etc finns eller finns så uppdatera.
        uid = current_user.id
        address = request.form.get("StreetAddress")
        zipcode = request.form.get("zip_code")
        region = request.form.get("Region")
        city = request.form.get("City")
        query = (
            "INSERT INTO shipping_address (id, street_address, zip_code, region, city) VALUES (:user_id, "
            ":street_address, :zip_code, :region, :city) ON DUPLICATE KEY UPDATE street_address = VALUES("
            "street_address), zip_code = VALUES(zip_code), region = VALUES(region), city = VALUES(city);")
        connect = db.engine.connect()
        connect.execute(text(query),
                        {'user_id': uid, 'street_address': address, 'zip_code': zipcode, 'region': region,
                         'city': city})
        connect.commit()
        connect.close()
        deductquantity(uid)
        # Tar bort från cart_items och lägger till i checkout databsen.
        # TODO: Ett problem är ju att vi vet inte nu vad kunden har beställt.
        query = ("INSERT INTO checkout(user_id, shipping_id, payment_id, sum_total) VALUES (:user_id, :shipping_id, "
                 ":payment_id, :sum_total);" "DELETE FROM cart_items WHERE user_id = :user_id;")
        connect = db.engine.connect()
        # TODO: Payment_id är ju ifall de använder swish etc, så den är hårdkodat.
        # Kanske ta bort shipping_id? den verkar vara överflödig.
        connect.execute(text(query), {'user_id': uid, 'shipping_id': uid, 'payment_id': 1, 'sum_total': summa})
        connect.commit()
        connect.close()
        return redirect(url_for("thankyou"))
    else:
        # Detta gör så ifall det redan finns information om användarens adress etc så läggs det in automatiskt
        # genom att hämta det från databasen.
        query = "SELECT street_address, zip_code, region, city FROM address WHERE user_id = :user_id"
        connect = db.engine.connect()
        result = connect.execute(text(query), {'user_id': uid})
        connect.close()
        user_info = result.fetchone()
        return render_template("checkout.html", user_info=user_info, sum_total=summa, **data)


@app.route('/thankyou')
def thankyou():
    data = {
        'title': 'Non-alcoholic Beer Store',
        'welcome_message': 'Thank you for shopping Non-alcoholic Beer!',
        'footer_text': 'Service for Non-alcoholic Beer Store. All rights reserved.'
    }
    return render_template("thankyou.html", **data)


def getrating(prod_id):
    query = "SELECT AVG(rating) FROM ratings WHERE prod_id = :prod_id"
    connect = db.engine.connect()
    result = connect.execute(text(query), {'prod_id': prod_id})
    rows = result.fetchall()
    connect.close()
    for row in rows:
        # Kollar ifall result är tomt.
        if row[0] is None:
            return 0
        else:
            return int(row[0])


@app.route('/rate-product', methods=['POST'])
def rateproduct():
    prod_id = request.form.get('prod_id')
    rating = request.form.get('rating')
    # print(prod_id)
    query = "INSERT into ratings(prod_id, user_id, rating) VALUES (:prod_id, :user_id, :rating)"
    connect = db.engine.connect()
    connect.execute(text(query), {'user_id': current_user.id, 'prod_id': prod_id, 'rating': rating})
    connect.commit()
    connect.close()
    return redirect(url_for("product", prod_id=prod_id))


def sumtotal(uid):
    sum_query = "SELECT quantity, product_id FROM cart_items WHERE user_id = :current_user"
    connect = db.engine.connect()
    sum_result = connect.execute(text(sum_query), {'current_user': uid})
    sum_total = 0
    for quanprod in sum_result:
        price_query = "SELECT price FROM products WHERE id = :product_id"
        connect = db.engine.connect()
        price_result = connect.execute(text(price_query), {'product_id': quanprod[1]})
        for result in price_result:
            # something something multiply with quantity...
            sum_total += float(result[0]) * quanprod[0]
    connect.close()
    print(sum_total)
    return sum_total


def deductquantity(uid):
    connect = db.engine.connect()
    # Get cart items for the given user_id
    query = "SELECT quantity, product_id FROM cart_items WHERE user_id = :user_id"
    result = connect.execute(text(query), {'user_id': uid})
    cart_items = result.fetchall()

    for quantity, product_id in cart_items:
        # Get current stock for the product
        product_query = "SELECT in_stock FROM products WHERE id = :product_id"
        product_result = connect.execute(text(product_query), {'product_id': product_id})
        product = product_result.fetchone()

        if product:
            in_stock = product[0]
            new_stock = max(0, in_stock - quantity)
            # Update stock in the products table
            update_query = "UPDATE products SET in_stock = :in_stock WHERE id = :product_id"
            connect.execute(text(update_query), {'in_stock': new_stock, 'product_id': product_id})

    # Commit and close
    connect.commit()
    connect.close()


@app.route('/add-comment', methods=['POST'])
def addcomment():
    prod_id = request.form.get('prod_id')
    comment = request.form.get('comment')
    print(prod_id)
    query = "INSERT into comments(prod_id, user_id, comment) VALUES (:prod_id, :user_id, :comment)"
    connect = db.engine.connect()
    connect.execute(text(query), {'prod_id': prod_id, 'user_id': current_user.id, 'comment': comment})
    connect.commit()
    connect.close()
    return redirect(url_for("product", prod_id=prod_id))


def getcomment(prod_id):
    query = "SELECT comment, user_id FROM comments WHERE prod_id = :prod_id"
    connect = db.engine.connect()
    comments = connect.execute(text(query), {'prod_id': prod_id})
    rows = comments.fetchall()
    connect.close()

    if not rows:
        return "Inga kommentarer ännu!"
    else:
        comment_list = []
        for row in rows:
            comment = row[0]
            user_id = row[1]
            username = getUserName(user_id)
            # print(comment, user_id, username)
            comment_list.append(comment + " Skriven av: " + str(username))
        return comment_list


if __name__ == '__main__':
    app.run(debug=True)
