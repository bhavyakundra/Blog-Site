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



def send_notification(post, users):
    base_url = request.url_root
    custom_link = "http://44.210.196.10:8000/" 

    for user in users:
        # Create a Jinja2 template
        template = Template("""
        <html>
        <head></head>
        <body>
            <h1>New Post</h1>
            <h2>{{ post.title }}</h2>
<<<<<<< Updated upstream
            <p><a href="{{  }}">Blog</a> Blog Link</p>
            <p><a href="{{ unsubscribe_url }}">Click here</a> to unsubscribe .</p>
                            
=======
            <p><a href="{{ custom_link }}">Home Page</a> To visit our website.</p>
            <p><a href="{{ unsubscribe_url }}">Click Here</a> To Unsubscribe.</p>
>>>>>>> Stashed changes
        </body>
        </html>
        """)
        # Generate the unsubscribe URL with the user's ID
        unsubscribe_url = f"{base_url}/unsubscribe?user_id={user.id}"

        # Render the template with the post title, custom link, and unsubscribe URL
        html_content = template.render(post=post, custom_link=custom_link, unsubscribe_url=unsubscribe_url)

        # Send the email
        send_email(user.email, 'New Post', html_content)
        print(send_email)


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
            
            
            if (current_user.is_admin):
                send_notification(post, User.query.filter_by(is_subscribed=True,send_notifications=True).all())  
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


from flask import Flask, request, current_app, url_for, send_from_directory
import os
from werkzeug.utils import secure_filename


# Define the directory where uploaded files are stored
UPLOAD_FOLDERS = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads_image/')
# app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# ... Rest of your code ...

# Define the 'uploaded_file' endpoint to serve uploaded files
@posts.route('/uploads_image/<filename>')
def uploaded_file(filename):
    return send_from_directory(current_app.config['UPLOAD_FOLDERS'], filename)
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif'}

# Function to check if the file extension is allowed
def allowed_files(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@posts.route('/upload-image', methods=['POST'])
def upload_image():
    uploaded_file = request.files['upload']  # 'upload' matches the input name attribute
    if uploaded_file:
        # Validate the file and save it to the desired location on your server
        if allowed_files(uploaded_file.filename):
            filename = secure_filename(uploaded_file.filename)
            file_path = os.path.join(current_app.config['UPLOAD_FOLDERS'], filename)
            uploaded_file.save(file_path)

            # Generate the URL for the uploaded image
            uploaded_image_url = url_for('posts.uploaded_file', filename=filename, _external=True)

            return '''
                <script>
                    window.parent.CKEDITOR.tools.callFunction(%s, '%s', 'Image uploaded successfully.');
                </script>
            ''' % (request.args.get('CKEditorFuncNum'), uploaded_image_url)
        else:
            return '''
                <script>
                    window.parent.CKEDITOR.tools.callFunction(%s, '', 'Invalid file type.');
                </script>
            ''' % request.args.get('CKEditorFuncNum')
    else:
        return '''
            <script>
                window.parent.CKEDITOR.tools.callFunction(%s, '', 'Failed to upload image.');
            </script>
        ''' % request.args.get('CKEditorFuncNum')