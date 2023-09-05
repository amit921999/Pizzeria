# Import Flask and SQLAlchemy
import time
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from celery import Celery
import logging

# Create a Flask app instance
app = Flask(__name__)
app.debug = True
app.threaded = True

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s %(message)s')

# Add logging statements to your code
logging.debug('Debug message')
logging.info('Info message')
logging.warning('Warning message')
logging.error('Error message')
logging.critical('Critical message')

# Configure the database URI
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:example@db/pizzeria'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Create a SQLAlchemy object
db = SQLAlchemy(app)


# Define the models for the tables
class PizzaBase(db.Model):
    __tablename__ = 'pizza_bases'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), nullable=False)
    price = db.Column(db.Numeric(5, 2), nullable=False)


class CheeseType(db.Model):
    __tablename__ = 'cheese_types'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), nullable=False)
    price = db.Column(db.Numeric(5, 2), nullable=False)


class Topping(db.Model):
    __tablename__ = 'toppings'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), nullable=False)
    price = db.Column(db.Numeric(5, 2), nullable=False)


class Pizza(db.Model):
    __tablename__ = 'pizzas'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    base_id = db.Column(db.Integer, db.ForeignKey('pizza_bases.id'), nullable=False)
    cheese_id = db.Column(db.Integer, db.ForeignKey('cheese_types.id'), nullable=False)
    base = db.relationship('PizzaBase', backref='pizzas')
    cheese = db.relationship('CheeseType', backref='pizzas')
    toppings = db.relationship('Topping', secondary='pizza_toppings', backref='pizzas')

    @property
    def price(self):
        return self.base.price + self.cheese.price + sum(topping.price for topping in self.toppings)


class Order(db.Model):
    __tablename__ = 'orders'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    created_at = db.Column(db.DateTime, nullable=False, default=db.func.current_timestamp())
    status = db.Column(db.String(20), nullable=False, default='Placed')
    pizzas = db.relationship('Pizza', secondary='order_items', backref='orders')

    @property
    def quantities(self):
        quantities = []
        for pizza in self.pizzas:
            order_pizza = OrderPizza.query.filter_by(order_id=self.id, pizza_id=pizza.id).first()
            quantities.append(order_pizza.quantity)
        return quantities


