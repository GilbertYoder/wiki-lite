  # Readme
  
  ## Wiki-Lite
  Wiki-lite is a light, file based wiki built with python on the Quart framework.
  
  Wiki-lite is completely file based, and uses git for wiki versioning.
  
  To use it, clone the repository, create two folders in the wiki-lite directory:
  "content" & "config"
  
  inside content create a subfolder to contain your wiki. If you have an existing markdown wiki, you can move it into this directory.
  Each wiki you have and want to host you can house in it's own parent folder here (under "content") and they will be separated on the frontend.
  
  Inside the config directory, create 2 files, "users.json" and "wiki_setup.json".
  
  Inside "users.json" you can setup your users:
  ```
      "bob": {
        "id": "bob",
        "password": "bob",
        "default_redirect_slug": "defaultWiki",
        "email": "bob@bob.bob"
    }
  ```
  
  the "default_redirect_slug" will be the default wiki this user will be redirected to, and will match a wiki folder under the contents directory.
  
  Inside "wiki_setup.json", setup your wiki preferences:
  ```
  {
    "name": "Developer Wiki",
    "bookmarks": [
        ["Important Page", "/wiki/defaultWiki/myPage"]
      ]
  }
  ```
  
  In this file you name your site, as well as setup any page bookmarks. The bookmarks will point to the page URL.
  
  Once setup, run ```docker compose build``` then ```docker compose up``` to run it. You can access your wiki at port 5000
  
