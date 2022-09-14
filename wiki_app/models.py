
from gc import is_finalized
from genericpath import isfile
from importlib.resources import path
from pathlib import Path
from unicodedata import name
from markdown import markdown
from quart import jsonify, redirect, Response, render_template
from flask_login import current_user

import os
import json
import git

class FileManager:
    def __init__(self, base_dir) -> None:
        self.base_dir = base_dir
        pass

    def search_string(self, string):
        paths = []
        for folder, dirs, files in os.walk(self.base_dir):
            if '.git' in folder.split("/"): continue
            for file in files:
                fullpath = os.path.join(folder, file)
                file_matches = {"filename": file, "path": "/wiki/" + "/".join(fullpath.split("/")[1:]), "matches": []}
                with open(fullpath, 'r') as f:
                    for line in f:
                        if string in line:
                            i = line.index(string)
                            match = line[0:i] + "<match>" + line[i: i + len(string)] + "</match>" + line[i + len(string):]
                            file_matches['matches'].append(match)
                if len(file_matches['matches']) > 0: paths.append(file_matches)
                
        return paths

# Router -- for managing all things Paths
class Router:

    @staticmethod
    def interpret_path(path, args=None):
        # Search in the intended path, prioritize pages over folders
        # If page exists, open that, if not... look for a folder, if not, revert to page that doesn't exist
        path = Router.web_to_local(path)
        
        if (Router.is_file(Router.ensure_extension(path))):
            if not Router.has_extension(path): return redirect(Router.local_to_web(Router.ensure_extension(path)))
            if args and 'commit_sha' in args:
                return Page().load_file_version(path, args['commit_sha'])
            return Page().load_from_path(path)

        elif (Router.is_dir(Router.ensure_no_extension(path))):
            return redirect(Router.local_to_web(path, is_folder=True) + "home.md")

        else:
            if not Router.has_extension(path):
                return redirect(Router.local_to_web(Router.ensure_extension(path)))
            return Page().load_fake_file(path)

    @staticmethod
    def web_to_local(path):
        return "content" + Router.clean_path(path)
    
    @staticmethod
    def local_to_web(path, is_folder=False):
        # assumes local path will begin with "contents"
        if path[-1] == "/":
            is_folder = True
            path = path[:-1]
            path = "/".join(path.split("/")[1:])
            path = Router.clean_path(path)
        path = "/wiki/" + "/".join(path.split("/")[1:])
        if is_folder: path = path + "/"
        return path

    @staticmethod
    def is_path(path):
        return os.path.exists(path)
    
    @staticmethod
    def is_file(path):
        return os.path.isfile(path)
    
    @staticmethod
    def is_dir(path):
        return os.path.isdir(path)

    @staticmethod
    def ensure_extension(name):
        if not Router.has_extension(name): name = name + ".md"
        return name

    @staticmethod
    def ensure_no_extension(name):
        while Router.has_extension(name):
            name = name[:-3]
        return name
    
    @staticmethod
    def has_extension(name):
        return (name.split(".")[-1] == "md")

    @staticmethod
    def get_parent_dir(fullpath):
        return "/".join(fullpath.split("/")[:-1]) + "/"
    
    @staticmethod
    def get_pagename(fullpath):
        return fullpath.split("/")[-1]
    
    @staticmethod
    def concat_paths(path, name):
        if path[-1] != '/': path += '/'
        if name[0] == '/': name = name[1:]
        return path + name
    
    @staticmethod
    def clean_path(path):
        is_folder = False
        if path[-1] == "/":
            is_folder = True
            path = path[:-1]

        # Remove excess slashes etc from path -- will return with leading forward slash unless top level
        arr = path.split("/")
        new_path = []
        for p in arr:
            while p[0] == "/": p = p[1:]
            while p[-1] == "/": p = p[:-1]
            new_path.append(p)
        if new_path[0] != "content": new_path[0] = "/" + new_path[0]
        if is_folder: new_path[-1] = new_path[-1] + "/"
        return "/".join(new_path)


