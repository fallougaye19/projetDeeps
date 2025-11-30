import psycopg2
from config import config

def setup_database():
    """Crée la base de données et l'utilisateur si nécessaire"""
    try:
        # Connexion à PostgreSQL avec les droits d'admin
        conn = psycopg2.connect(
            host=config.DB_HOST,
            port=config.DB_PORT,
            database='postgres',  # Base de données par défaut
            user='postgres',      # Utilisateur admin
            password=input("Entrez le mot de passe PostgreSQL admin: ")
        )
        conn.autocommit = True
        
        with conn.cursor() as cur:
            # Créer l'utilisateur s'il n'existe pas
            cur.execute(f"SELECT 1 FROM pg_roles WHERE rolname = '{config.DB_USER}'")
            if not cur.fetchone():
                cur.execute(f"CREATE USER {config.DB_USER} WITH PASSWORD '{config.DB_PASSWORD}'")
                print(f"✓ Utilisateur {config.DB_USER} créé")
            
            # Créer la base de données si elle n'existe pas
            cur.execute(f"SELECT 1 FROM pg_database WHERE datname = '{config.DB_NAME}'")
            if not cur.fetchone():
                cur.execute(f"CREATE DATABASE {config.DB_NAME} OWNER {config.DB_USER}")
                print(f"✓ Base de données {config.DB_NAME} créée")
            
            # Donner les permissions
            cur.execute(f"GRANT ALL PRIVILEGES ON DATABASE {config.DB_NAME} TO {config.DB_USER}")
            print("✓ Permissions accordées")
        
        conn.close()
        print("✓ Configuration de la base de données terminée avec succès")
        
    except Exception as e:
        print(f"✗ Erreur lors de la configuration: {e}")
        print("\nAssurez-vous que:")
        print("1. PostgreSQL est installé et démarré")
        print("2. Vous avez les droits d'administration")
        print("3. Les paramètres dans .env sont corrects")

if __name__ == '__main__':
    setup_database()