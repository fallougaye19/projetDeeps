import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2 import errors
import os
from config import config

class Database:
    def __init__(self):
        """Initialisation des paramètres DB"""
        self.database_url = config.DATABASE_URL  # Toujours définie
        self.use_database_url = self.database_url is not None

        # Paramètres locaux (dev)
        self.conn_params = {
            'host': config.DB_HOST,
            'port': config.DB_PORT,
            'database': config.DB_NAME,
            'user': config.DB_USER,
            'password': config.DB_PASSWORD
        }

    def get_connection(self):
        """Connexion DB"""
        try:
            if self.use_database_url:
                db_url = self.database_url

                # Conversion Render → psycopg2
                if db_url.startswith("postgres://"):
                    db_url = db_url.replace("postgres://", "postgresql://", 1)

                conn = psycopg2.connect(
                    db_url,
                    sslmode="require"
                )
            else:
                conn = psycopg2.connect(**self.conn_params)

            return conn

        except Exception as e:
            print(f"Erreur de connexion à la base de données: {e}")
            return None


    #############################################
    #                INIT DB                    #
    #############################################
    def init_db(self):
        conn = self.get_connection()
        if not conn:
            print("❌ Impossible de se connecter à la base de données")
            return False

        try:
            with conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        id SERIAL PRIMARY KEY,
                        username VARCHAR(80) UNIQUE NOT NULL,
                        email VARCHAR(120) UNIQUE NOT NULL,
                        password VARCHAR(255) NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        is_active BOOLEAN DEFAULT TRUE
                    )
                """)

                cur.execute("""
                    CREATE TABLE IF NOT EXISTS predictions (
                        id SERIAL PRIMARY KEY,
                        user_id INTEGER REFERENCES users(id),
                        filename VARCHAR(255) NOT NULL,
                        predicted_class VARCHAR(50) NOT NULL,
                        confidence DECIMAL(5,4) NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)

            conn.commit()
            print("✓ Base de données initialisée")
            return True

        except Exception as e:
            print(f"❌ Erreur init_db: {e}")
            conn.rollback()
            return False

        finally:
            conn.close()


    #############################################
    #                LOGIN / USERS              #
    #############################################
    def get_user_by_username(self, username):
        """Retourne l'utilisateur selon username"""
        conn = self.get_connection()
        if not conn:
            return None

        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT * FROM users 
                    WHERE username=%s AND is_active=TRUE
                """, (username,))
                return cur.fetchone()

        except Exception as e:
            print(f"Erreur get_user_by_username: {e}")
            return None

        finally:
            conn.close()


    def create_user(self, username, email, password_hash):
        """Création compte utilisateur"""
        conn = self.get_connection()
        if not conn:
            return None

        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    INSERT INTO users (username, email, password)
                    VALUES (%s, %s, %s)
                    RETURNING id, username, email, created_at
                """, (username, email, password_hash))

                conn.commit()
                return cur.fetchone()

        except psycopg2.IntegrityError:
            conn.rollback()
            return None

        except Exception as e:
            print(f"Erreur create_user: {e}")
            conn.rollback()
            return None

        finally:
            conn.close()


    #############################################
    #                PREDICTIONS                #
    #############################################
    def save_prediction(self, user_id, filename, predicted_class, confidence):
        conn = self.get_connection()
        if not conn:
            return None

        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    INSERT INTO predictions (user_id, filename, predicted_class, confidence)
                    VALUES (%s, %s, %s, %s)
                    RETURNING id, created_at
                """, (user_id, filename, predicted_class, confidence))

                conn.commit()
                return cur.fetchone()

        except Exception as e:
            print(f"Erreur save_prediction: {e}")
            conn.rollback()
            return None

        finally:
            conn.close()


    def get_user_predictions(self, user_id, limit=10):
        conn = self.get_connection()
        if not conn:
            return []

        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT id, filename, predicted_class, confidence, created_at
                    FROM predictions
                    WHERE user_id=%s
                    ORDER BY created_at DESC
                    LIMIT %s
                """, (user_id, limit))

                return cur.fetchall()

        except Exception as e:
            print(f"Erreur get_user_predictions: {e}")
            return []

        finally:
            conn.close()


# Instance globale
db = Database()
