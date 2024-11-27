from flask import Flask, request, jsonify, Response
import pandas as pd
import unicodedata
import json

app = Flask(__name__)

# Funkcja do usuwania polskich znaków i normalizacji tekstu
def normalize_text(text):
    if not isinstance(text, str):
        return text
    return ''.join(
        c for c in unicodedata.normalize('NFKD', text)
        if not unicodedata.combining(c)
    ).lower().strip()

# Wczytanie danych z pliku CSV
def load_data():
    try:
        data = pd.read_csv('product_details(1).csv')  # Nazwa pliku CSV
    except Exception as e:
        print(f"Błąd wczytywania pliku CSV: {e}")
        data = pd.DataFrame()
    return data

# Endpoint do wyszukiwania produktów
@app.route('/search', methods=['GET'])
def search_products():
    # Pobierz zapytanie z parametru `query`
    query = request.args.get('query', '').strip()
    if not query:
        return jsonify({'error': 'Brak parametru query'}), 400

    # Normalizujemy zapytanie
    normalized_query = normalize_text(query)

    # Wczytaj dane
    data = load_data()

    # Normalizujemy dane i dodajemy nową kolumnę do filtrowania
    data['Normalized Name'] = data['Product Name'].apply(normalize_text)

    # Dopasowane produkty
    exact_matches = data[data['Normalized Name'].str.contains(normalized_query, na=False)]

    # Podobne produkty (produkty zawierające część zapytania lub zbliżone nazwy)
    similar_matches = data[data['Normalized Name'].str.contains(normalized_query[:3], na=False)]  # Dopasowanie do pierwszych 3 znaków zapytania
    similar_matches = similar_matches[~similar_matches.index.isin(exact_matches.index)]  # Usuń produkty już zwrócone jako dopasowane

    # Jeśli brak wyników
    if exact_matches.empty and similar_matches.empty:
        return jsonify({'message': 'Nie znaleziono produktów'}), 404

    # Konwersja wyników do list słowników
    results = {
        "exact_matches": exact_matches.to_dict(orient='records'),
        "similar_matches": similar_matches.to_dict(orient='records')
    }

    # Zwracamy wyniki w sposób czytelny dla polskich znaków
    return Response(
        response=json.dumps(results, ensure_ascii=False, indent=4),
        content_type='application/json; charset=utf-8'
    )

if __name__ == '__main__':
    import os
    PORT = int(os.environ.get('PORT', 5000))  # Pobiera port z zmiennej środowiskowej lub ustawia domyślnie 5000
    app.run(host='0.0.0.0', port=PORT, debug=True)  # Uruchamia aplikację na publicznym adresie IP