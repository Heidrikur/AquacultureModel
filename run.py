from flask import Flask

app = Flask(__name__)

@app.route('/')
#def home():
#    # "<h1> Hello World </h1>"
#    return "<h1> This is my new web application </h1>"

def test():
    return "<h1> Hello World </h1>"
if __name__ =="__main__":
    app.run(debug=True,port=8080)