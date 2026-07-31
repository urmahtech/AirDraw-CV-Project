from flask import Flask, render_template
import subprocess
import sys

app = Flask(__name__)


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/start")
def start():
    subprocess.Popen([sys.executable, "-m", "src.main"])

    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>AirDraw</title>
        <style>
            body{
                background:#111;
                color:white;
                text-align:center;
                font-family:Arial;
                margin-top:100px;
            }

            h1{
                color:#00ff99;
            }

            a{
                color:#00ff99;
                font-size:20px;
                text-decoration:none;
            }

            a:hover{
                text-decoration:underline;
            }
        </style>
    </head>

    <body>

        <h1>AirDraw is starting...</h1>

        <p>If the webcam window does not open within a few seconds,
        check the VS Code terminal for any errors.</p>

        <br>

        <a href="/">← Back to Home</a>

    </body>
    </html>
    """


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)