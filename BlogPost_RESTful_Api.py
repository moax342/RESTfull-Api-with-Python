from flask import Flask, render_template, redirect, url_for,flash
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from flask_ckeditor import CKEditor
from datetime import date
from forms import CreatePostForm,RegisterForm,LoginForm,CommentForm
from functools import wraps
from flask import abort

app = Flask(__name__)
app.config['SECRET_KEY'] = 'any-secert-key-you-want'
ckeditor = CKEditor(app)
Bootstrap(app)

# CONNECT TO DB
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///blog.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

login_manager=LoginManager()
login_manager.init_app(app)

#creating the login manger in order to login work
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# creating a wraper function
def admin_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # If id is not 1 then return abort with 403 error
        if current_user.id != 1:
            return abort(403)
        # Otherwise continue with the route function
        return f(*args, **kwargs)
    return decorated_function


# CONFIGURE TABLE
class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    name = db.Column(db.String(100))
    posts = relationship("BlogPost", back_populates="author")
    comments = relationship("Comment", back_populates="comment_author")


class BlogPost(db.Model):
    __tablename__ = "blog_posts"
    id = db.Column(db.Integer, primary_key=True)
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    author = relationship("User", back_populates="posts")
    title = db.Column(db.String(250), unique=True, nullable=False)
    subtitle = db.Column(db.String(250), nullable=False)
    date = db.Column(db.String(250), nullable=False)
    body = db.Column(db.Text, nullable=False)
    img_url = db.Column(db.String(250), nullable=False)

    # -----------Parent Relationship-----------#
    comments = relationship("Comment", back_populates="parent_post")


class Comment(db.Model):
    __tablename__ = "comments"
    id = db.Column(db.Integer, primary_key=True)
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    comment_author = relationship("User", back_populates="comments")

    # ------------Child Relationship ------------#
    post_id = db.Column(db.Integer, db.ForeignKey("blog_posts.id"))
    parent_post = relationship("BlogPost", back_populates="comments")
    text = db.Column(db.Text, nullable=False)

# with app.app_context():
#     db.create_all()


# all routes are below
@app.route('/')
def get_all_posts():
    posts = BlogPost.query.all()
    return render_template("index.html", all_posts=posts,current_user=current_user)


@app.route("/post/<int:post_id>",methods=["GET", "POST"])
def show_post(post_id):
    form=CommentForm()
    requested_post=BlogPost.query.filter_by(id=post_id).first()
    # the user can comment only if he is logged in 
    if form.validate_on_submit():
        if not current_user.is_authenticated:
            flash("You need to login or register to comment.")
            return redirect(url_for("login"))
    # take the comment from the form into the database
        new_comment = Comment(
            text=form.comment_text.data,
            comment_author=current_user,
            parent_post=requested_post
        )
        db.session.add(new_comment)
        db.session.commit()
    # getting all the commenst to show in the related post
    comments = Comment.query.all()
    return render_template("post.html",form=form, post=requested_post,
                           current_user=current_user,comments=comments)


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/contact")
def contact():
    return render_template("contact.html")


@app.route('/create_post',methods=["GET", "POST"])
@admin_only
def create_post():
    form=CreatePostForm()
    # getting the post data from the admin
    if form.validate_on_submit():
        new_post = BlogPost(
            title=form.title.data,
            subtitle=form.subtitle.data,
            body=form.body.data,
            auther_id=current_user,
            img_url=form.img_url.data,
            date=date.today().strftime("%B %d, %Y")
        )
        db.session.add(new_post)
        db.session.commit()
        return redirect(url_for("get_all_posts"))
    return render_template('make-post.html',form=form,current_user=current_user)


@app.route("/edit/<post_id>",methods=['GET','POST'])
@admin_only
def edit_post(post_id):
    post = BlogPost.query.get(post_id)
    # load the form with the post-data to edit it
    edit_form = CreatePostForm(
        title=post.title,
        subtitle=post.subtitle,
        img_url=post.img_url,
        author=post.author,
        body=post.body
    )
# updating the data by the new data
    if edit_form.validate_on_submit():
        post.title = edit_form.title.data
        post.subtitle = edit_form.subtitle.data
        post.img_url = edit_form.img_url.data
        post.author = current_user.name
        post.body = edit_form.body.data
        db.session.commit()
        return redirect(url_for("show_post", post_id=post.id))
    return render_template("make-post.html", form=edit_form, is_edit=True,current_user=current_user)

# deleteing a post is admin only
@app.route('/delete/<post_id>')
@admin_only
def delete_post(post_id):
    requested_post = BlogPost.query.filter_by(id=post_id).first()
    db.session.delete(requested_post)
    db.session.commit()
    return redirect(url_for("get_all_posts",current_user=current_user))

@app.route('/login',methods=['GET','POST'])
def login():
    form=LoginForm()
    if form.validate_on_submit():
        email=form.email.data
        password=form.password.data

        # checking if the user is in the database
        user = User.query.filter_by(email=email).first()

        # Email doesn't exist
        if not user:
            flash("That email does not exist, please try again.")
            return redirect(url_for('register'))

        # Password incorrect
        elif not check_password_hash(user.password, password):
            flash('Password incorrect, please try again.')
            return redirect(url_for('login'))
            # Email exists and password correct
        else:
            login_user(user)
            return redirect(url_for('get_all_posts'))

    return render_template('login.html',form=form)

@app.route('/register',methods=['GET','POST'])
def register():
    form =RegisterForm()
    # when submitting
    if form.validate_on_submit():
        if User.query.filter_by(email=form.email.data).first():
            # Shows user already exists
            flash("You've already signed up with that email, log in instead!")
            return redirect(url_for('login'))
        else:
            new_user=User(
                name=form.name.data,
                email=form.email.data,
                password=generate_password_hash(form.password.data,"pbkdf2:sha256",8)
            )
            db.session.add(new_user)
            db.session.commit()

            # Log in and authenticate the user after adding details to database.
            login_user(new_user)
            return redirect(url_for('get_all_posts'))

    return render_template('register.html',form=form)

# logging out
@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('get_all_posts',current_user=False))


if __name__ == "__main__":
    app.run()
