from app import create_app, db
from app.models import Book

app = create_app()

with app.app_context():
    books = Book.query.all()
    for book in books:
        if book.embedding is not None:
            continue
        book.generate_embedding()
        book.save()
    print('Embeddings generated and saved successfully!')
    
    
if __name__ == '__main__':
    app.run(debug=True)
