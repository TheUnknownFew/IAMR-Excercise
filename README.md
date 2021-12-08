# IAMR-Excercise

Architecture Activity:

Suppose we are in an organization whose goal is to help small businesses. We've started organizing a weekly farmers market to give small/local businesses a platform to reach customers. We want to create an app that helps these businesses sign up to our farmers market, manage inventory, fulfill order, analyze performance data, and advertise their goods.

The farmers market has many vendors. Each vendor has multiple bins, and each bin can contain multiple products of the same type (ex. an apple bin, corn bin, another apple bin, etc). We would like you to design and optionally implement a simple backend for this new app, in particular you should design a database structure for storing information and design/create REST endpoints for accessing data.

A few example use cases to consider for your design:

- The configuration of the farmers market and building of a map of the locations of each product and access pathways.
- A vendor makes a sale and needs to update the stock of a product
- A vendor wants to know how much stock they have left
- A customer orders multiple products and the vendor needs the best route to fulfill the order
- A vendor wants to know how long it takes to fill each order
- A customer wants to know where in the market they can buy a particular product

We want to know what tools and frameworks could be used to help with the implementation and how you would build a cost model for using these tools.

For the database aspect we would like you to at least talk through what a schema for the database might look like. However, in your code you do not actually need to implement the database unless you want to. Feel free to use simple language data structures for storing info accessed by REST endpoints instead. Please discuss how you would document the REST endpoints and keep the documentation up to date.

Also consider the security of the data and access to the data.  How would we keep information separate for each vendor?  How would you keep a hacker from accessing the API?

If you decide to implement any of the services we would prefer if you did this in python, but feel free to use any language you are comfortable with.

During the interview you can show us your design/implementation and talk us through it and any decisions you made along the way.

This is not so different from what the Enterprise Software team does at IAM. The farmers market is an automated warehouse where part of what we do is manage product inventory, provide product locations to robots, and create tools for accessing, modifying, and viewing data.

---
# Citations

- boilerplate flask application - https://github.com/pallets/flask/tree/1.1.2/examples/tutorial
- setting up flask in pycharm   - https://medium.com/@mushtaque87/flask-in-pycharm-community-edition-c0f68400d91e