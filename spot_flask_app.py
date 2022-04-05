import os
from application import app

if __name__ == '__main__':
    app.run(threaded=True, debug=True, port= int(os.environ.get("PORT", os.environ.get("SPOTIPY_REDIRECT_URI", 8080).split(":")[-1])))
