# SenGadget 🇸🇳

Boutique e-commerce de gadgets et accessoires tech, développée avec Django.

## Installation

```bash
git clone https://github.com/ton-username/SenGadget.git
cd SenGadget
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Éditer .env et renseigner les valeurs
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

## Variables d'environnement

| Variable | Description |
|---|---|
| SECRET_KEY | Clé secrète Django |
| DEBUG | True en dev, False en prod |
| ALLOWED_HOSTS | Hôtes autorisés séparés par virgule |
| EMAIL_HOST_USER | Adresse Gmail expéditeur |
| EMAIL_HOST_PASSWORD | Mot de passe d'application Gmail |
