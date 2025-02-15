# email_service.py
from flask_mail import Mail, Message
import os
from flask import render_template_string

mail = Mail()

# HTML template for welcome email
WELCOME_EMAIL_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .header { background: #f8f9fa; padding: 20px; text-align: center; }
        .content { padding: 20px; }
        .footer { background: #f8f9fa; padding: 20px; text-align: center; }
    </style>
</head>
<body>
    <div class="header">
        <h1>Welcome to Our Library!</h1>
    </div>
    <div class="content">
        <h2>Hello {{username}},</h2>
        <p>Thank you for registering with our library management system. We're excited to have you join us!</p>
        
        <h3>Your Account Details:</h3>
        <p>Username: {{username}}</p>
        <p>Email: {{email}}</p>
        
        <h3>What You Can Do:</h3>
        <ul>
            <li>Borrow and manage books</li>
            <li>Write reviews and ratings</li>
            <li>Participate in forum discussions</li>
            <li>Track your reading history</li>
        </ul>
        
        <p>To get started, simply log in to your account and explore our collection of books.</p>
        
        <p>If you have any questions, feel free to contact our support team.</p>
    </div>
    <div class="footer">
        <p>Best regards,<br>Your Library Team</p>
    </div>
</body>
</html>
"""

def send_welcome_email(user):
    """
    Send welcome email to newly registered users
    
    Args:
        user: User object containing username and email
    """
    try:
        msg = Message(
            'Welcome to Our Library!',
            sender=os.getenv('MAIL_DEFAULT_SENDER'),
            recipients=[user.email]
        )
        
        # Render the HTML template with user data
        msg.html = render_template_string(
            WELCOME_EMAIL_TEMPLATE,
            username=user.username,
            email=user.email
        )
        
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Error sending welcome email: {str(e)}")
        return False

# Add a new template for borrowed book notification
BORROWED_BOOK_EMAIL_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .header { background: #f8f9fa; padding: 20px; text-align: center; }
        .content { padding: 20px; }
        .footer { background: #f8f9fa; padding: 20px; text-align: center; }
        .book-details { background: #f1f1f1; padding: 15px; border-radius: 5px; }
    </style>
</head>
<body>
    <div class="header">
        <h1>Borrowed Book Added</h1>
    </div>
    <div class="content">
        <h2>Hello {{username}},</h2>
        <p>You've added a new book to your borrowed list:</p>
        
        <div class="book-details">
            <h3>Book Details:</h3>
            <p><strong>Title:</strong> {{book_title}}</p>
            <p><strong>Author:</strong> {{author}}</p>
            <p><strong>Borrow Date:</strong> {{borrow_date}}</p>
            <p><strong>Due Date:</strong> {{due_date}}</p>
        </div>
        
        <p>Please remember to return the book by the due date.</p>
        
        <p>If you have any questions, please contact the library support.</p>
    </div>
    <div class="footer">
        <p>Best regards,<br>Your Library Team</p>
    </div>
</body>
</html>
"""

def send_borrowed_book_notification(user, book_details):
    """
    Send notification email when a book is added to borrowed list
    
    Args:
        user: User object 
        book_details: Dictionary containing book information
    """
    try:
        msg = Message(
            'New Borrowed Book Notification',
            sender=os.getenv('MAIL_DEFAULT_SENDER'),
            recipients=[user.email]
        )
        
        # Render the HTML template with user and book data
        msg.html = render_template_string(
            BORROWED_BOOK_EMAIL_TEMPLATE,
            username=user.username,
            book_title=book_details['book_title'],
            author=book_details['author'],
            borrow_date=book_details['borrow_date'],
            due_date=book_details['due_date']
        )
        
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Error sending borrowed book notification: {str(e)}")
        return False