from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_apscheduler import APScheduler
import os
import logging
import random
import string
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Initialize the Flask application
app = Flask(__name__)

# Configure PostgreSQL database URI
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:Pending1@localhost:5432/inventory_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Configure Scheduler
scheduler = APScheduler()
scheduler.init_app(app)

# Initialize the database and migration
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Enable SQLAlchemy logging to see SQL statements in the console
logging.basicConfig()
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)


# Function to generate a random SKU
def generate_sku():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))


# Define the Inventory model
class Inventory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sku = db.Column(db.String(8), unique=True, nullable=False, default=generate_sku)
    item_name = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    location = db.Column(db.String(50))
    dispatch_count = db.Column(db.Integer, default=0)  # Initialize dispatch_count to 0


# Define the Supplier model
class Supplier(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    contact = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(200))
    sku = db.Column(db.String(8), db.ForeignKey('inventory.sku'), nullable=True)  # Link to inventory


# Home route
@app.route('/')
def index():
    return render_template('index.html')


# Route for managing inventory
@app.route('/inventory', methods=['GET', 'POST'])
def inventory():
    if request.method == 'POST':
        try:
            item_name = request.form.get('item_name')
            quantity = request.form.get('quantity')
            location = request.form.get('location')

            print(f"Received item: {item_name}, quantity: {quantity}, location: {location}")

            if not item_name or not quantity:
                return jsonify({'status': 'error', 'message': 'Invalid input data.'})

            try:
                quantity = int(quantity)
            except ValueError:
                return jsonify({'status': 'error', 'message': 'Quantity must be a number.'})

            # Check if an item with the same name already exists
            existing_item = Inventory.query.filter_by(item_name=item_name).first()
            if existing_item:
                # If item exists, increase its quantity and update location
                existing_item.quantity += quantity
                existing_item.location = location
                db.session.commit()
                print(f"Updated existing item: {existing_item.item_name} with new quantity {existing_item.quantity}.")
                return jsonify({'status': 'success',
                                'message': f'Updated item {existing_item.item_name} with new quantity {existing_item.quantity}.'})
            else:
                # If item does not exist, create a new one
                sku = generate_sku()
                new_item = Inventory(item_name=item_name, quantity=quantity, location=location, sku=sku)
                db.session.add(new_item)
                db.session.commit()

                print(f"Item added successfully with SKU {sku}.")
                return jsonify({'status': 'success', 'message': f'Item added successfully with SKU {sku}!'})

        except Exception as e:
            print(f"Error: {e}")
            db.session.rollback()
            return jsonify({'status': 'error', 'message': 'An error occurred while adding the item.'})

    else:
        items = Inventory.query.all()
        print(f"Current inventory: {items}")
        return render_template('inventory.html', items=items)


# Route for managing suppliers
@app.route('/suppliers', methods=['GET', 'POST'])
def suppliers():
    if request.method == 'POST':
        try:
            name = request.form.get('name')
            contact = request.form.get('contact')
            email = request.form.get('email')
            address = request.form.get('address')
            sku = request.form.get('sku')  # Get the SKU from the form

            print(f"Received supplier: {name}, contact: {contact}, email: {email}, address: {address}, sku: {sku}")

            if not name or not contact or not email:
                return jsonify({'status': 'error', 'message': 'All fields except address are required.'})

            # Validate the SKU (if provided)
            if sku:
                inventory_item = Inventory.query.filter_by(sku=sku).first()
                if not inventory_item:
                    return jsonify({'status': 'error', 'message': 'Invalid SKU. No matching inventory item found.'})

            new_supplier = Supplier(name=name, contact=contact, email=email, address=address, sku=sku)
            db.session.add(new_supplier)
            db.session.commit()

            print("Supplier added successfully to the database.")
            return jsonify({'status': 'success', 'message': 'Supplier added successfully!'})

        except Exception as e:
            print(f"Error: {e}")
            db.session.rollback()
            return jsonify({'status': 'error', 'message': 'An error occurred while adding the supplier.'})

    else:
        suppliers_list = Supplier.query.all()
        print(f"Current suppliers: {suppliers_list}")
        return render_template('suppliers.html', suppliers=suppliers_list)


