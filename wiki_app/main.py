
import hypercorn
from hypercorn.asyncio import serve
from hypercorn.config import Config
import asyncio

from quart import Quart, flask_patch, render_template, request, Response, url_for, redirect
from models import FileManager, SettingsController, User, Router, Page
from flask_login import LoginManager, login_required, login_user, current_user, logout_user
import os
import json

app = Quart(__name__)
app.config['SECRET_KEY'] = 'secret'

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User().get_user(user_id)

file_manager = FileManager("content")
settings_controller = SettingsController()
settings = settings_controller.get_settings()
site_name = settings['name']
bookmarks = settings['bookmarks']

@app.route("/")
@login_required
async def home():
    return redirect("/wiki/" + current_user.config['default_redirect_slug'])

@app.route("/wiki/")
@login_required
async def wiki():
    return redirect("/wiki/" + current_user.config['default_redirect_slug'])

@app.route('/login', methods=['GET', 'POST'])
async def login():
    error = None

    if request.method == 'POST':
        form_username = (await request.form)['username']
        form_pass = (await request.form)['password']
        user = User().get_user(form_username)
        if user:
            if (user.config['password'] == form_pass):
                login_user(user, remember=True)
                return redirect("/wiki/" + user.config['default_redirect_slug'])
            else:
                error = "The provided credentials are incorrect. Please try again"
    return await render_template('login.html', error=error, site_name=site_name)

@app.route("/logout", methods=["GET"])
@login_required
def logout():
    """Logout the current user."""
    user = current_user
    user.authenticated = False
    logout_user()
    return redirect("/login")

@app.route("/wiki/<path:page>")
@login_required
async def layout(page):
    # args = request.args
    page = Router.interpret_path(page)
    if type(page) == Response: return page
    hide_nav_up = page.is_toplevel()
    slug_list = page.get_slug_list()
    sidebar_filelist = page.get_dir_pages()
    sidebar_folderlist = page.get_dir_folders()
    page_exists = page.exists

    history_list = []
    if page.commit_history and len(page.commit_history) > 0:
        for commit in page.commit_history:
            history_list.append([commit.message, commit.author.name, commit.committed_datetime.strftime("%m/%d/%Y"), commit.hexsha])
        history_list[0][3] = ""

    return await render_template("page.html",
    html=page.html, 
    slug_list=slug_list,
    relativepath=page.relativepath,
    sidebar_files=sidebar_filelist,
    sidebar_folders=sidebar_folderlist,
    hide_nav_up=hide_nav_up,
    site_name=site_name,
    bookmarks=bookmarks,
    page_exists=page_exists,
    history=history_list,
    pagename=page.name)

@app.route("/save_page/<path:relativepath>", methods=['POST'])
@login_required
async def save_page(relativepath):
    data = (json.loads(await request.data))
    page = Router.interpret_path(relativepath)
    page.update_page(data)
    return page.html

@app.route("/wiki_page/html/<path:fullpath>")
@login_required
async def load_template(fullpath):
    args = request.args
    return Router.interpret_path(fullpath, args).html

@app.route("/wiki_page/markdown/<path:fullpath>")
@login_required
async def get_template(fullpath):
    args = request.args
    return Router.interpret_path(fullpath, args).source

@app.route("/wiki_page/create_page/<path:relativepath>")
@login_required
async def create_page(relativepath):
    Page().create_page(Router.web_to_local(relativepath))
    return "ok"

@app.route("/wiki_page/create_folder/<path:relativepath>")
@login_required
async def create_folder(relativepath):
    fullpath = Router.web_to_local(relativepath)
    if not os.path.isdir(fullpath):
        os.mkdir(fullpath)
        return "ok"
    return "Folder already exists"

@app.route("/wiki_page/delete_page/<path:relativepath>")
@login_required
async def delete_page(relativepath):
    Page().delete_page(Router.web_to_local(relativepath))
    return "ok"

@app.route("/wiki_page/search")
@login_required
async def search():
    args = request.args
    term = args['text']

    matches = file_manager.search_string(term)
    matches = {"term": term, "matches": matches}

    return await render_template("search_results.html", site_name=site_name, matches=matches, bookmarks=bookmarks)

# app.run()

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    config = Config()
    config.bind = ["0.0.0.0:5000"]
    loop.run_until_complete(serve(app, config))