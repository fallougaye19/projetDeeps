import os
import numpy as np
import cv2
from flask import Flask, render_template, request, jsonify, url_for
from werkzeug.utils import secure_filename
from tensorflow.keras.models import load_model
from tensorflow.keras.utils import load_img, img_to_array
import base64
from io import BytesIO
from PIL import Image

# Configuration de l'application Flask
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg'}

# Créer le dossier uploads s'il n'existe pas
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Charger le modèle au démarrage
MODEL_PATH = 'models/best_overall_model.h5'
try:
    model = load_model(MODEL_PATH)
    print(f"✓ Modèle chargé depuis: {MODEL_PATH}")
except Exception as e:
    print(f"⚠ Erreur lors du chargement du modèle: {e}")
    model = None

# Configuration
IMG_SIZE = (128, 128)
CATEGORIES = ['Parasitized', 'Uninfected']
CLASS_INFO = {
    'Parasitized': {
        'description': 'Cellule infectée par le parasite du paludisme',
        'recommendation': 'Consultation médicale recommandée immédiatement',
        'color': '#dc3545'
    },
    'Uninfected': {
        'description': 'Cellule saine, non infectée',
        'recommendation': 'Aucune action nécessaire',
        'color': '#28a745'
    }
}

def allowed_file(filename):
    """Vérifie si le fichier a une extension autorisée"""
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def preprocess_image(image_path, target_size=IMG_SIZE):
    """
    Prétraite l'image pour la prédiction
    """
    try:
        # Méthode 1: Avec Keras
        img = load_img(image_path, target_size=target_size)
        img_array = img_to_array(img)
        img_array = img_array / 255.0  # Normalisation
        img_array = np.expand_dims(img_array, axis=0)  # Ajouter dimension batch

        return img_array
    except Exception as e:
        print(f"Erreur preprocessing: {e}")
        return None

def predict_image(image_path):
    """
    Effectue la prédiction sur l'image
    """
    if model is None:
        return None, "Modèle non chargé"

    try:
        # Prétraitement
        img_array = preprocess_image(image_path)
        if img_array is None:
            return None, "Erreur lors du prétraitement"

        # Prédiction
        predictions = model.predict(img_array, verbose=0)

        # Extraire les résultats
        predicted_class_idx = np.argmax(predictions[0])
        confidence = float(predictions[0][predicted_class_idx])
        predicted_class = CATEGORIES[predicted_class_idx]

        # Préparer les résultats détaillés
        results = {
            'predicted_class': predicted_class,
            'confidence': confidence,
            'confidence_percentage': f"{confidence * 100:.2f}%",
            'all_probabilities': {
                CATEGORIES[i]: float(predictions[0][i])
                for i in range(len(CATEGORIES))
            },
            'class_info': CLASS_INFO[predicted_class]
        }

        return results, None

    except Exception as e:
        return None, f"Erreur lors de la prédiction: {str(e)}"

def image_to_base64(image_path):
    """Convertit une image en base64 pour l'affichage"""
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode('utf-8')
    except:
        return None

@app.route('/')
def index():
    """Page d'accueil"""
    return render_template('index.html')

@app.route('/predict', methods=['POST'])
def predict():
    """Route pour la prédiction"""

    # Vérifier si un fichier a été envoyé
    if 'file' not in request.files:
        return jsonify({'error': 'Aucun fichier trouvé'}), 400

    file = request.files['file']

    # Vérifier si un fichier a été sélectionné
    if file.filename == '':
        return jsonify({'error': 'Aucun fichier sélectionné'}), 400

    # Vérifier l'extension du fichier
    if not allowed_file(file.filename):
        return jsonify({'error': 'Format de fichier non autorisé. Utilisez PNG, JPG ou JPEG'}), 400

    try:
        # Sauvegarder le fichier
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        # Faire la prédiction
        results, error = predict_image(filepath)

        if error:
            os.remove(filepath)
            return jsonify({'error': error}), 500

        # Convertir l'image en base64
        img_base64 = image_to_base64(filepath)

        # Nettoyer: supprimer le fichier uploadé
        os.remove(filepath)

        # Ajouter l'image aux résultats
        results['image'] = img_base64

        return jsonify(results), 200

    except Exception as e:
        return jsonify({'error': f'Erreur serveur: {str(e)}'}), 500

@app.route('/about')
def about():
    """Page à propos"""
    return render_template('about.html')

@app.route('/health')
def health():
    """Health check endpoint"""
    status = {
        'status': 'healthy',
        'model_loaded': model is not None,
        'model_path': MODEL_PATH
    }
    return jsonify(status), 200

# Gestionnaire d'erreurs
@app.errorhandler(413)
def request_entity_too_large(error):
    return jsonify({'error': 'Fichier trop volumineux. Maximum 16MB'}), 413

@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Erreur interne du serveur'}), 500

if __name__ == '__main__':
    print("\n" + "="*70)
    print("🚀 DÉMARRAGE DE L'APPLICATION MALARIA DETECTION")
    print("="*70)
    print(f"Modèle: {MODEL_PATH}")
    print(f"Status: {'✓ Chargé' if model else '✗ Non chargé'}")
    print(f"Dossier uploads: {app.config['UPLOAD_FOLDER']}")
    print(f"Formats acceptés: {', '.join(app.config['ALLOWED_EXTENSIONS'])}")
    print("="*70 + "\n")

    # Lancer l'application
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=False, host='0.0.0.0', port=port
