# Pizzeria System

This is a Python project that implements a system for a pizzeria. It allows customers to choose and order pizzas from an app, and tracks the order status using a background task.

## Installation

To run this project, you need to have Docker and Docker Compose installed on your machine. You can follow the instructions from the official website² to install them.

To build and start the containers, run the following command in the project directory:

```bash
docker-compose up -d
```

This will create three containers: one for the MySQL database, one for the Redis broker, and one for the Flask app.

## Usage

To use the app, you can send HTTP requests to `http://localhost:5000/` using a tool like Postman or curl. The app exposes the following endpoints:

- `GET /bases`: Get all pizza bases
- `GET /cheeses`: Get all cheese types
- `GET /toppings`: Get all toppings
- `POST /pizzas`: Create a pizza
- `POST /orders`: Create an order
- `GET /orders/<int:order_id>`: Get an order by ID

The app also uses Celery to run a background task that tracks the order status based on time. You can monitor the task progress using a tool like Flower or Celery CLI.

## Contributing

If you want to contribute to this project, please follow the code style and documentation standards. You can also run tests using pytest or unittest.
