# routes.py
import logging
import os
import uuid
from datetime import datetime
from PIL import Image
from flask import (
    render_template, redirect, url_for, flash, 
    request, current_app
)
from flask_login import (
    login_user, logout_user, login_required, 
    current_user
)
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

from app import app
from extensions import db
from models import (
    User, Book, BorrowedBook, ForumPost, 
    ForumComment, UserBook
)
from email_service import (
    send_welcome_email, send_borrowed_book_notification
)

# Configuration
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)

UPLOAD_FOLDER = 'static/forum_uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Helper Functions
def allowed_file(filename):
    """Check if the file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def process_image(file, max_size=(800, 600), quality=85):
    """Process and optimize uploaded images"""
    img = Image.open(file)
    img.thumbnail(max_size, Image.LANCZOS)
    
    filename = f"{uuid.uuid4()}.jpg"
    filepath = os.path.join(current_app.root_path, UPLOAD_FOLDER, filename)
    
    img.save(filepath, optimize=True, quality=quality)
    return filename

# Basic Routes
# @app.route('/')
# def index():
#     """Home page route"""
#     books = Book.query.all()
#     return render_template('index.html', books=books)

# Authentication Routes
@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration route"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        try:
            username = request.form.get('username')
            email = request.form.get('email')
            password = request.form.get('password')
            
            new_user = User(
                username=username,
                email=email,
                password=generate_password_hash(password, method='pbkdf2:sha256'),
                created_at=datetime.utcnow()
            )

            db.session.add(new_user)
            db.session.commit()

            try:
                email_sent = send_welcome_email(new_user)
                if email_sent:
                    flash('Registration successful! Please check your email for login details.', 'success')
                else:
                    flash('Registration successful! However, welcome email could not be sent.', 'warning')
            except Exception as e:
                logger.error(f"Email sending failed: {str(e)}")
                flash('Registration successful! However, there was an issue sending the welcome email.', 'warning')

            login_user(new_user)
            return redirect(url_for('index'))

        except Exception as e:
            db.session.rollback()
            logger.error(f"Registration error: {str(e)}")
            flash('An error occurred during registration. Please try again.', 'danger')
            return redirect(url_for('register'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login route"""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('index'))
            
        flash('Invalid username or password', 'danger')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    """User logout route"""
    logout_user()
    return redirect(url_for('index'))

# Forum Routes
@app.route('/forum')
def forum():
    """Forum main page route"""
    posts = ForumPost.query.order_by(ForumPost.date_posted.desc()).all()
    return render_template('forum.html', posts=posts)

@app.route('/forum/post', methods=['POST'])
@login_required
def create_post():
    """Create new forum post route"""
    try:
        title = request.form.get('title')
        content = request.form.get('content')
        photo = request.files.get('photo')
        
        photo_filename = None
        if photo and allowed_file(photo.filename):
            photo_filename = process_image(photo)
        
        post = ForumPost(
            user_id=current_user.id,
            title=title,
            content=content,
            photo_filename=photo_filename
        )
        db.session.add(post)
        db.session.commit()
        flash("Post created successfully!", 'success')
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating post: {str(e)}")
        flash("An error occurred. Please try again.", 'danger')
        
    return redirect(url_for('forum'))

@app.route('/forum/comment/<int:post_id>', methods=['POST'])
@login_required
def add_comment(post_id):
    """Add comment to forum post route"""
    content = request.form.get('content')
    comment = ForumComment(post_id=post_id, user_id=current_user.id, content=content)
    try:
        db.session.add(comment)
        db.session.commit()
        flash("Comment added successfully!", 'success')
    except Exception as e:
        db.session.rollback()
        flash("An error occurred. Please try again.", 'danger')
    return redirect(url_for('forum'))

@app.route('/forum/delete_post/<int:post_id>', methods=['POST'])
@login_required
def delete_post(post_id):
    """Delete forum post route"""
    try:
        post = ForumPost.query.get_or_404(post_id)
        db.session.delete(post)
        db.session.commit()
        flash('Post deleted successfully', 'success')
    except Exception as e:
        logger.error(f'Error deleting post: {e}')
        flash('An error occurred while deleting the post', 'danger')
    return redirect(url_for('forum'))