class OrderPizza(db.Model):
    __tablename__ = 'order_pizzas'
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    pizza_id = db.Column(db.Integer, db.ForeignKey('pizzas.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    order = db.relationship('Order', backref='order_pizzas')
    pizza = db.relationship('Pizza')


# Create a function to create and insert the data once
def create_and_insert_data():
    # Check if the tables are empty
    if not PizzaBase.query.first() and not CheeseType.query.first() and not Topping.query.first():
        # Create the tables
        db.create_all()

        # Create some sample data for pizza bases
        pizza_bases = [
            PizzaBase(id=1, name='Thin-crust', price=5.00),
            PizzaBase(id=2, name='Normal', price=6.00),
            PizzaBase(id=3, name='Cheese-burst', price=7.00)
        ]

        # Create some sample data for cheese types
        cheese_types = [
            CheeseType(id=1, name='Mozzarella', price=1.00),
            CheeseType(id=2, name='Cheddar', price=1.50),
            CheeseType(id=3, name='Parmesan', price=2.00),
            CheeseType(id=4, name='Vegan', price=2.50)
        ]

        # Create some sample data for toppings
        toppings = [
            Topping(id=1, name='Pepperoni', price=1.00),
            Topping(id=2, name='Mushrooms', price=0.50),
            Topping(id=3, name='Olives', price=0.50),
            Topping(id=4, name='Onions', price=0.50),
            Topping(id=5, name='Pineapple', price=1.00),
            Topping(id=6, name='Bacon', price=1.50),
            Topping(id=7, name='Jalapenos', price=0.50)
        ]

        # Add the data to the database session
        db.session.add_all(pizza_bases + cheese_types + toppings)

        # Commit the changes to the database
        db.session.commit()


# Call the function before the first request
@app.before_first_request
def before_first_request():
    create_and_insert_data()


# Define the association tables for many-to-many relationships
pizza_toppings_table = db.Table('pizza_toppings',
                                db.Column('pizza_id', db.Integer, db.ForeignKey('pizzas.id'), primary_key=True),
                                db.Column('topping_id', db.Integer, db.ForeignKey('toppings.id'), primary_key=True)
                                )

order_items_table = db.Table('order_items',
                             db.Column('order_id', db.Integer, db.ForeignKey('orders.id'), primary_key=True),
                             db.Column('pizza_id', db.Integer, db.ForeignKey('pizzas.id'), primary_key=True),
                             db.Column('quantity', db.Integer, nullable=False)
                             )

# Create the tables in the database
db.create_all()

# Configure the Celery broker and backend
app.config['CELERY_BROKER_URL'] = 'redis://localhost:6379/0'
app.config['CELERY_RESULT_BACKEND'] = 'redis://localhost:6379/0'

# Create a Celery object
celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
celery.conf.update(app.config)


# Define a route to get all pizza bases
@app.route('/bases')
def get_bases():
    bases = PizzaBase.query.all()
    return jsonify([{'id': base.id, 'name': base.name, 'price': str(base.price)} for base in bases])


# Define a route to get all cheese types
@app.route('/cheeses')
def get_cheeses():
    cheeses = CheeseType.query.all()
    return jsonify([{'id': cheese.id, 'name': cheese.name, 'price': str(cheese.price)} for cheese in cheeses])


# Define a route to get all toppings
@app.route('/toppings')
def get_toppings():
    toppings = Topping.query.all()
    return jsonify([{'id': topping.id, 'name': topping.name, 'price': str(topping.price)} for topping in toppings])


# Define a route to create a pizza
@app.route('/pizzas', methods=['POST'])
def create_pizza():
    # Get the request data as JSON
    data = request.get_json()

    # Validate the data
    if not data or not data.get('base_id') or not data.get('cheese_id') or not data.get('topping_ids'):
        return jsonify({'error': 'Missing or invalid data'}), 400

    # Get the base, cheese and toppings from the database
    base = PizzaBase.query.get(data['base_id'])
    cheese = CheeseType.query.get(data['cheese_id'])
    toppings = Topping.query.filter(Topping.id.in_(data['topping_ids'])).all()

    # Check if they exist
    if not base or not cheese or len(toppings) != len(data['topping_ids']):
        return jsonify({'error': 'Invalid base, cheese or topping ID'}), 404

    # Create a new pizza object
    pizza = Pizza(base=base, cheese=cheese)

    # Add the toppings to the pizza
    for topping in toppings:
        pizza.toppings.append(topping)

    # Add the pizza to the database session
    db.session.add(pizza)

    # Commit the changes to the database
    db.session.commit()

    # Return the pizza details as JSON
    return jsonify({
        'id': pizza.id,
        'base': pizza.base.name,
        'cheese': pizza.cheese.name,
        'toppings': [topping.name for topping in pizza.toppings],
        'price': str(pizza.price)
    }), 201


# Define a route to create an order
# @app.route('/orders', methods=['POST'])
# def create_order():
#     # Get the request data as JSON
#     data = request.get_json()
#
#     # Validate the data
#     if not data or not data.get('pizza_ids') or not data.get('quantities'):
#         return jsonify({'error': 'Missing or invalid data'}), 400
#
#     # Get the pizzas and quantities from the data
#     pizza_ids = data['pizza_ids']
#     quantities = data['quantities']
#
#     # Check if they have the same length
#     if len(pizza_ids) != len(quantities):
#         return jsonify({'error': 'Mismatched pizza IDs and quantities'}), 400
#
#     # Get the pizzas from the database
#     pizzas = Pizza.query.filter(Pizza.id.in_(pizza_ids)).all()
#
#     # Check if they exist
#     if len(pizzas) != len(pizza_ids):
#         return jsonify({'error': 'Invalid pizza ID'}), 404
#
#     # Create a new order object
#     order = Order()
#     order.quantities = quantities
#
#     # Add the pizzas and quantities to the order
#     for pizza, quantity in zip(pizzas, quantities):
#         order.pizzas.append(pizza)
#         order.quantities.append(quantity)
#
#     # Calculate the total price of the order
#     order.price = sum(pizza.price * quantity for pizza, quantity in zip(pizzas, quantities))
#
#     # Add the order to the database session
#     db.session.add(order)
#
#     # Commit the changes to the database
#     db.session.commit()
#
#     # Start a background task to track the order status
#     track_order.delay(order.id)
#
#     # Return the order details as JSON
#     return jsonify({
#         'id': order.id,
#         'created_at': order.created_at,
#         'status': order.status,
#         'pizzas': [{'id': pizza.id, 'name': pizza.name, 'price': str(pizza.price)} for pizza in order.pizzas],
#         'quantities': order.quantities,
#         'price': str(order.price)
#     }), 201


# Define a route to get an order by ID
@app.route('/orders', methods=['POST'])
def create_order():
    data = request.get_json()
    if not data or not data.get('pizza_ids') or not data.get('quantities'):
        return jsonify({'error': 'Missing or invalid data'}), 400

    if len(data['pizza_ids']) != len(data['quantities']):
        return jsonify({'error': 'Mismatched pizza IDs and quantities'}), 400

    order = Order()
    db.session.add(order)
    db.session.commit()

    for pizza_id, quantity in zip(data['pizza_ids'], data['quantities']):
        pizza = Pizza.query.get(pizza_id)
        if not pizza:
            return jsonify({'error': f'Pizza {pizza_id} not found'}), 404

        order_pizza = OrderPizza(order_id=order.id, pizza_id=pizza.id, quantity=quantity)
        db.session.add(order_pizza)

    db.session.commit()

    return jsonify({'id': order.id}), 201


@app.route('/orders/<int:order_id>')
def get_order(order_id):
    # Get the order from the database
    order = Order.query.get(order_id)

    # Check if it exists
    if not order:
        return jsonify({'error': 'Order not found'}), 404

    # Return the order details as JSON
    return jsonify({
        'id': order.id,
        'created_at': order.created_at,
        'status': order.status,
        'pizzas': [{'id': pizza.id, 'name': pizza.name, 'price': str(pizza.price)} for pizza in order.pizzas],
        'quantities': order.quantities,
        'price': str(order.price)
    })


# Define a Celery task to track the order status based on time
@celery.task(bind=True)
def track_order(self, order_id):
    # Get the order from the database
    order = Order.query.get(order_id)

    # Check if it exists
    if not order:
        return {'error': 'Order not found'}

    # Set the initial status to Placed
    order.status = 'Placed'

    # Update the database and send a progress update
    db.session.commit()
    self.update_state(state='PROGRESS', meta={'status': order.status})

    # Wait for one minute and change the status to Accepted
    time.sleep(60)
    order.status = 'Accepted'

    # Update the database and send a progress update
    db.session.commit()
    self.update_state(state='PROGRESS', meta={'status': order.status})

    # Wait for three minutes and change the status to Preparing
    time.sleep(180)
    order.status = 'Preparing'

    # Update the database and send a progress update
    db.session.commit()
    self.update_state(state='PROGRESS', meta={'status': order.status})

    # Wait for five minutes and change the status to Dispatched
    time.sleep(300)
    order.status = 'Dispatched'

    # Update the database and send a progress update
    db.session.commit()
    self.update_state(state='PROGRESS', meta={'status': order.status})

    # Wait for five minutes and change the status to Delivered
    time.sleep(300)
    order.status = 'Delivered'

    # Update the database and mark the task as successful
    db.session.commit()
    return {'status': order.status}