# Route for dispatching items
@app.route('/dispatch', methods=['POST'])
def dispatch():
    try:
        item_id = request.json.get('id')
        dispatch_quantity = int(request.json.get('quantity'))

        item = Inventory.query.get(item_id)

        if not item:
            return jsonify({'status': 'error', 'message': 'Item not found.'})

        if dispatch_quantity > item.quantity:
            return jsonify({'status': 'error', 'message': 'Dispatch quantity exceeds available inventory.'})

        # Ensure dispatch_count is initialized properly
        if item.dispatch_count is None:
            item.dispatch_count = 0

        # Update the quantity of the item and increase dispatch count
        item.quantity -= dispatch_quantity
        item.dispatch_count += 1
        db.session.commit()

        print(f"Dispatched {dispatch_quantity} of {item.item_name}. Remaining quantity: {item.quantity}.")
        return jsonify({'status': 'success', 'message': f'Dispatched {dispatch_quantity} of {item.item_name}.'})

    except Exception as e:
        print(f"Error during dispatch: {e}")
        db.session.rollback()
        return jsonify({'status': 'error', 'message': 'An error occurred while dispatching the item.'})


# Route for deleting suppliers
@app.route('/delete_supplier', methods=['POST'])
def delete_supplier():
    try:
        supplier_id = request.json.get('id')
        supplier = Supplier.query.get(supplier_id)

        if not supplier:
            return jsonify({'status': 'error', 'message': 'Supplier not found.'})

        db.session.delete(supplier)
        db.session.commit()

        print(f"Supplier {supplier.name} deleted successfully.")
        return jsonify({'status': 'success', 'message': f'Supplier {supplier.name} deleted successfully.'})

    except Exception as e:
        print(f"Error during deletion: {e}")
        db.session.rollback()
        return jsonify({'status': 'error', 'message': 'An error occurred while deleting the supplier.'})


# Function to send email
def send_email(supplier, item, order_quantity):
    try:
        # Email configuration
        sender_email = "supplier750@gmail.com"
        sender_password = "Pending1@"
        smtp_server = "smtp.gmail.com"
        smtp_port = 587

        receiver_email = supplier.email
        subject = f"Reorder Request for {item.item_name}"
        body = f"Dear {supplier.name},\n\nWe need to reorder {order_quantity} units of {item.item_name}. Please confirm the order at your earliest convenience.\n\nBest regards,\nSmartSort Team"

        # Setup email message
        message = MIMEMultipart()
        message["From"] = sender_email
        message["To"] = receiver_email
        message["Subject"] = subject
        message.attach(MIMEText(body, "plain"))

        # Send email
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, receiver_email, message.as_string())
        server.quit()

        print(f"Email sent to {supplier.email} for item {item.item_name}.")

    except Exception as e:
        print(f"Error sending email: {e}")


# Scheduled task to check inventory and send emails
@scheduler.task('interval', id='check_inventory', seconds=3600)
def check_inventory():
    low_inventory_threshold = 5  # Define a threshold for low inventory
    for item in Inventory.query.all():
        if item.quantity <= low_inventory_threshold:
            supplier = Supplier.query.filter_by(sku=item.sku).first()
            if supplier:
                # Determine if the product is in high demand
                if item.dispatch_count > 10:  # Example logic for high demand
                    order_quantity = int(item.quantity * 1.25)  # Increase order by 25%
                else:
                    order_quantity = item.quantity  # Order the same amount

                # Send email to supplier
                send_email(supplier, item, order_quantity)


# Start the scheduler
scheduler.start()

# Initialize the database and run the app
if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Create tables if they don't exist

    app.run(debug=True)
