import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2 import errors
import os
from config import config

class Database:
    def __init__(self):
        self.conn_params = {
            'host': config.DB_HOST,
            'port': config.DB_PORT,
            'database': config.DB_NAME,
            'user': config.DB_USER,
            'password': config.DB_PASSWORD
        }
    
    def get_connection(self):
        """Établit une connexion à la base de données"""
        try:
            conn = psycopg2.connect(**self.conn_params)
            return conn
        except Exception as e:
            print(f"Erreur de connexion à la base de données: {e}")
            return None
    
    def init_db(self):
        """Initialise la base de données avec les tables nécessaires"""
        conn = self.get_connection()
        if not conn:
            return False
        
        try:
            with conn.cursor() as cur:
                # Table des utilisateurs
                cur.execute('''
                    CREATE TABLE IF NOT EXISTS users (
                        id SERIAL PRIMARY KEY,
                        username VARCHAR(80) UNIQUE NOT NULL,
                        email VARCHAR(120) UNIQUE NOT NULL,
                        password VARCHAR(255) NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        is_active BOOLEAN DEFAULT TRUE
                    )
                ''')
                
                # Table des prédictions (historique)
                cur.execute('''
                    CREATE TABLE IF NOT EXISTS predictions (
                        id SERIAL PRIMARY KEY,
                        user_id INTEGER REFERENCES users(id),
                        filename VARCHAR(255) NOT NULL,
                        predicted_class VARCHAR(50) NOT NULL,
                        confidence DECIMAL(5,4) NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
            conn.commit()
            print("✓ Base de données initialisée avec succès")
            return True
            
        except Exception as e:
            print(f"Erreur lors de l'initialisation de la base de données: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def create_user(self, username, email, password_hash):
        """Crée un nouvel utilisateur"""
        conn = self.get_connection()
        if not conn:
            return None
        
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                query = '''
                    INSERT INTO users (username, email, password) 
                    VALUES (%s, %s, %s) 
                    RETURNING id, username, email, created_at
                '''
                cur.execute(query, (username, email, password_hash))
                result = cur.fetchone()
                conn.commit()
                return result
        except psycopg2.IntegrityError as e:
            # Violation de contrainte UNIQUE (username ou email déjà existant)
            print(f"Erreur d'intégrité: {e}")
            conn.rollback()
            return None
        except Exception as e:
            print(f"Erreur lors de la création de l'utilisateur: {e}")
            conn.rollback()
            return None
        finally:
            conn.close()
    
    def get_user_by_username(self, username):
        """Récupère un utilisateur par son nom d'utilisateur"""
        conn = self.get_connection()
        if not conn:
            return None
        
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                query = 'SELECT * FROM users WHERE username = %s AND is_active = TRUE'
                cur.execute(query, (username,))
                result = cur.fetchone()
                return result
        except Exception as e:
            print(f"Erreur lors de la récupération de l'utilisateur: {e}")
            return None
        finally:
            conn.close()
    
    def save_prediction(self, user_id, filename, predicted_class, confidence):
        """Sauvegarde une prédiction dans l'historique"""
        conn = self.get_connection()
        if not conn:
            return None
        
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                query = '''
                    INSERT INTO predictions (user_id, filename, predicted_class, confidence)
                    VALUES (%s, %s, %s, %s)
                    RETURNING id, created_at
                '''
                cur.execute(query, (user_id, filename, predicted_class, confidence))
                result = cur.fetchone()
                conn.commit()
                return result
        except Exception as e:
            print(f"Erreur lors de la sauvegarde de la prédiction: {e}")
            conn.rollback()
            return None
        finally:
            conn.close()
    
    def get_user_predictions(self, user_id, limit=10):
        """Récupère l'historique des prédictions d'un utilisateur"""
        conn = self.get_connection()
        if not conn:
            return []
        
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                query = '''
                    SELECT id, filename, predicted_class, confidence, created_at
                    FROM predictions 
                    WHERE user_id = %s 
                    ORDER BY created_at DESC 
                    LIMIT %s
                '''
                cur.execute(query, (user_id, limit))
                result = cur.fetchall()
                return result
        except Exception as e:
            print(f"Erreur lors de la récupération des prédictions: {e}")
            return []
        finally:
            conn.close()

# Instance globale de la base de données
db = Database()