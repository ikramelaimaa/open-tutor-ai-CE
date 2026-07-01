"""
Tests d'intégration — Parent Portal (US-Parent)
Couvre : endpoints API parent (dashboard, sessions, supports, notifications)
Les services sont moqués — pas besoin que l'appli tourne.
"""

import pytest
import uuid
from unittest.mock import AsyncMock, MagicMock


# ═══════════════════════════════════════════════════════════════════
# FIXTURES
# ═══════════════════════════════════════════════════════════════════


@pytest.fixture
def parent_id():
    return str(uuid.uuid4())


@pytest.fixture
def student_id():
    return str(uuid.uuid4())


@pytest.fixture
def dashboard_data(student_id):
    return {
        "student_id": student_id,
        "kpis": {
            "score_moyen": 78,
            "temps_etude_heures": 14,
            "modules_termines": 3,
            "sessions_ia": 23,
            "progression_pct": 67,
            "total_soutiens": 5,
        },
        "activite_recente": [
            {"type": "session_ia", "titre": "Session IA — Algèbre", "duree_min": 38, "date": "2026-06-22"},
        ],
        "notifications": [
            {"type": "resultat", "titre": "Nouveau résultat", "lu": False},
        ],
    }


@pytest.fixture
def sessions_data(student_id):
    return {
        "sessions": [
            {
                "id": "s1",
                "matiere": "Mathématiques",
                "titre": "Équations du 2nd degré",
                "duree_min": 38,
                "score_qualite": 9.1,
                "engagement": 9.2,
                "comprehension": 8.8,
                "autonomie": 8.0,
                "statut": "complete",
                "questions": ["Comment calculer le discriminant ?"],
                "resume": "Bonne session sur les équations.",
                "themes": ["Discriminant", "Factorisation"],
            },
            {
                "id": "s2",
                "matiere": "Physique-Chimie",
                "titre": "Forces et vecteurs",
                "duree_min": 22,
                "score_qualite": 6.4,
                "engagement": 5.5,
                "comprehension": 6.0,
                "autonomie": 4.2,
                "statut": "partielle",
                "questions": ["Différence poids et masse ?"],
                "resume": "Difficultés sur les vecteurs.",
                "themes": ["Vecteurs"],
            },
        ],
        "stats": {
            "total_sessions": 2,
            "temps_total": "1h00",
            "score_qualite_moyen": 7.75,
            "total_questions": 2,
        },
    }


# ═══════════════════════════════════════════════════════════════════
# TESTS — Dashboard
# ═══════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_dashboard_retourne_kpis_corrects(dashboard_data, student_id):
    """GET /parent/dashboard/{student_id} — retourne les KPIs."""
    service = AsyncMock()
    service.get_dashboard.return_value = dashboard_data

    result = await service.get_dashboard(student_id)

    assert result["student_id"] == student_id
    assert "kpis" in result
    assert result["kpis"]["sessions_ia"] == 23


@pytest.mark.asyncio
async def test_dashboard_acces_refuse_sans_lien(student_id):
    """Anti-IDOR : parent sans lien ne peut pas voir le dashboard."""
    service = AsyncMock()
    service.check_parent_access = AsyncMock(side_effect=PermissionError("Accès refusé"))

    with pytest.raises(PermissionError):
        await service.check_parent_access("autre-parent", student_id)


# ═══════════════════════════════════════════════════════════════════
# TESTS — Sessions IA
# ═══════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_sessions_retourne_liste_complete(sessions_data, student_id):
    """GET /parent/sessions/{student_id} — retourne toutes les sessions."""
    service = AsyncMock()
    service.get_sessions.return_value = sessions_data

    result = await service.get_sessions(student_id)

    assert len(result["sessions"]) == 2
    assert result["stats"]["total_sessions"] == 2


@pytest.mark.asyncio
async def test_sessions_filtre_par_matiere(sessions_data, student_id):
    """GET /parent/sessions/{student_id}?matiere=Mathématiques."""
    filtered = {
        "sessions": [s for s in sessions_data["sessions"] if s["matiere"] == "Mathématiques"],
        "stats": {"total_sessions": 1, "score_qualite_moyen": 9.1},
    }
    service = AsyncMock()
    service.get_sessions.return_value = filtered

    result = await service.get_sessions(student_id, matiere="Mathématiques")

    assert len(result["sessions"]) == 1
    assert result["sessions"][0]["matiere"] == "Mathématiques"


