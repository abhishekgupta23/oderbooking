import streamlit as st
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import order

engine = create_engine("sqlite:///order.sqlite3")
Session = sessionmaker(bind=engine)
session = Session()

sidebar = st.sidebar

choices = ['Add Data', 'Read Data', 'Delete Data']
selChoice = sidebar.selectbox(options=choices, label="Choose Option")


def addOrder():
    st.header("Add Order Data")

    product = st.text_input("Enter Product Name")
    date = st.text_input("Enter Date")
    price = st.text_input("Enter Price")
    quantity = st.text_input("Enter Quantity")
    btn = st.button('Save Order')
    if btn:
        amount = int(price) * int(quantity)
        try:
            ord1 = order(product=product, date=date, price=price,
                         quantity=quantity, total_amount=amount)
            session.add(ord1)
            session.commit()
            st.success('Data Saved')
            data = session.query(order).filter_by(product = product).first()
            st.title("Bill")
            st.write(data.date)
            st.write("order id ===========>")
            st.write(data.id)
            st.write("Product ============>")
            st.write(data.product)
            st.write("Price ============>")
            st.write(data.price)
            st.write("quantity ============>")
            st.write(data.quantity)
            st.write("Total Amount ============>")
            st.write(data.total_amount)

        except Exception as e:
            print(e)
            st.error('Something went wrong')


def readOrder():
    st.header("Search Product")
    name = st.text_input('Enter Product id')
    btn = st.button('Find Product')
    if btn:
        try:
            data = session.query(order).filter_by(id = name).first()
            st.write(data.product)
            st.write(data.date)
            st.write(data.total_amount)
        except Exception as e:
                print(e)
                st.error('Something went wrong')


def deleteOrder():
    id = int(st.text_input('Enter ID to delete',0))
    try:
        if id:
            data = session.query(order).filter_by(id = id).first()
            st.write(data.product)
            st.write(data.date)
            st.write(data.total_amount)
            btn = st.button("Delete")
            if btn:
                session.delete(data)
                session.commit()
                st.success("Delete")
    except Exception as e:
                print(e)
                st.error('Something went wrong')

if selChoice == choices[0]:
    addOrder()
elif selChoice == choices[1]:
    readOrder()
elif selChoice == choices[2]:
    deleteOrder()