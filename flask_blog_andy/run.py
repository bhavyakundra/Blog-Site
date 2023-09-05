from flask_bcrypt import Bcrypt
from flaskblog.models import User
from flaskblog import create_app, db

app = create_app()
bcrypt = Bcrypt()

with app.app_context():
    db.create_all()
    # Retrieve the admin user
    admin_user = User.query.filter_by(username='admin').first()

    if admin_user:
        # Update the password
        admin_user.password = bcrypt.generate_password_hash('new_password').decode('utf-8')
        db.session.commit()
        print("Admin password updated successfully")
    else:
        print("Admin user not found")

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5001, debug=True)