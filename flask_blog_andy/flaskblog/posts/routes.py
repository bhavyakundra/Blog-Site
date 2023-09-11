import os
import uuid
from flaskblog import db, create_app
from jinja2 import Template
from flaskblog.models import Post, File,User
from flaskblog.posts.forms import PostForm
from werkzeug.utils import secure_filename
from flask_login import current_user, login_required
from flask import render_template, url_for, flash, redirect, request, current_app, Blueprint
from flaskblog.users.utils import send_email
posts = Blueprint('posts', __name__)
app = create_app

ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
ALLOWED_PDF_EXTENSIONS = {'pdf'}
ALLOWED_EXCEL_EXTENSIONS = {'xlsx', 'xls'}

def get_file_extension(filename):
    return os.path.splitext(filename)[1].lower()

def allowed_file(filename, allowed_extensions):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

from jinja2 import Template

def send_notification(post, users):
    base_url = request.url_root 
    for user in users:
        # Create a Jinja2 template
        template = Template("""
        <html>
        <head></head>
        <body>
            <h1>New Post!</h1>
            <h2>{{ post.title }}</h2>
            <p><a href="{{ unsubscribe_url }}">Click here</a> to unsubscribe .</p>
        </body>
        </html>
        """)

        # Generate the unsubscribe URL with the user's ID
        unsubscribe_url = f"{base_url}/unsubscribe?user_id={user.id}"

        # Render the template with the post title and unsubscribe URL
        html_content = template.render(post=post, unsubscribe_url=unsubscribe_url)

        # Send the email
        send_email(user.email, 'New Post', html_content)

@posts.route("/post/new", methods=['GET', 'POST'])
@login_required
def new_post():
    if (current_user.can_add_post or current_user.is_admin):
        form = PostForm()
        if form.validate():
            post = Post(title=form.title.data, content=form.content.data, author=current_user)
            db.session.add(post)
            db.session.commit()

            # Handle uploaded files
            allowed_extensions_image = ALLOWED_IMAGE_EXTENSIONS
            allowed_extensions_pdf = ALLOWED_PDF_EXTENSIONS
            allowed_extensions_excel = ALLOWED_EXCEL_EXTENSIONS

            for uploaded_file in request.files.getlist('files'):
                original_filename = secure_filename(uploaded_file.filename)
                file_extension = get_file_extension(original_filename)
                filename = secure_filename(original_filename)

                if allowed_file(original_filename, allowed_extensions_image):
                    file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                    post.image_filename = filename  # Set Image filename
                elif allowed_file(original_filename, allowed_extensions_pdf):
                    file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                    post.pdf_filename = filename  # Set PDF filename
                elif allowed_file(original_filename, allowed_extensions_excel):
                    file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                    post.excel_filename = filename  # Set Excel filename
                else:
                    # Handle unsupported file types
                    continue

                uploaded_file.save(file_path)
                file_obj = File(filename=filename, posts=[post])
                db.session.add(file_obj)

            db.session.commit()
            
            
            if current_user.is_admin:
                send_notification(post, User.query.filter_by(is_subscribed=True,send_notifications=True).all())  
                print("userrrrr",User.query.filter_by(send_notifications=True,is_subscribed=True).all())
                flash('Your post has been created!', 'success')
                return redirect(url_for('main.home'))

        return render_template('create_post.html', title='New Post', form=form, legend='New Post')
    
    else:
        flash('You do not have permission to add the post.', 'danger')
        return redirect(url_for('main.home'))


@posts.route("/post/<int:post_id>")
@login_required
def post(post_id):
    post = Post.query.get_or_404(post_id)
    return render_template('post.html', title=post.title, post=post)


@posts.route("/post/<int:post_id>/update", methods=['GET', 'POST'])
@login_required
def update_post(post_id):
    post = Post.query.get_or_404(post_id)

    if (current_user.can_update_post or current_user.is_admin) and post.author == current_user:
        form = PostForm()

        # Store the previous file attachments
        previous_image = post.image_filename
        previous_pdf = post.pdf_filename
        previous_excel = post.excel_filename

        if form.validate():
            # Update post title and content
            post.title = form.title.data
            post.content = form.content.data

            # Handle uploaded files
            allowed_extensions_image = ALLOWED_IMAGE_EXTENSIONS
            allowed_extensions_pdf = ALLOWED_PDF_EXTENSIONS
            allowed_extensions_excel = ALLOWED_EXCEL_EXTENSIONS

            # Restore previous filenames if no new files are uploaded
            if not request.files.getlist('files'):
                post.image_filename = previous_image
                post.pdf_filename = previous_pdf
                post.excel_filename = previous_excel

            for uploaded_file in request.files.getlist('files'):
                original_filename = secure_filename(uploaded_file.filename)
                file_extension = get_file_extension(original_filename)
                filename = secure_filename(original_filename)
            
                if allowed_file(uploaded_file.filename, allowed_extensions_image):
                    print("Processing image file...")
                    file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                    post.image_filename = filename  # Set Image filename
                elif allowed_file(uploaded_file.filename, allowed_extensions_pdf):
                    print("Processing PDF file...")
                    file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                    post.pdf_filename = filename  # Set PDF filename
                elif allowed_file(uploaded_file.filename, allowed_extensions_excel):
                    print("Processing Excel file...")
                    file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                    post.excel_filename = filename  # Set Excel filename
                else:
                    # Handle unsupported file types
                    continue

                uploaded_file.save(file_path)
                file_obj = File(filename=filename, posts=[post])
                db.session.add(file_obj)

            db.session.commit()
            
            flash('Your post has been updated!', 'success')
            return redirect(url_for('main.home'))

        elif request.method == 'GET':
            form.title.data = post.title
            form.content.data = post.content

        # Restore previous file attachments if no new files are uploaded
        form.files.data = None  # Clear file data
        if not form.files.data and previous_image:
            form.files.data = [previous_image]
        if not form.files.data and previous_pdf:
            form.files.data = [previous_pdf]
        if not form.files.data and previous_excel:
            form.files.data = [previous_excel]

        return render_template('create_post.html', title='Update Post', form=form, legend='Update Post')
    else:
        flash('You do not have permission to update this post.', 'danger')
        return redirect(url_for('main.home'))


@posts.route("/post/<int:post_id>/delete", methods=['POST'])
@login_required 
def delete_post(post_id):
    if current_user.is_admin or current_user.can_delete_post:
        post = Post.query.get_or_404(post_id)
        db.session.delete(post)
        db.session.commit()
        print("######")
        flash('The post has been deleted!', 'success')
        
        return redirect(url_for('admin.admin_page'))
    
    else:
        flash('You do not have permission to delete posts.', 'danger')
        return redirect(url_for('admin.admin_page'))
    

@posts.route("/post/<int:post_id>/file/<int:file_id>/delete", methods=['POST'])
@login_required
def delete_file(post_id, file_id):
    post = Post.query.get_or_404(post_id)
    file_to_delete = File.query.get_or_404(file_id)

    # Check if the current user has permission to delete the file
    if current_user.can_update_post or current_user.is_admin:
        try:
            # Remove the file from the post's files list and delete it
            if file_to_delete in post.files:
                post.files.remove(file_to_delete)
                db.session.delete(file_to_delete)
                db.session.commit()
                flash('File deleted successfully.', 'success')
            else:
                flash('File not found.', 'danger')
        except Exception as e:
            flash('An error occurred while deleting the file.', 'danger')
            db.session.rollback()
    else:
        flash('You do not have permission to delete the file.', 'danger')

    return redirect(url_for('posts.post', post_id=post_id))