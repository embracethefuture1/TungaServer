from flask import Flask, request, render_template

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def home():
    result = None
    if request.method == 'POST':
        sayi1 = int(request.form['sayi1'])
        sayi2 = int(request.form['sayi2'])
        result = sayi1 + sayi2
    return render_template('index.html', result=result)

if __name__ == '__main__':
    app.run()
