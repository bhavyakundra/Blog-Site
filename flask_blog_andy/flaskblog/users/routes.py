from flask import render_template, url_for, flash, redirect, request, Blueprint
from flask_login import login_user, current_user, logout_user, login_required
from flaskblog.models import User, Post
from flaskblog.users.forms import (RegistrationForm, LoginForm, UpdateAccountForm,
                                   RequestResetForm, ResetPasswordForm)
from flaskblog.users.utils import save_picture, send_reset_email
from flaskblog import db, bcrypt
from flask_mail import Message
from flaskblog import mail
from functools import wraps
from flask import abort

users = Blueprint('users', __name__)


@users.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))  # if user is already logged in, redirect to home page
    form = RegistrationForm()
    if form.validate():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        is_admin = True if form.username.data.lower() == 'admin' else False
        user = User(username=form.username.data, email=form.email.data, password=hashed_password,is_admin=is_admin)
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created! You are now able to log in', 'success')
        return redirect(url_for('users.login'))
    return render_template('register.html', title='Register', form=form)


@users.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))  # if user is already logged in, redirect to home page
    form = LoginForm()
    if form.validate():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('main.home'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
    return render_template('login.html', title='Login', form=form)


@users.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('main.home'))


@users.route("/account", methods=['GET', 'POST'])
@login_required
def account():
    form = UpdateAccountForm()
    if form.validate():
        if form.picture.data:
            picture_file = save_picture(form.picture.data, current_user.id)
            if picture_file:
                current_user.image_file = picture_file
                db.session.commit()  # Commit changes to the database
                flash('Your account has been updated!', 'success')
                return redirect(url_for('users.account'))
        current_user.username = form.username.data
        current_user.email = form.email.data
        db.session.commit()
        flash('Your account has been updated!', 'success')
        return redirect(url_for('users.account'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
    image_file = url_for('static', filename='profile_pics/' + current_user.image_file)
    return render_template('account.html', title='Account', image_file=image_file, form=form)



@users.route("/user/<string:username>")
def user_posts(username):
    page = request.args.get('page', 1, type=int)
    user = User.query.filter_by(username=username).first_or_404()
    posts = Post.query.filter_by(author=user)\
        .order_by(Post.date_posted.desc())\
        .paginate(page=page, per_page=5)
    return render_template('user_posts.html', posts=posts, user=user)


@users.route('/reset_password', methods=['GET', 'POST'])
def reset_request():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    form = RequestResetForm()
    if form.validate():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            token = user.get_reset_token()
            msg = Message('Password Reset Request', sender='noreply@demo.com', recipients=[user.email])
            msg.body = f'''To reset your password, visit the following link:
{url_for('users.reset_token', token=token, _external=True)}

If you did not make this request, simply ignore this email.
'''
            mail.send(msg)
            flash('An email has been sent with instructions to reset your password.', 'info')
            return redirect(url_for('users.login'))
        else:
            flash('Email does not exist. Please register first.', 'danger')
    return render_template('reset_request.html', title='Reset Password', form=form)


@users.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_token(token):
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    user = User.verify_reset_token(token)
    if not user:
        flash('That is an invalid or expired token.', 'warning')
        return redirect(url_for('users.reset_request'))
    form = ResetPasswordForm() 
    if form.validate():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user.password = hashed_password
        db.session.commit()
        flash('Your password has been updated! You can now log in.', 'success')
        return redirect(url_for('users.login'))
    return render_template('reset_token.html', title='Reset Password', form=form)


@users.route("/user/<int:user_id>/update_permissions", methods=['POST'])
@login_required
def update_permissions(user_id):
    if current_user.is_admin:
        user = User.query.get_or_404(user_id)
        
        user.can_add_post = bool(request.form.get(f"can_add_post_{user.id}"))
        user.can_update_post = bool(request.form.get(f"can_update_post_{user.id}"))
        user.can_delete_post = bool(request.form.get(f"can_delete_post_{user.id}"))
        
        db.session.commit()
        
        flash('User permissions updated!', 'success')
    
    return redirect(url_for('admin.admin_page'))


@users.route("/user/<int:user_id>/delete", methods=['POST'])  # Change the method to POST
@login_required
def delete_user(user_id):
    if current_user.is_admin:
        user = User.query.get_or_404(user_id)
        
        db.session.delete(user)
        db.session.commit()
        
        flash('The user has been deleted!', 'success')
    
    return redirect(url_for('admin.admin_page'))  # Redirect to the home page


@users.route('/toggle_subscription', methods=['POST'])
@login_required
def toggle_subscription():
    if request.method == 'POST':
        if 'subscribe' in request.form:
            current_user.is_subscribed = True
        elif 'unsubscribe' in request.form:
            current_user.is_subscribed = False

        db.session.commit()

    return redirect(url_for('users.account'))


@users.route('/unsubscribe', methods=['GET'])

def unsubscribe():
    user_id = request.args.get('user_id')
    # Fetch the user by user_id
    user = User.query.get(user_id)

    if user:
        # Set the user's send_notifications attribute to False to unsubscribe
        user.is_subscribed = False
        db.session.commit()
        flash('You have successfully unsubscribed from email notifications.', 'success')
    else:
        flash('Invalid user or user not found.', 'danger')

    return redirect(url_for('main.home'))  