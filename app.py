from flask import Flask, request, jsonify
import os
from flask_cors import CORS
from dotenv import load_dotenv
from facebook.parse_page import ParsePage
from postgres_db.core import PostgreSQL

load_dotenv(override=True)

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}}) 

SAVE_PATH = os.getenv("STATIC_DIR")

@app.route('/save_html', methods=['POST'])
def save_html():
    try:
        html_content = request.form.get('html')
        if html_content:
            ParsePage().run(html_content)
            # file_path = os.path.join(SAVE_PATH, request.form.get('file'))
            # with open(file_path, 'w', encoding='utf-8') as file:
            #     file.write(html_content)
            return 'HTML saved successfully', 200
    except Exception as ex:
        print(ex)
    return 'No HTML provided', 400


@app.route('/get_url', methods=['GET'])
def get_url():
    try:
        sql = """WITH random_row AS (
                    SELECT id
                    FROM ghana_links
                    WHERE status = 0
                    ORDER BY RANDOM()
                    LIMIT 1
                 )
                 UPDATE ghana_links
                 SET status = 1
                 WHERE id = (SELECT id FROM random_row)
                 RETURNING profile_url;"""
        db = PostgreSQL()
        cursor = db.connection.cursor()
        cursor.execute(sql)
        url = cursor.fetchone()  # Получаем одну запись
        db.connection.commit()
        cursor.close()
        if url:
            return jsonify({'url': url[0]})  # Возвращаем только строку
        else:
            return jsonify({'url': None})  # Если записи не найдено
    except Exception as ex:
        print(f"Error: {ex}")
        return 'Something wrong', 400
    finally:
        db.close_connection()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)