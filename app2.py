import string
import re
import aiml
import random
import mysql.connector
from flask import Flask, render_template, request, Markup
from Sastrawi.Stemmer.StemmerFactory import StemmerFactory
from spellchecker import correction

app = Flask(__name__)

kernel = aiml.Kernel()
kernel.bootstrap(learnFiles="std-startup.xml", commands="load aiml")

# MySQL database connection
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",  # Isi dengan password MySQL Anda
    database="knowledge_based"
)

cursor = db.cursor()

chat_log = []
# chat_log.append({"sender": "bot", "content": "Halo selamat datang, Ada yang bisa saya bantu kak?"})


@app.route("/")
def landing():
    return render_template("landing_page.html")


@app.route("/bot")
def page():
    return render_template("chatbot.html")


@app.route('/chat/mantap')
def hapus():
    chat_log.clear()
    return render_template("index.html", chat_log=chat_log)


@app.route("/chat")
def home():
    chat_log.append({"sender": "user", "content": "Halo Bot!"})
    chat_log.append(
        {"sender": "bot", "content": "Halo selamat datang, Ada yang bisa saya bantu kak?"})
    return render_template("index.html", chat_log=chat_log)


DEFAULT_RESPONSES = [
    "Pertanyaan yang anda inputkan tidak ada pada database kami, Apakah anda ingin dihubungkan ke CS kami?"
]

# membuat Stemming
factory = StemmerFactory()
stemmer = factory.create_stemmer()

# function PreProcessing


def preprocess(text):
    # mengubah inputan menjadi huruf kecil semua (case folding)
    text = text.lower()
    print("Hasil Inputan Menjadi Huruf Kecil: ", text)
    # menghilangkan nomor dan tanda baca
    text = re.sub(r"\d+", "", text)
    text = text.translate(str.maketrans("", "", string.punctuation))
    print("Hasil penghilangan nomor dan tanda baca: ", text)

    # melakukan tokenizing, Membagi kalimat menjadi perkata
    words = text.split()
    print("Hasil tokenizing: ", words)

    # melakukan spell check
    corrected_words = []
    for word in words:
        corrected_words.append(correction(word))
    print("Hasil Spell Check Typo : ", corrected_words)

    # melakukan Stemming, Merubah semua kata menjadi kata dasar
    stemmed_words = []
    for word in corrected_words:
        stemmed_words.append(stemmer.stem(word))
        print("Hasil Stemming : ", stemmed_words)

    # melakukan filtering stopwords, membuang kata yang tidak di perlukan
    with open("stopword.txt", "r") as file:
        stopwords = file.read().splitlines()
    filtered_words = [
        word for word in stemmed_words if word not in stopwords]
    print("Hasil filtering stopwords: ", filtered_words)

    # menggabungkan kata sudah melalui tahapan PreProcessing
    preprocessed_text = " ".join(filtered_words)

    print("Pattern :", preprocessed_text)
    return preprocessed_text


@app.route("/", methods=["GET", "POST"])
def chat():
    if request.method == "POST":
        user_input = request.form.get("user_input")
        preprocessed_text = preprocess(user_input)

        # Check if the question exists in the database
        cursor.execute(
            "SELECT response FROM aiml WHERE question = %s", (preprocessed_text,))
        result = cursor.fetchone()

        if result:
            response = result[0]
        else:
            response = kernel.respond(preprocessed_text)

        if response:
            response = Markup(response)
            chat_log.append({"sender": "user", "content": user_input})
            chat_log.append({"sender": "bot", "content": response})
        else:
            response = random.choice(DEFAULT_RESPONSES)
            chat_log.append({"sender": "user", "content": user_input})
            chat_log.append({"sender": "bot", "content": response})

    return render_template("index.html", chat_log=chat_log)


if __name__ == "__main__":
    app.run(debug=True)
