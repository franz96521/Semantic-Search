from flask import Blueprint, request, render_template, redirect, url_for
from flask import Blueprint, render_template, request, redirect, url_for, flash
from app import db
from app.models import Author
from app import db
from app.models import Author, Book, Customer, Order
from flask import jsonify
from scipy.spatial.distance import cosine
from sentence_transformers import SentenceTransformer
import numpy as np
from dotenv import load_dotenv
import os 
load_dotenv()

import semantic_models

bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    books = Book.query.all()
    authors = Author.query.all()
    editorials = Book.query.with_entities(Book.editorial).distinct().all()
    return render_template('index.html', books=books,authors=authors,editorials=editorials)

@bp.route('/add_book', methods=['GET', 'POST'])
def add_book():
    if request.method == 'POST':
        title = request.form.get('title')
        price = request.form.get('price')
        author_id = request.form.get('author_id')

        if not title or not price or not author_id:
            flash('All fields are required!', 'error')
            return redirect(url_for('main.add_book'))

        try:
            price = float(price)
            author_id = int(author_id)
        except ValueError:
            flash('Price and Author ID must be valid numbers!', 'error')
            return redirect(url_for('main.add_book'))
        
        description = request.form.get('description')
        editorial = request.form.get('editorial')
        edition_year = request.form.get('edition_year')
        gender = request.form.get('gender')

        if not Author.query.get(author_id):
            flash('Author ID does not exist!', 'error')
            return redirect(url_for('main.add_book'))

        new_book = Book(title=title, price=price, author_id=author_id, description=description, editorial=editorial, edition_year=edition_year,gender=gender)
        db.session.add(new_book)
        db.session.commit()
        flash('Book added successfully!', 'success')
        return redirect(url_for('main.index'))

    authors = Author.query.all()
    return render_template('add_book.html', authors=authors)

@bp.route('/add_author', methods=['GET', 'POST'])
def add_author():
    if request.method == 'POST':
        name = request.form.get('name')

        if not name:
            flash('Name is required!', 'error')
            return redirect(url_for('main.add_author'))

        new_author = Author(name=name)
        db.session.add(new_author)
        db.session.commit()
        flash('Author added successfully!', 'success')
        return redirect(url_for('main.index'))

    return render_template('add_author.html')


@bp.route('/semantic_search', methods=['POST'])
def semantic_search():
    query = request.form.get('query')
    author = request.form.get('authorQuery')
    year = request.form.get('yearQuery')
    editorial = request.form.get('editorialQuery')
    gender = request.form.get('genderQuery')
    
    print(f'Query: {query}, Author: {author} year: {year} editorial: {editorial} gender:{gender}')
    # if not query:
    #     return jsonify([])  # Return empty list if no query is provided
    
    query_embedding = semantic_models.embed_text([query])
    
    # print(f'Query Embedding dimension: {query_embedding.shape}, {query_embedding.dtype}')
    
    books = Book.query.all()
    results = []
    
    for book in books:
        print(f'Book: {book.gender}')
        if book.embedding:
            book_embedding = np.frombuffer(book.embedding,dtype=np.float32)
            # print(f'Book Embedding dimension: {book_embedding.shape}')
            similarity = 1 - cosine(query_embedding, book_embedding)
            results.append((book, similarity))
        else:
            results.append((book, 0))  # Handle books with no embedding
# filter by author
    if author:
        results = [result for result in results if author.lower() in result[0].author.name.lower()]
    
    if year:
        results = [result for result in results if year.lower() in str(result[0].edition_year).lower()]
            
    if editorial:
        results = [result for result in results if editorial.lower() in str(result[0].editorial).lower()]
    
    if gender:
        results = [result for result in results if gender.lower() in str(result[0].gender).lower()]
        
    # remove duplicates
    results = list(set(results))

    results.sort(key=lambda x: x[1], reverse=True)  # Sort by similarity
    
    return jsonify([{
        'title': book.title,
        'author': book.author.name,
        'price': book.price,
        'description': book.description,
        'gender':book.gender,
        'editorial':book.editorial,
        'edition_year':book.edition_year,        
    } for book, _ in results[:20]])  # Return top 10 results

@bp.route('/order/<int:book_id>', methods=['POST'])
def order(book_id):
    book = Book.query.get_or_404(book_id)
    customer_id = int(request.form['customer_id'])
    quantity = int(request.form['quantity'])
    new_order = Order(book_id=book.id, customer_id=customer_id, quantity=quantity)
    db.session.add(new_order)
    db.session.commit()
    return redirect(url_for('main.index'))

@bp.route('/add_author_ajax', methods=['POST'])
def add_author_ajax():
    name = request.form.get('name')
    if name:
        new_author = Author(name=name)
        db.session.add(new_author)
        db.session.commit()
        return jsonify(success=True, author={'id': new_author.id, 'name': new_author.name})
    return jsonify(success=False)


@bp.route('/search_authors', methods=['POST'])
def search_authors():
    author_query = request.form.get('authorQuery', '')
    # Perform your semantic search on authors
    results = Book.query.join(Author).filter(Author.name.contains(author_query)).all()
    books = [{
        'title': book.title,
        'author': book.author.name,
        'price': book.price,
        'description': book.description
    } for book in results]
    return jsonify(books)