from flask import render_template, request, Blueprint
from flaskblog.models import Post
from flask import render_template,request
from flaskblog.posts.forms import PostForm
from flask_login import current_user, login_required
import yfinance as yf
main = Blueprint('main', __name__)


@main.route("/")
@main.route("/home")
@login_required
def home():
    page = request.args.get('page', 1, type=int)
    posts = Post.query.order_by(Post.date_posted.desc()).paginate(page=page, per_page=5)
    return render_template('home.html', posts=posts)


@main.route("/about")
@login_required
def about():
    return render_template('about.html', title='About')

@main.route("/amzn")
def amzn():
    return render_template('amzn.html', title='Table')


@main.route("/mary")
def mary():
    return render_template('mary.html', title='mary')

@main.route("/models")
def models():
    price = yf.Ticker("HSAI")
    current_ticker = price.info['currentPrice']
    return render_template('models.html', HSAI_price=current_ticker)