class Page:
    def __init__(self) -> None:
        self.fullpath = None
        self.path = None
        self.webpath = None
        self.relativepath = None
        self.name = None
        self.source = None
        self.html = None
        self.commit_history = None
        pass

    def load_from_path(self, fullpath):
        self.fullpath = Router.ensure_extension(fullpath)
        self.path = Router.get_parent_dir(fullpath)
        self.webpath = Router.local_to_web(self.fullpath)
        self.relativepath = "/".join(self.fullpath.split("/")[1:])
        self.name = fullpath.split("/")[-1][:-3]
        self.commit_history = gitManager.get_history(fullpath)

        if not Router.is_file(self.fullpath):
            self._exists = False
            return False

        self._exists = True
        with open(fullpath) as file:
            self.source = file.read()
        self.html = markdown(self.source, extensions=['fenced_code', 'tables'])
        return self
    
    def load_fake_file(self, fullpath):
        self.fullpath = fullpath
        self.path = Router.get_parent_dir(fullpath)
        self.webpath = Router.local_to_web(self.fullpath)
        self.relativepath = "/".join(self.fullpath.split("/")[1:])
        self.name = fullpath.split("/")[-1][:-3]
        self._exists = False

        self.source = "**This page isn't created yet.**\n\n Enter ```np:" + Router.ensure_no_extension(Router.get_pagename(fullpath)) + "``` in the command palette to create it."
        self.html = markdown(self.source, extensions=['fenced_code', 'tables'])
        return self

    def load_file_version(self, fullpath, commit_sha):
        self.fullpath = fullpath
        self.path = Router.get_parent_dir(fullpath)
        self.webpath = Router.local_to_web(self.fullpath)
        self.relativepath = "/".join(self.fullpath.split("/")[1:])
        self.name = fullpath.split("/")[-1][:-3]
        self._exists = False

        self.source = gitManager.get_file_at_commit(commit_sha, fullpath)
        self.html = markdown(self.source, extensions=['fenced_code', 'tables'])
        return self

    def update_page(self, data):
        contents = data['data']
        with open(Router.ensure_extension(self.fullpath), "w") as file:
            file.write(contents)
        self.html = markdown(contents, extensions=['fenced_code', 'tables'])
        gitManager.handle_possible_change(self.fullpath, data['commit_message'])

    @staticmethod
    def delete_page(fullpath):
        os.remove(fullpath)
        gitManager.handle_possible_change(fullpath, "Deleted page: " + Router.get_pagename(fullpath))
        return True

    def is_toplevel(self):
        return (len(self.fullpath.split("/")) < 4)

    def get_slug_list(self):
        slug_list = []
        i = "/wiki"
        for p in self.webpath[1:].split("/")[1:]:
            i = i + "/" + p
            slug_list.append([p, i])
        return slug_list

    @property
    def exists(self):
        return self._exists

    def get_dir_pages(self):
        if not os.path.isdir(self.path): return Response(status=404)
        pages = [dirname for dirname in os.listdir(self.path) if os.path.isfile(self.path + "/" + dirname)]
        return pages
        
    def get_dir_folders(self):
        if not os.path.isdir(self.path): return Response(status=404)
        folders = [os.path.splitext(filename)[0] for filename in os.listdir(self.path) if not os.path.isfile(self.path + "/" + filename)]
        return folders
    
    @staticmethod
    def create_page(path):
        if Router.is_file(path): return False
        with open(path, "w") as f:
            f.write(path)
        gitManager.handle_possible_change(path, "Added page: " + Router.get_pagename(path))
        return True

class SettingsController:

    def __init__(self) -> None:
        self.config_location = "config/wiki_setup.json"
        self.user_settings_location = "config/users.json"
        pass

    def get_settings(self):
        with open(self.config_location) as f:
            settings = f.read()
        return json.loads(settings)
    
    def get_user_settings(self):
        with open(self.user_settings_location) as f:
            settings = f.read()
        return json.loads(settings)


class GitManager:

    def __init__(self, repo_path) -> None:
        self.repo_path = repo_path
        self.repo = self.get_repo()

    def handle_possible_change(self, fullpath, commit_message):
        path = self.get_gitpath_from_fullpath(fullpath)
        author = git.Actor(current_user.config['id'], current_user.config['email'])

        if self.file_changed(path.split("/")[-1]):
            self.stage_file(path)
            self.commit_change(commit_message, author)
    
    def get_author():
        author = git.Actor(current_user.config['id'], current_user.config['email'])

    def get_repo(self):
        if not self.is_git_repo():
            return git.Repo.init(self.repo_path)
        else:
            return git.Repo(self.repo_path)

    def is_git_repo(self):
        try:
            _ = git.Repo(self.repo_path).git_dir
            return True
        except git.exc.InvalidGitRepositoryError:
            return False
    
    def stage_file(self, relativepath):
        self.repo.git.add(relativepath) #path should not include 'content/'
    
    def file_changed(self, filename):
        git_status = self.repo.git.status()
        if filename in git_status:
            return True
        return False
    
    def commit_change(self, message, author):
        self.repo.index.commit(message, author=author)

    def get_gitpath_from_fullpath(self, fullpath):
        return "/".join(fullpath.split("/")[1:])
    
    def get_history(self, fullpath):
        path = self.get_gitpath_from_fullpath(fullpath)
        history = list(self.repo.iter_commits(paths=path))
        return history
    
    def get_commit_by_hexsha(self, fullpath, hexsha):
        commits = self.get_history(fullpath)
        for com in commits:
            if com.hexsha == hexsha: return com
        return None

    def get_file_at_commit(self, hexsha, fullpath):
        commit = self.get_commit_by_hexsha(fullpath, hexsha)
        path = self.get_gitpath_from_fullpath(fullpath)
        return self.repo.git.execute(["git", "show", f"{commit.hexsha}:{path}"])

class User():
    def __init__(self) -> None:
        self.user_config = SettingsController().get_user_settings()
        pass

    def get_user(self, id):
        if id in self.user_config:
            self.config = self.user_config[id]
            return self
        return None

    def is_active(self):
        return True

    def get_id(self):
        return self.config['id']

    def is_authenticated(self):
        return True

    def is_anonymous(self):
        return False


gitManager = GitManager('content/')