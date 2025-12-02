import psycopg2
from psycopg2.extras import RealDictCursor
import os
from config import config

class Database:
    def __init__(self):
        """
        Initialise la configuration de la BDD.
        On utilise DATABASE_URL en production (Render),
        sinon les paramètres individuels en local.
        """
        self.database_url = config.DATABASE_URL  # Toujours défini, même si None
        self.use_database_url = self.database_url is not None

        # Paramètres individuels (développement local)
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
            if self.use_database_url:
                db_url = self.database_url

                # 🚨 Convertir postgres:// → postgresql:// (Render)
                if db_url.startswith("postgres://"):
                    db_url = db_url.replace("postgres://", "postgresql://", 1)

                conn = psycopg2.connect(
                    db_url,
                    sslmode='require'   # obligatoire sur Render
                )
            else:
                conn = psycopg2.connect(**self.conn_params)

            return conn

        except Exception as e:
            print(f"Erreur de connexion à la base de données: {e}")
            return None

    def init_db(self):
        """Initialise la base avec les tables nécessaires"""
        conn = self.get_connection()
        if not conn:
            print("❌ Impossible de se connecter à la base de données")
            return False

        try:
            with conn.cursor() as cur:
                cur.execute('''
                    CREATE TABLE IF NOT EXISTS users (
                        id SERIAL PRIMARY KEY,
                        username VARCHAR(80) UNIQUE NOT NULL,
                        email VARCHAR(120) UNIQUE NOT NULL,
                        password VARCHAR(255) NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        is_active BOOLEAN DEFAULT TRUE
                    );
                ''')

                cur.execute('''
                    CREATE TABLE IF NOT EXISTS predictions (
                        id SERIAL PRIMARY KEY,
                        user_id INTEGER REFERENCES users(id),
                        filename VARCHAR(255) NOT NULL,
                        predicted_class VARCHAR(50) NOT NULL,
                        confidence DECIMAL(5,4) NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                ''')

            conn.commit()
            print("✓ Base de données initialisée avec succès")
            return True
        
        except Exception as e:
            print(f"❌ Erreur lors de l'initialisation de la base de données: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()

    # --- autres méthodes identiques ---

db = Database()
