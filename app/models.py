from datetime import datetime
from app import db
from sentence_transformers import SentenceTransformer
import numpy as np
from sqlalchemy.types import LargeBinary  # Add this import
from dotenv import load_dotenv
import os 
import semantic_models

class Author(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    books = db.relationship('Book', backref='author', lazy=True)



class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    price = db.Column(db.Float, nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('author.id'), nullable=True, default=None)
    added_on = db.Column(db.DateTime, default=datetime.utcnow)
    editorial = db.Column(db.String(200), nullable=True)
    gender = db.Column(db.String(200), nullable=True)
    index = db.Column(db.String(200), nullable=True)
    edition_year = db.Column(db.String(200), nullable=True)
    embedding = db.Column(db.LargeBinary, nullable=True)   
    

    def generate_embedding(self):
        author = Author.query.get(self.author_id)
        author_name = author.name if author else ''
        text = f"{self.title} {author_name} {self.editorial} {self.edition_year} {self.description or ''}".strip()
        
        if not text:
            self.embedding = None  # Handle empty text case
        else:
            embedding =semantic_models.embed_text([text])            
            self.embedding = np.array(embedding).tobytes()
            # print(f'Embedding saving shape: {np.frombuffer(self.embedding, dtype=np.float32).shape}')

    def save(self):
        if self.embedding is None:
            self.generate_embedding()
        db.session.add(self)
        db.session.commit()


class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    orders = db.relationship('Order', backref='customer', lazy=True)

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'), nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    order_date = db.Column(db.DateTime, default=datetime.utcnow)
    quantity = db.Column(db.Integer, default=1)
