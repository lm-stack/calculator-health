# CLAUDE.md — Calculator Health

## Description
Outil de planification automatique des horaires du personnel soignant pour le CHUV.
Utilise OR-Tools (CP-SAT) pour résoudre le Nurse Scheduling Problem.

## Stack
- **Backend** : Python 3.11+ / FastAPI / OR-Tools / Supabase
- **Frontend** : Next.js 14 (App Router) / TypeScript / Tailwind CSS
- **BDD** : Supabase (PostgreSQL)

## Commandes utiles

### Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload        # Lancer le serveur (port 8000)
pytest tests/                         # Lancer les tests
python seed.py                        # Insérer les données de test
```

### Frontend
```bash
cd frontend
npm install
npm run dev                           # Lancer le dev server (port 3000)
npm run build                         # Build de production
```

## Conventions
- Langue de communication : **français**
- Code et noms techniques : **anglais**
- Commits atomiques, messages clairs en anglais
- Ne pas push sans demande explicite

## Architecture solver
- Variables booléennes : (employee, day, shift) → 0/1
- Contraintes dures : 1 shift/jour, couverture, repos 11h, heures max, absences, rôles
- Objectifs : régularité des patterns, préférences, équité nuits/weekends