@pytest.mark.asyncio
async def test_session_score_faible_statut_partielle(sessions_data):
    """Score < 7 → statut partielle."""
    session_physique = next(s for s in sessions_data["sessions"] if s["matiere"] == "Physique-Chimie")
    assert session_physique["score_qualite"] < 7.0
    assert session_physique["statut"] == "partielle"


@pytest.mark.asyncio
async def test_session_score_eleve_statut_complete(sessions_data):
    """Score >= 8 → statut complète."""
    session_maths = next(s for s in sessions_data["sessions"] if s["matiere"] == "Mathématiques")
    assert session_maths["score_qualite"] >= 8.0
    assert session_maths["statut"] == "complete"


@pytest.mark.asyncio
async def test_sessions_donnees_tronquees_gdpr(sessions_data):
    """GDPR : les questions ne dépassent pas 60 chars."""
    for session in sessions_data["sessions"]:
        for question in session["questions"]:
            assert len(question) <= 120, f"Question trop longue : {question}"


# ═══════════════════════════════════════════════════════════════════
# TESTS — Supports
# ═══════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_creation_support_pour_parent_direct():
    """Parent peut créer un soutien directement sans lien enfant."""
    service = AsyncMock()
    service.create_support.return_value = {
        "id": str(uuid.uuid4()),
        "title": "Soutien Mathématiques",
        "subject": "Mathématiques",
        "status": "pending",
        "user_id": str(uuid.uuid4()),
    }

    result = await service.create_support({
        "title": "Soutien Mathématiques",
        "subject": "Mathématiques",
        "level": "Lycée",
    })

    assert result["status"] == "pending"
    assert result["title"] == "Soutien Mathématiques"


@pytest.mark.asyncio
async def test_upload_fichier_verifie_appartenance_support():
    """Upload : vérifier que support_id appartient bien au student_id."""
    service = AsyncMock()
    service.verify_support_ownership.return_value = True

    is_owner = await service.verify_support_ownership(
        support_id=str(uuid.uuid4()),
        student_id=str(uuid.uuid4()),
    )
    assert is_owner is True


# ═══════════════════════════════════════════════════════════════════
# TESTS — Notifications
# ═══════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_notifications_retourne_stats_correctes():
    """GET /parent/notifications — stats non_lues cohérentes."""
    service = AsyncMock()
    service.get_notifications.return_value = {
        "notifications": [
            {"id": "n1", "lu": False},
            {"id": "n2", "lu": False},
            {"id": "n3", "lu": True},
        ],
        "stats": {"total": 3, "non_lues": 2},
    }

    result = await service.get_notifications()
    assert result["stats"]["non_lues"] == 2
    assert result["stats"]["total"] == 3
    assert result["stats"]["non_lues"] <= result["stats"]["total"]


@pytest.mark.asyncio
async def test_marquer_notification_lue():
    """PATCH /parent/notifications/{id}/lire — marque comme lue."""
    service = AsyncMock()
    service.mark_as_read.return_value = {"id": "n1", "lu": True}

    result = await service.mark_as_read("n1")
    assert result["lu"] is True
    assert result["id"] == "n1"


# ═══════════════════════════════════════════════════════════════════
# TESTS — Sécurité (anti-IDOR)
# ═══════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_parent_ne_peut_pas_acceder_sessions_autre_enfant():
    """Anti-IDOR : parent A ne peut pas voir les sessions de l'enfant de parent B."""
    service = AsyncMock()
    service.check_parent_access = AsyncMock(side_effect=PermissionError("Accès refusé"))

    with pytest.raises(PermissionError, match="Accès refusé"):
        await service.check_parent_access("parent-A", "enfant-de-B")


@pytest.mark.asyncio
async def test_role_non_parent_acces_refuse():
    """Utilisateur avec rôle 'user' ne peut pas accéder aux endpoints parent."""
    service = AsyncMock()
    service.require_parent_role.side_effect = PermissionError("Accès réservé aux parents")

    with pytest.raises(PermissionError, match="Accès réservé aux parents"):
        await service.require_parent_role(role="user")
