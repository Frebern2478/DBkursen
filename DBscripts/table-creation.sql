CREATE TABLE users (
	id INT NOT NULL AUTO_INCREMENT,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    email VARCHAR(200),
    password VARCHAR(255),
    privilege INT,
    PRIMARY KEY(id)
);

CREATE TABLE address (
	user_id INT,
    street_address VARCHAR(200),
    zip_code INT,
    city VARCHAR(100),
    region VARCHAR(100),
    PRIMARY KEY(user_id),
    FOREIGN KEY(user_id) REFERENCES users(id)
);

CREATE TABLE product_categories (
	id INT AUTO_INCREMENT,
    categories VARCHAR(100),
    PRIMARY KEY(id)
);

CREATE TABLE products (
	id INT AUTO_INCREMENT,
    category_id INT,
    item_name VARCHAR(100),
    in_stock INT,
    price DECIMAL(6,2),
    PRIMARY KEY(id),
    FOREIGN KEY(category_id) REFERENCES product_categories(id)
);

CREATE TABLE comments (
    id INT AUTO_INCREMENT,
    prod_id INT,
	user_id INT,
    comment VARCHAR(255),
    PRIMARY KEY(id),
    FOREIGN KEY(prod_id) REFERENCES products(id),
    FOREIGN KEY(user_id) REFERENCES users(id)
);

CREATE TABLE ratings (
	id INT AUTO_INCREMENT,
    prod_id INT,
    user_id INT,
    rating INT,
    PRIMARY KEY(id),
    FOREIGN KEY(prod_id) REFERENCES products(id),
    FOREIGN KEY(user_id) REFERENCES users(id)
);

CREATE TABLE cart_items (
    user_id INT,
    product_id INT,
    quantity INT,
    PRIMARY KEY(user_id, product_id),
    FOREIGN KEY(user_id) REFERENCES users(id),
    FOREIGN KEY(product_id) REFERENCES products(id)
);

CREATE TABLE shipping_address (
	id INT AUTO_INCREMENT,
    street_address VARCHAR(200),
    zip_code INT,
    city VARCHAR(100),
    region VARCHAR(100),
    phone_nr VARCHAR(50),
    PRIMARY KEY(id)
);

CREATE TABLE payment_options (
	id INT AUTO_INCREMENT,
    options VARCHAR(100),
    PRIMARY KEY(id)
);

CREATE TABLE sales (
	id INT AUTO_INCREMENT,
    date DATETIME,
    product_id INT,
    percent_off INT,
    PRIMARY KEY(id),
    FOREIGN KEY(product_id) REFERENCES products(id)
);

CREATE TABLE shopping_cart (
    user_id INT,
    sales_id INT,
    date_added DATETIME DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY(user_id),
    FOREIGN KEY(user_id) REFERENCES users(id),
    FOREIGN KEY(sales_id) REFERENCES sales(id)
);

CREATE TABLE checkout (
	id INT AUTO_INCREMENT,
    user_id INT,
    shipping_id INT,
    payment_id INT,
    sum_total DECIMAL(10,2),
    PRIMARY KEY(id),
    FOREIGN KEY(user_id) REFERENCES users(id),
    FOREIGN KEY(shipping_id) REFERENCES shipping_address(id),
    FOREIGN KEY(payment_id) REFERENCES payment_options(id)
);