@app.route('/forum/delete_comment/<int:comment_id>', methods=['POST'])
@login_required
def delete_comment(comment_id):
    """Delete forum comment route"""
    comment = ForumComment.query.get_or_404(comment_id)
    if comment.user_id != current_user.id:
        flash('You can only delete your own comments.', 'danger')
        return redirect(url_for('forum'))
        
    try:
        db.session.delete(comment)
        db.session.commit()
        flash("Comment deleted successfully!", 'success')
    except Exception as e:
        db.session.rollback()
        flash("An error occurred. Please try again.", 'danger')
    return redirect(url_for('forum'))

# Book Management Routes
@app.route('/add_borrowed_book', methods=['GET', 'POST'])
@login_required
def add_borrowed_book():
    """Add borrowed book route"""
    if request.method == 'POST':
        title = request.form['title']
        author = request.form['author']
        due_date_str = request.form['due_date']
        
        try:
            due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date()
            borrow_date = datetime.utcnow().date()
            
            new_borrowed_book = UserBook(
                user_id=current_user.id, 
                book_title=title, 
                author=author,
                borrow_date=borrow_date,
                due_date=due_date
            )
            
            db.session.add(new_borrowed_book)
            db.session.commit()

            book_details = {
                'book_title': title,
                'author': author,
                'borrow_date': borrow_date.strftime('%Y-%m-%d'),
                'due_date': due_date.strftime('%Y-%m-%d')
            }

            try:
                email_sent = send_borrowed_book_notification(current_user, book_details)
                if email_sent:
                    flash('Book added to your borrowed list. A notification email has been sent.', 'success')
                else:
                    flash('Book added to your borrowed list. However, the notification email could not be sent.', 'warning')
            except Exception as e:
                logger.error(f"Email sending failed: {str(e)}")
                flash('Book added to your borrowed list. However, there was an issue sending the notification email.', 'warning')

            return redirect(url_for('borrowed_books'))
        except ValueError:
            flash('Invalid date format', 'danger')
        except Exception as e:
            db.session.rollback()
            flash('Error adding book', 'danger')
            logger.error(f"Error adding borrowed book: {str(e)}")
    
    return render_template('add_borrowed_book.html')

@app.route('/borrowed_books')
@login_required
def borrowed_books():
    """View borrowed books route"""
    books = UserBook.query.filter_by(user_id=current_user.id).order_by(UserBook.borrow_date.desc()).all()
    current_date = datetime.utcnow().date()
    return render_template('borrowed_books.html', books=books, current_date=current_date)

@app.route('/mark_returned/<int:book_id>', methods=['POST'])
@login_required
def mark_returned(book_id):
    """Mark book as returned route"""
    book = UserBook.query.get_or_404(book_id)
    
    if book.user_id != current_user.id:
        flash('Unauthorized', 'danger')
        return redirect(url_for('borrowed_books'))
    
    book.is_returned = True
    book.return_date = datetime.utcnow()
    
    try:
        db.session.commit()
        flash('Book marked as returned', 'success')
    except:
        db.session.rollback()
        flash('Error marking book as returned', 'danger')
    
    return redirect(url_for('borrowed_books'))

@app.route('/')
def index():
    """Enhanced home page route with statistics"""
    try:
        # Gather statistics
        users_count = User.query.count()
        books_count = Book.query.count()
        active_borrowers = UserBook.query.filter_by(is_returned=False).distinct(UserBook.user_id).count()
        forum_posts_count = ForumPost.query.count()
        
        # Get available books
        books = Book.query.all()
        
        return render_template('index.html',
                             books=books,
                             users_count=users_count,
                             books_count=books_count,
                             active_borrowers=active_borrowers,
                             forum_posts_count=forum_posts_count)
    except Exception as e:
        logger.error(f"Error loading index page: {str(e)}")
        flash('Error loading page data', 'danger')
        return render_template('index.html', books=[])