INSERT INTO payment_options(options)
VALUES
	('Swish'),
    ('Visa'),
    ('Mastercard');

INSERT INTO product_categories(categories)
VALUES
	('Lager'),
    ('Ale'),
    ('Porter & Stout');

INSERT INTO products(category_id, item_name, in_stock, price)
VALUES
	((SELECT id FROM product_categories WHERE categories = 'Lager'), 'Mariestads', 500, 12.50),
    ((SELECT id FROM product_categories WHERE categories = 'Lager'), 'Falcon', 500, 11.99),
    ((SELECT id FROM product_categories WHERE categories = 'Lager'), 'Carlsberg', 500, 10.49),
    ((SELECT id FROM product_categories WHERE categories = 'Ale'), 'Brooklyn', 500, 15.49),
    ((SELECT id FROM product_categories WHERE categories = 'Ale'), 'Newcastle', 500, 13.99),
    ((SELECT id FROM product_categories WHERE categories = 'Ale'), 'Innis&Gunn', 500, 11.50),
    ((SELECT id FROM product_categories WHERE categories = 'Porter & stout'), 'Guinness', 500, 14.49),
    ((SELECT id FROM product_categories WHERE categories = 'Porter & stout'), 'Carnegie', 500, 14.99),
    ((SELECT id FROM product_categories WHERE categories = 'Porter & stout'), 'Fullers', 500, 12.50);
