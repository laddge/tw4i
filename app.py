import os
from urllib.parse import urlparse
import tweepy
from flask import Flask, session, redirect, url_for, render_template, request

CK = os.getenv("TW_CK")
CS = os.getenv("TW_CS")
CALLBACK = os.getenv("CALLBACK")

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")


@app.route("/", methods=["GET", "POST"])
def index():
    auth = tweepy.OAuthHandler(CK, CS, CALLBACK)
    access_token = session.get("access_token")
    access_token_secret = session.get("access_token_secret")
    if access_token and access_token_secret:
        auth.set_access_token(access_token, access_token_secret)
        api = tweepy.API(auth)
        user = api.verify_credentials()
        posted = False
        tweet_url = ""
        if request.method == "POST":
            posted = True
            try:
                reply_url = request.form.get("reply_url")
                text = request.form.get("text")
                in_reply_to_status_id = None
                if reply_url:
                    text = f"@{urlparse(reply_url).path.split('/')[1]} {text}"
                    in_reply_to_status_id = urlparse(reply_url).path.split("/")[3]
                media_ids = []
                for i in range(4):
                    f = request.files.get(f"media{i}")
                    if not f:
                        continue
                    res = api.media_upload(filename=f.filename, file=f)
                    media_ids.append(res.media_id)
                tweet = api.update_status(
                    status=text,
                    media_ids=media_ids,
                    in_reply_to_status_id=in_reply_to_status_id,
                )
                tweet_url = (
                    f"https://twitter.com/{tweet.user.screen_name}/status/{tweet.id}"
                )
            except Exception as e:
                print(e)
        return render_template(
            "index.html", posted=posted, user=user, tweet_url=tweet_url
        )
    session.pop("access_token", None)
    session.pop("access_token_secret", None)
    return render_template("index.html")


@app.route("/auth")
def auth():
    try:
        auth_url = auth.get_authorization_url()
        session.permanent = True
        session["request_token"] = auth.request_token.get("oauth_token")
    except Exception as e:
        print(e)
        return redirect(url_for("index"))
    return redirect(auth_url)


@app.route("/callback")
def callback():
    auth = tweepy.OAuthHandler(CK, CS, CALLBACK)
    token = session.pop("request_token", None)
    verifier = request.args.get("oauth_verifier")
    auth.request_token = {"oauth_token": token, "oauth_token_secret": verifier}
    try:
        auth.get_access_token(verifier)
        session.permanent = True
        session["access_token"] = auth.access_token
        session["access_token_secret"] = auth.access_token_secret
    except Exception as e:
        print(e)
        return "何かがおかしい"
    return redirect(url_for("index"))


@app.route("/logout")
def logout():
    session.pop("request_token", None)
    session.pop("access_token", None)
    session.pop("access_token_secret", None)
    return redirect(url_for("index"))
