from os import urandom

import nh3
from flask import *
from flask_login import *
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from werkzeug.security import generate_password_hash, check_password_hash
from Login.User import User, AnonymousUser

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = "mysql+pymysql://root:root@dbscripts:3306/dbkursen"
#app.config['SQLALCHEMY_DATABASE_URI'] = "mysql+pymysql://root:hej123@localhost:3306/dbkursen"
app.config["SECRET_KEY"] = urandom(20)  # TEST
db = SQLAlchemy()
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
    return render_template('index.html', **getdatatemplate())


def load_users():
    # För att visa den inloggade användarens för och efternamn.
    if current_user.is_authenticated:
        return User.getFirstName(user) + ' ' + User.getLastName(user)
    else:
        return "Guest"


@app.route('/login', methods=['GET', 'POST'])
def login():
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
                    return redirect(url_for("home"))
                else:
                    login_user(user)
                    return redirect(url_for("home"))
    return render_template("login.html", **getdatatemplate())


@app.route('/register', methods=['GET', 'POST'])
def register():
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
    return render_template("register.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("home"))


@app.route("/settings", methods=['GET', 'POST'])
@login_required
def settings():
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
        user_info = result.fetchone()
        return render_template("settings.html", user_info=user_info, **getdatatemplate())


@app.route("/store")
def store():
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
    return render_template("store.html", categories=categories, **getdatatemplate())


@app.route("/category/<int:category_id>")
def category(category_id):
    # Denna sida visar alla products med samma category_id och fungerar likadant som store
    is_admin = iscurrentuseradmin()
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
    return render_template("products.html", products=products, is_admin=is_admin, **getdatatemplate(), category_id=category_id)


@app.route("/product/<int:prod_id>", methods=['GET', 'POST'])
def product(prod_id):
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
            try:
                quantity = int(quantity)
            except ValueError:
                flash("Du måste ange ett giltigt antal.")
                return redirect(url_for("product", prod_id=prod_id))
        if quantity <= 0:
            flash("Du kan inte köpa en negativ mängd av en produkt.")
        elif quantity >= int(stock):
            flash("Du kan inte handla fler än vad som finns i lager.")
        else:
            cart_items(productID, quantity)
            flash("Produkten har lagts till i varukorgen.")
        return redirect(url_for("product", prod_id=prod_id))
    return render_template("productpage.html", prod_id=prod_id, productname=productname, stock=stock, price=price,
                           rating=rate, comment=comment, **getdatatemplate())


@app.route("/shoppingcart")
@login_required
def shoppingcart():
    uid = current_user.id
    cart_query = "SELECT product_id, quantity FROM cart_items WHERE user_id = :current_user"
    product_query = "SELECT item_name, price FROM products WHERE id = :product_id"
    connect = db.engine.connect()
    cart_result = connect.execute(text(cart_query), {'current_user': uid})
    shopping_results = []
    for item in cart_result:
        product_id = item[0]
        quantity = item[1]
        product_result = connect.execute(text(product_query), {'product_id': product_id})
        for product in product_result:
            shopping_results.append((product[0], str(product[1]), quantity))
    connect.close()
    return render_template("shoppingcart.html", shopping_results=shopping_results, **getdatatemplate())


def cart_items(prod_id, quantity):
    # Lägga in items i cart_items
    query = ("INSERT INTO cart_items (user_id, product_id, quantity) VALUES (:user_id, :product_id, :quantity) ON "
             "DUPLICATE KEY UPDATE quantity = quantity + :quantity")
    connect = db.engine.connect()
    connect.execute(text(query), {'user_id': current_user.id, 'product_id': prod_id, 'quantity': quantity})
    connect.commit()
    connect.close()


def getUserName(userid):
    # Denna funktion används för att få ut för och efternamn till användaren.
    query = "SELECT first_name, last_name FROM users WHERE id = :id"
    connect = db.engine.connect()
    result = connect.execute(text(query), {'id': userid})
    return result.fetchone()


@app.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
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
        # Här tar vi bort varorna från lagret.
        deductquantity(uid)
        # Tar bort från cart_items och lägger till i checkout databsen.
        # TODO: Ett problem är ju att vi vet inte nu vad kunden har beställt.
        insert_query = "INSERT INTO checkout (user_id, shipping_id, payment_id, sum_total) VALUES (:user_id, :shipping_id, :payment_id, :sum_total)"
        connect = db.engine.connect()
        connect.execute(text(insert_query), {'user_id': uid, 'shipping_id': uid, 'payment_id': 1,
                                             'sum_total': summa})
        # Delete cart items
        delete_query = "DELETE FROM cart_items WHERE user_id = :user_id"
        connect.execute(text(delete_query), {'user_id': uid})
        connect.commit()
        connect.close()
        # TODO: Payment_id är ju ifall de använder andra betalningstjänster etc, och den är inte gjord än, så vi hårdkodar här.
        # Kanske ta bort shipping_id? den verkar vara överflödig.
        return redirect(url_for("thankyou"))
    else:
        # Detta gör så ifall det redan finns information om användarens adress etc så läggs det in automatiskt
        # genom att hämta det från databasen.
        query = "SELECT street_address, zip_code, region, city FROM address WHERE user_id = :user_id"
        connect = db.engine.connect()
        result = connect.execute(text(query), {'user_id': uid})
        connect.close()
        user_info = result.fetchone()
        return render_template("checkout.html", user_info=user_info, sum_total=summa, **getdatatemplate())


@app.route('/thankyou')
@login_required
def thankyou():
    data = {
        'title': 'Non-alcoholic Beer Store',
        'welcome_message': 'Thank you for shopping at Non-alcoholic Beer Store!',
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
        # Kollar ifall result är av None.
        if not row[0]:
            return 0
        else:
            return int(row[0])


@app.route('/rate-product', methods=['POST'])
def rateproduct():
    prod_id = request.form.get('prod_id')
    rating = request.form.get('rating')
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
    return sum_total


def getdatatemplate():
    data = {
        'title': 'Non-alcoholic Beer Store',
        'welcome_message': 'Non-alcoholic Beer Store',
        'user': load_users(),
        'footer_text': 'Service for Non-alcoholic Beer Store. All rights reserved.'
    }
    return data


def deductquantity(uid):
    connect = db.engine.connect()
    # Få itemsen givet uid
    query = "SELECT quantity, product_id FROM cart_items WHERE user_id = :user_id"
    result = connect.execute(text(query), {'user_id': uid})
    cart_items = result.fetchall()
    for quantity, product_id in cart_items:
        # Få hur många är i lager från products
        product_query = "SELECT in_stock FROM products WHERE id = :product_id"
        product_result = connect.execute(text(product_query), {'product_id': product_id})
        product = product_result.fetchone()
        if product:
            in_stock = product[0]
            new_stock = max(0, in_stock - quantity)
            # Uppdatera i products
            update_query = "UPDATE products SET in_stock = :in_stock WHERE id = :product_id"
            connect.execute(text(update_query), {'in_stock': new_stock, 'product_id': product_id})
    connect.commit()
    connect.close()


@app.route('/add-comment', methods=['POST'])
@login_required
def addcomment():
    prod_id = request.form.get('prod_id')
    comment = request.form.get('comment')
    cleancomment = nh3.clean(comment)
    query = "INSERT into comments(prod_id, user_id, comment) VALUES (:prod_id, :user_id, :comment)"
    connect = db.engine.connect()
    connect.execute(text(query), {'prod_id': prod_id, 'user_id': current_user.id, 'comment': cleancomment})
    connect.commit()
    connect.close()
    return redirect(url_for("product", prod_id=prod_id))


def getcomment(prod_id):
    userprivilege = getuserprivilege(current_user.id)
    query = "SELECT id ,comment, user_id FROM comments WHERE prod_id = :prod_id"
    connect = db.engine.connect()
    comments = connect.execute(text(query), {'prod_id': prod_id})
    rows = comments.fetchall()
    connect.close()
    if not rows:
        return "Inga kommentarer ännu!"
    else:
        comment_list = ""
        for row in rows:
            comment_id = row[0]
            comment = nh3.clean(row[1])
            user_id = row[2]
            username = getUserName(user_id)
            firstname = username[0]
            lastname = username[1]
            comment_list += comment + " Skriven av: " + firstname + " " + lastname + '<br>'
            if iscurrentuseradmin():
                # Add delete link
                delete_url = url_for('delete_comment', comment_id=comment_id, prod_id=prod_id)
                comment_list += f" <a href='{delete_url}'>Delete</a>"
            comment_list += '<br>'
        return comment_list


def getuserprivilege(uid):
    query = "SELECT privilege FROM users WHERE id = :id"
    connect = db.engine.connect()
    result = connect.execute(text(query), {'id': uid})
    userprivilege = result.fetchone()
    connect.close()
    if not userprivilege:
        return None
    return userprivilege[0]


def iscurrentuseradmin():
    # if user is admin return true.
    userprivilege = getuserprivilege(current_user.id)
    if userprivilege != 0:
        # print("User is admin")
        return True
    else:
        return False


@app.route('/delete_comment/<int:comment_id><int:prod_id>', methods=['GET', 'POST'])
def delete_comment(comment_id, prod_id):
    if iscurrentuseradmin():
        query = "DELETE FROM comments WHERE id = :comment_id"
        connect = db.engine.connect()
        connect.execute(text(query), {'comment_id': comment_id})
        connect.commit()
        connect.close()
        # return render_template("thankyou.html")
        return redirect(url_for("product", prod_id=prod_id))


def deleteallcommentandrating(prod_id):
    # Detta behövs för att kunna ta bort en produkt som har kommentar eller rating pga foreign key.
    if iscurrentuseradmin():
        commentquery = "DELETE FROM comments WHERE prod_id = :prod_id"
        connect = db.engine.connect()
        connect.execute(text(commentquery), {'prod_id': prod_id})
        connect.commit()
        ratingquery = "DELETE FROM ratings WHERE prod_id = :prod_id"
        connect.execute(text(ratingquery), {'prod_id': prod_id})
        connect.commit()
        connect.close()


@app.route('/add_product/<int:category_id>', methods=['GET', 'POST'])
def add_product(category_id):
    if iscurrentuseradmin():
        if request.method == 'POST':
            item_name = request.form.get('item_name')
            in_stock = request.form.get('quantity')
            price = request.form.get('price')
            query = "INSERT INTO products (category_id,item_name, in_stock, price) VALUES (:category_id, :item_name, :in_stock, :price)"
            connect = db.engine.connect()
            connect.execute(text(query), {'category_id': category_id,'item_name': item_name, 'in_stock': in_stock, 'price': price})
            connect.commit()
            connect.close()
            return render_template("thankyou.html")
    return render_template("add_product.html")


@app.route('/delete_product/<int:prod_id>', methods=['GET', 'POST'])
def delete_product(prod_id):
    if iscurrentuseradmin():
        deleteallcommentandrating(prod_id)
        query = "DELETE FROM products WHERE id = :prod_id"
        connect = db.engine.connect()
        connect.execute(text(query), {'prod_id': prod_id})
        connect.commit()
        connect.close()
        return render_template("thankyou.html")
        # return redirect(url_for("category", prod_id=prod_id))


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
