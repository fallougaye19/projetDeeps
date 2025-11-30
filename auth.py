from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from database import db
from functools import wraps
import re

auth_bp = Blueprint('auth', __name__)

def validate_email(email):
    """Valide le format de l'email"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password(password):
    """
    Valide la force du mot de passe
    - Au moins 8 caractères
    - Au moins une lettre majuscule
    - Au moins une lettre minuscule
    - Au moins un chiffre
    """
    if len(password) < 8:
        return False, "Le mot de passe doit contenir au moins 8 caractères."
    
    if not re.search(r'[A-Z]', password):
        return False, "Le mot de passe doit contenir au moins une lettre majuscule."
    
    if not re.search(r'[a-z]', password):
        return False, "Le mot de passe doit contenir au moins une lettre minuscule."
    
    if not re.search(r'\d', password):
        return False, "Le mot de passe doit contenir au moins un chiffre."
    
    return True, ""

def validate_username(username):
    """Valide le nom d'utilisateur"""
    if len(username) < 3:
        return False, "Le nom d'utilisateur doit contenir au moins 3 caractères."
    
    if len(username) > 50:
        return False, "Le nom d'utilisateur ne peut pas dépasser 50 caractères."
    
    if not re.match(r'^[a-zA-Z0-9_-]+$', username):
        return False, "Le nom d'utilisateur ne peut contenir que des lettres, chiffres, tirets et underscores."
    
    return True, ""

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Route de connexion"""
    # Si l'utilisateur est déjà connecté, rediriger vers l'accueil
    if 'user_id' in session:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        # Validation des entrées
        if not username or not password:
            flash('Veuillez remplir tous les champs.', 'danger')
            return render_template('login.html')
        
        user = db.get_user_by_username(username)
        
        if user and check_password_hash(user['password'], password):
            # Régénérer l'ID de session pour prévenir la fixation de session
            session.clear()
            session['user_id'] = user['id']
            session['username'] = user['username']
            session.permanent = True
            
            # Log de connexion (optionnel)
            print(f"✓ Connexion réussie: {username}")
            
            flash('Connexion réussie!', 'success')
            
            # Rediriger vers la page demandée ou l'accueil
            next_page = request.args.get('next')
            if next_page and next_page.startswith('/'):
                return redirect(next_page)
            return redirect(url_for('index'))
        else:
            # Message générique pour éviter l'énumération d'utilisateurs
            flash('Nom d\'utilisateur ou mot de passe incorrect.', 'danger')
            print(f"⚠ Tentative de connexion échouée: {username}")
    
    return render_template('login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Route d'inscription"""
    # Si l'utilisateur est déjà connecté, rediriger vers l'accueil
    if 'user_id' in session:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        # Validation du nom d'utilisateur
        valid, message = validate_username(username)
        if not valid:
            flash(message, 'danger')
            return render_template('register.html')
        
        # Validation de l'email
        if not validate_email(email):
            flash('Adresse email invalide.', 'danger')
            return render_template('register.html')
        
        # Validation de la correspondance des mots de passe
        if password != confirm_password:
            flash('Les mots de passe ne correspondent pas.', 'danger')
            return render_template('register.html')
        
        # Validation de la force du mot de passe
        valid, message = validate_password(password)
        if not valid:
            flash(message, 'danger')
            return render_template('register.html')
        
        # Hachage du mot de passe
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        
        # Création de l'utilisateur
        result = db.create_user(username, email, hashed_password)
        
        if result:
            flash('Inscription réussie! Vous pouvez maintenant vous connecter.', 'success')
            print(f"✓ Nouvel utilisateur créé: {username}")
            return redirect(url_for('auth.login'))
        else:
            flash('Ce nom d\'utilisateur ou email existe déjà.', 'danger')
    
    return render_template('register.html')

@auth_bp.route('/logout')
def logout():
    """Route de déconnexion"""
    username = session.get('username', 'Utilisateur inconnu')
    session.clear()
    flash('Vous avez été déconnecté.', 'info')
    print(f"✓ Déconnexion: {username}")
    return redirect(url_for('auth.login'))

def login_required(f):
    """
    Décorateur pour les routes nécessitant une authentification
    Redirige vers la page de connexion si l'utilisateur n'est pas authentifié
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Veuillez vous connecter pour accéder à cette page.', 'warning')
            # Sauvegarder l'URL demandée pour redirection après connexion
            return redirect(url_for('auth.login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function