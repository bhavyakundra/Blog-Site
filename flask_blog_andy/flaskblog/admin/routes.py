from flaskblog import db
from functools import wraps
from .forms import UserPermissionsForm
from flaskblog.models import User, Post
from flask_login import login_required, current_user
from flask import Blueprint,request, render_template, redirect, url_for, flash, abort
 
admin = Blueprint('admin', __name__)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.is_authenticated and current_user.is_admin:
            return f(*args, **kwargs)
        else:
            abort(403)  # Access denied
    return decorated_function


@admin.route("/admin_page", methods=['GET', 'POST'])
@admin_required
def admin_page():
    users = User.query.all()
    form = UserPermissionsForm()  # No need to pass user_ids anymore

    if request.method == 'POST':
        for user in users:
            user.can_add_post = bool(request.form.get(f'can_add_post_{user.id}'))
            user.can_update_post = bool(request.form.get(f'can_update_post_{user.id}'))
            user.can_delete_post = bool(request.form.get(f'can_delete_post_{user.id}'))
        
        db.session.commit()
        flash('User permissions updated!', 'success')
        return redirect(url_for('admin.admin_page'))

    posts = Post.query.all()
    return render_template('admin_page.html', users=users, posts=posts, form=form)


@admin.route("/user/<int:user_id>/permissions", methods=['GET', 'POST'])
@login_required
@admin_required
def user_permissions(user_id):
    user = User.query.get_or_404(user_id)
    form = UserPermissionsForm()

    if request.method == 'POST':
        user.can_add_post = bool(request.form.get('can_add_post'))
        user.can_update_post = bool(request.form.get('can_update_post'))
        user.can_delete_post = bool(request.form.get('can_delete_post'))
        
        db.session.commit()
        flash('User permissions updated!', 'success')
        return redirect(url_for('admin.admin_page'))

    return render_template('user_permissions.html', title='Manage User Permissions', form=form, user=user)