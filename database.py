from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column,Integer,String , create_engine

base = declarative_base()

class order(base):

    __tablename__ = 'Order'
    id = Column(Integer,autoincrement=True,primary_key=True)
    product = Column(String)
    date = Column(String)
    quantity = Column(String)
    price = Column(String)
    total_amount = Column(String)
if __name__ == "__main__" :
    engine = create_engine("sqlite:///order.sqlite3")
    base.metadata.create_all(engine)
