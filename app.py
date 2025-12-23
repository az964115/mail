from flask import Flask, request, jsonify, render_template
import quarantine

app = Flask(__name__)

@app.before_first_request
def init():
    if not quarantine.login():
        raise RuntimeError("Login mail server failed")


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/search")
def search():
    subject = request.args.get("subject", "")
    result = quarantine.search_quarantine(subject)
    return jsonify(result)


@app.route("/api/release", methods=["POST"])
def release():
    mail_id = request.json.get("mail_id")
    quarantine.release_mail(mail_id)
    return jsonify({"success": True})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
