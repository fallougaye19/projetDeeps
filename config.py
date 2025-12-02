import os
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

class Config:
    """Configuration de l'application"""
    # Flask
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key')
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')
    DEBUG = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    
    # Upload
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', 'uploads')
    MAX_CONTENT_LENGTH = int(os.getenv('MAX_CONTENT_LENGTH', 16777216))  # 16MB
    ALLOWED_EXTENSIONS = set(os.getenv('ALLOWED_EXTENSIONS', 'png,jpg,jpeg').split(','))
    
    # Model
    MODEL_PATH = os.getenv('MODEL_PATH', 'models/best_overall_model.h5')
    IMG_SIZE = int(os.getenv('IMG_SIZE', 128))
    
    # PostgreSQL - Gestion production vs développement
    DATABASE_URL = os.getenv('DATABASE_URL')  # URL complète fournie par Render
    
    # Paramètres individuels (fallback pour développement local)
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = os.getenv('DB_PORT', '5432')
    DB_NAME = os.getenv('DB_NAME', 'malaria_detection')
    DB_USER = os.getenv('DB_USER', 'malaria_user')
    DB_PASSWORD = os.getenv('DB_PASSWORD', '')
    
    @property
    def SQLALCHEMY_DATABASE_URI(self):
        """Retourne l'URI de connexion appropriée"""
        if self.DATABASE_URL:
            # En production (Render), utiliser DATABASE_URL
            return self.DATABASE_URL
        else:
            # En développement, construire l'URI à partir des paramètres
            return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False

config = Config()