#Shon Bennett 
#CMSC 455 Assignment 2 Cart Service

import os
from flask import Flask, jsonify, request
import requests
import logging

#make Flask application 
app = Flask(__name__)

user_cart = [] #user's cart starts off as empty 

# user_id acts as the specific cart 
@app.route('/cart/<int:user_id>', methods=['GET'])
def get_cart(user_id):
    app.logger.info("Requesting to see the cart content")
    return jsonify({"Cart Content": user_cart})

# add specified amount of product to cart + decrease the product service inventory by specified amount  
@app.route('/cart/<int:user_id>/add/<int:product_id>/<int:amount_to_add>', methods=['POST'])
def add(user_id, product_id, amount_to_add):
    #in case more than what is available is requested
    given_remainder = False
    remaining_amount = 0

    #gather product needed via the ID; this will return a Response object  
    cart_url = f"https://product-service-1bd0.onrender.com/products/{product_id}"
    result = requests.get(cart_url)
    app.logger.info("User is attempting to add items to their cart")
    
    #convert the Response object into JSON
    product = result.json()
    
    #if request more than what is in stock, give them what was remaining in stock
    if amount_to_add > product['product']['quantity']:
        app.logger.info(f"You have requested more than what currently is in stock. The maximum amount possible ({product['product']['quantity']}) was added to your cart.")
        remaining_amount = product['product']['quantity']
        product['product']['quantity'] = 0
        given_remainder = True
    else:
        #subtract to the quantity from product service element 
        product['product']['quantity'] -= amount_to_add

    #use product POST method and overwrite the original product in product service's array 
    args = {
        "name":product['product']['name'],
        "price":product['product']['price'],
        "product_id":product_id,
        "quantity":product['product']['quantity']
    }
    result = requests.post(f"https://product-service-1bd0.onrender.com/products", json=args)
    assert result.status_code != 404, "Cart's call to Product Service POST method failed (method: add)!!!"
    
    #finally add the requested amount to user cart (if too much was requested, add remaining amount to cart)
    if given_remainder == True:
        product['product']['quantity'] = remaining_amount
    else:
        product['product']['quantity'] = amount_to_add

    flag = False
    for items in user_cart:
        if items['product']['product_id'] == product_id:
            items['product']['quantity'] += product['product']['quantity']
            flag = True

    if flag == False:
        user_cart.append(product)

    return jsonify({"Added to Cart": user_cart}) 

# remove specified amount of product from cart + increase the product service inventory by specified amount  
@app.route('/cart/<int:user_id>/remove/<int:product_id>/<int:amount_to_remove>', methods=['POST'])
def remove(user_id, product_id, amount_to_remove):
    if len(user_cart) == 0:
        app.logger.info("There is nothing in the cart to remove.")
        return jsonify({"Cart Content": user_cart})

    #in case user tries to remove more than what they have in their cart 
    remove_remainder = False
    amount_to_send_back = 0

    #gather product needed via the ID; this will return a Response object  
    cart_url = f"https://product-service-1bd0.onrender.com/products/{product_id}"
    result = requests.get(cart_url)
    app.logger.info("User is attempting to remove items from cart")
    
    #convert the Response object into JSON
    product = result.json()

    #grab the item from the user's cart and test if they requested to remove too much
    item = user_cart[0]
    args = {}
    for items in user_cart:
        if items['product']['product_id'] == product_id:
            item = items

    #if request more than what is in stock, give them what was remaining in stock
    if amount_to_remove > item['product']['quantity']:
        app.logger.info(f"You have requested to remove more than what is in your cart. The maximum amount possible ({item['product']['quantity']}) was removed from your cart.")
        amount_to_send_back = item['product']['quantity']
        item['product']['quantity'] = 0
        remove_remainder = True

        #use product POST method and overwrite the original product in product service's array 
        args = {
            "name":product['product']['name'],
            "price":product['product']['price'],
            "product_id":product_id,
            "quantity":product['product']['quantity'] + amount_to_send_back
        }
    else:
        #send back requested amount to product inventory
        item['product']['quantity'] -= amount_to_remove
        #use product POST method and overwrite the original product in product service's array 
        args = {
            "name":product['product']['name'],
            "price":product['product']['price'],
            "product_id":product_id,
            "quantity":product['product']['quantity'] + amount_to_remove
        }


    result = requests.post(f"https://product-service-1bd0.onrender.com/products", json=args)
    assert result.status_code != 404, "Cart's call to Product Service POST method failed (method: remove)!!!"
    
    #if this is true, that means the quantity is 0. just remove the item altogether 
    if remove_remainder == True:
            for x in range(len(user_cart)):
                if user_cart[x]['product']['product_id'] == product_id:
                    user_cart.pop(x)
                    return jsonify({"Removed from Cart. Here is new cart content": user_cart})
    
    return jsonify({"Removed from Cart. Here is new cart content": user_cart}) 

if __name__ == '__main__':
    #the string of zeros indicates that we are accepting from all addresses 
    app.run(debug=True,host='0.0.0.0', port=8080) #specify that this is on another port (at first they were both on port 5000)
