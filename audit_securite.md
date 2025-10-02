# Rapport d'Audit de Sécurité - quick_switch.py

## ✅ Points Positifs

1. **Gestion des permissions** : Le code gère les PermissionError lors de l'accès aux fichiers de profil utilisateur (lignes 68-73)
2. **Validation des utilisateurs** : Filtre les utilisateurs système (UID < 1000) et les comptes sans shell valide (lignes 136-142)
3. **Gestion des erreurs** : Try/except autour des opérations subprocess et fichier
4. **Timeouts** : Utilisation de timeouts (5s) sur les subprocess pour éviter les blocages (lignes 234, 252)

## 🔴 Vulnérabilités Critiques

### 1. Injection de Commandes (CRITIQUE)
- **Localisation** : Ligne 227
- **Problème** : `string:{username}` injecté directement dans dbus-send sans validation
- **Impact** : Un nom d'utilisateur malformé pourrait permettre l'exécution de commandes arbitraires
- **Exploitation** : Si un utilisateur système nommé `user"; malicious-command; #` existait
- **Code vulnérable** :
```python
['dbus-send', '--system', '--type=method_call',
 '--dest=org.freedesktop.DisplayManager',
 '/org/freedesktop/DisplayManager/Seat0',
 'org.freedesktop.DisplayManager.Seat.SwitchToUser',
 f'string:{username}', 'string:']
```

### 2. Path Traversal
- **Localisation** : Lignes 61-73
- **Problème** : Construction de chemins avec `Path(home_dir) / ".face"` sans validation
- **Impact** : Si home_dir est manipulé, pourrait accéder à des fichiers arbitraires
- **Mitigation partielle** : pwd.getpwall() fournit normalement des données sûres
- **Code concerné** :
```python
face_path = Path(home_dir) / ".face"
if face_path.exists():
    return str(face_path)
```

### 3. Privilege Escalation Potentielle
- **Localisation** : Lignes 219-254
- **Problème** : Appels subprocess avec loginctl/dm-tool sans vérification des permissions
- **Impact** : Dépend des politiques PolicyKit, mais pourrait permettre des changements de session non autorisés

## ⚠️ Problèmes de Sécurité Modérés

### 4. Information Disclosure
- **Localisation** : Lignes 61-67
- **Problème** : Tentative de lecture de `/var/lib/AccountsService/icons/{username}` et `~/.face`
- **Impact** : Expose les avatars utilisateurs, mais faible criticité

### 5. Absence de Validation d'Entrée
- **Localisation** : Ligne 197
- **Problème** : `username` provient de `row.user_data` sans validation avant utilisation
- **Note** : Bien que provenant de pwd.getpwall(), absence de contrôle sanitaire

### 6. Gestion d'Erreurs Trop Large
- **Localisation** : Lignes 104-106
- **Problème** : `except Exception: pass` cache toutes les erreurs de chargement d'images
- **Impact** : Masque des problèmes potentiels de sécurité
- **Code concerné** :
```python
try:
    pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(pic_path, 48, 48, True)
    texture = Gio.Texture.new_for_pixbuf(pixbuf)
    avatar.set_custom_image(texture)
except Exception:
    pass  # Use default avatar if image loading fails
```

## 📋 Bonnes Pratiques Non Respectées

### 7. Logs de Debug en Production
- **Localisation** : Lignes 231-254
- **Problème** : Multiples `print()` qui exposent des détails d'implémentation
- **Recommandation** : Utiliser logging avec niveaux appropriés

### 8. Manque de Sanitization
- **Problème** : Les noms d'utilisateurs ne sont jamais échappés avant utilisation dans les commandes shell
- **Recommandation** : Utiliser `shlex.quote()` pour les arguments shell

### 9. Hardcoded Paths
- **Problème** : `/var/lib/AccountsService/icons/` (ligne 62)
- **Recommandation** : Devrait utiliser des constantes configurables

## 🛠️ Recommandations

### Haute Priorité

#### Correction de l'injection de commandes
```python
# Avant ligne 227, ajouter:
import shlex
username_safe = shlex.quote(username)

# Ou mieux, valider le nom d'utilisateur:
import re
if not re.match(r'^[a-z_][a-z0-9_-]*[$]?$', username):
    raise ValueError("Invalid username")
```

#### Validation stricte des noms d'utilisateurs
```python
def validate_username(username):
    """Validate username against POSIX standards"""
    if not username:
        return False
    # POSIX username regex
    if not re.match(r'^[a-z_]([a-z0-9_-]{0,31}|[a-z0-9_-]{0,30}\$)$', username):
        return False
    return True
```

### Moyenne Priorité

#### Validation des chemins home
```python
def get_profile_picture(self, username, home_dir):
    """Get user profile picture from various locations"""
    # Validate home_dir is under /home/
    home_path = Path(home_dir).resolve()
    if not str(home_path).startswith('/home/'):
        return None
    # ... rest of the code
```

#### Remplacement des print() par logging
```python
import logging

logger = logging.getLogger(__name__)

# Remplacer:
print(f"Trying {description}...")
# Par:
logger.debug(f"Trying {description}...")
```

#### Gestion d'erreurs spécifique
```python
# Remplacer:
except Exception:
    pass
# Par:
except (GLib.Error, OSError) as e:
    logger.warning(f"Failed to load profile picture: {e}")
```

### Basse Priorité

- Ajouter des tests unitaires pour les cas limites
- Implémenter un rate limiting pour éviter le spam de tentatives de switch
- Ajouter des logs d'audit pour tracer les changements d'utilisateur
- Utiliser des constantes pour les chemins système

## 🎯 Score Global : 5/10

**Criticité** : MOYENNE-HAUTE en raison du risque d'injection de commandes dans dbus-send.

Le code est globalement correct pour un outil desktop personnel, mais nécessite des améliorations importantes pour un déploiement en production ou multi-utilisateurs.

## 📝 Checklist de Sécurisation

- [ ] Ajouter validation stricte des noms d'utilisateurs
- [ ] Échapper/valider les paramètres dans les commandes subprocess
- [ ] Valider les chemins home avant accès fichier
- [ ] Remplacer print() par logging approprié
- [ ] Affiner les exceptions catchées
- [ ] Ajouter des tests de sécurité unitaires
- [ ] Implémenter un système de logs d'audit
- [ ] Externaliser les chemins hardcodés en configuration
- [ ] Documenter les permissions PolicyKit requises
- [ ] Ajouter rate limiting sur les tentatives de switch
