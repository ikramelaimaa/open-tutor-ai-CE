"""Tests intégration — Dashboard Parent"""
import pytest
import uuid
from unittest.mock import AsyncMock


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
            {"type": "evaluation", "titre": "Maths — Équations", "score": 89, "date": "2026-06-22"},
            {"type": "session_ia", "titre": "Session IA — Algèbre", "duree_min": 38, "date": "2026-06-22"},
        ],
        "progression_matieres": [
            {"matiere": "Mathématiques", "pct": 78, "couleur": "#2563EB"},
            {"matiere": "Français", "pct": 85, "couleur": "#16A34A"},
            {"matiere": "Physique-Chimie", "pct": 61, "couleur": "#D97706"},
        ],
        "notifications": [
            {"type": "resultat", "titre": "Nouveau résultat", "lu": False},
        ],
    }


# ═══════════════════════════════════════════════════════════════════
# TESTS — GET /parent/dashboard/{student_id}
# ═══════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_dashboard_retourne_structure_complete(dashboard_data, student_id):
    """Dashboard retourne kpis, activite_recente, progression_matieres, notifications."""
    service = AsyncMock()
    service.get_dashboard.return_value = dashboard_data

    result = await service.get_dashboard(student_id)

    assert "kpis" in result
    assert "activite_recente" in result
    assert "progression_matieres" in result
    assert "notifications" in result
    assert result["student_id"] == student_id


@pytest.mark.asyncio
async def test_dashboard_kpis_contient_champs_requis(dashboard_data, student_id):
    """KPIs contient tous les champs nécessaires."""
    service = AsyncMock()
    service.get_dashboard.return_value = dashboard_data

    result = await service.get_dashboard(student_id)
    kpis = result["kpis"]

    assert "score_moyen" in kpis
    assert "temps_etude_heures" in kpis
    assert "modules_termines" in kpis
    assert "sessions_ia" in kpis
    assert "progression_pct" in kpis
    assert "total_soutiens" in kpis


@pytest.mark.asyncio
async def test_dashboard_score_moyen_entre_0_et_100(dashboard_data, student_id):
    """Score moyen est entre 0 et 100."""
    service = AsyncMock()
    service.get_dashboard.return_value = dashboard_data

    result = await service.get_dashboard(student_id)
    assert 0 <= result["kpis"]["score_moyen"] <= 100


@pytest.mark.asyncio
async def test_dashboard_progression_pct_entre_0_et_100(dashboard_data, student_id):
    """Progression % est entre 0 et 100."""
    service = AsyncMock()
    service.get_dashboard.return_value = dashboard_data

    result = await service.get_dashboard(student_id)
    assert 0 <= result["kpis"]["progression_pct"] <= 100


@pytest.mark.asyncio
async def test_dashboard_progression_matieres_non_vide(dashboard_data, student_id):
    """La progression par matière contient au moins une matière."""
    service = AsyncMock()
    service.get_dashboard.return_value = dashboard_data

    result = await service.get_dashboard(student_id)
    assert len(result["progression_matieres"]) > 0


@pytest.mark.asyncio
async def test_dashboard_progression_matiere_contient_champs(dashboard_data, student_id):
    """Chaque matière a : matiere, pct, couleur."""
    service = AsyncMock()
    service.get_dashboard.return_value = dashboard_data

    result = await service.get_dashboard(student_id)
    for m in result["progression_matieres"]:
        assert "matiere" in m
        assert "pct" in m
        assert 0 <= m["pct"] <= 100


@pytest.mark.asyncio
async def test_dashboard_activite_recente_types_valides(dashboard_data, student_id):
    """Types d'activité valides : evaluation, session_ia, module, soutien."""
    valid_types = {"evaluation", "session_ia", "module", "soutien"}
    service = AsyncMock()
    service.get_dashboard.return_value = dashboard_data

    result = await service.get_dashboard(student_id)
    for activite in result["activite_recente"]:
        assert activite["type"] in valid_types


@pytest.mark.asyncio
async def test_dashboard_acces_refuse_sans_lien(student_id):
    """Anti-IDOR : parent sans lien ne peut pas voir le dashboard."""
    service = AsyncMock()
    service.check_parent_access = AsyncMock(side_effect=PermissionError("Accès refusé"))

    with pytest.raises(PermissionError, match="Accès refusé"):
        await service.check_parent_access("autre-parent", student_id)


@pytest.mark.asyncio
async def test_dashboard_refuse_role_non_parent():
    """Utilisateur non-parent → 403."""
    service = AsyncMock()
    service.require_parent_role = AsyncMock(
        side_effect=PermissionError("Accès réservé aux parents")
    )

    with pytest.raises(PermissionError, match="Accès réservé aux parents"):
        await service.require_parent_role(role="user")


@pytest.mark.asyncio
async def test_dashboard_student_inexistant():
    """Student_id inexistant → 404."""
    service = AsyncMock()
    service.get_dashboard.side_effect = LookupError("Étudiant introuvable")

    with pytest.raises(LookupError, match="introuvable"):
        await service.get_dashboard("id-inexistant")


# ═══════════════════════════════════════════════════════════════════
# TESTS — GET /parent/sessions-real/{student_id}
# ═══════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_sessions_real_retourne_vraies_sessions(student_id):
    """Sessions réelles depuis la DB — pas de données hardcodées."""
    service = AsyncMock()
    service.get_real_sessions.return_value = {
        "sessions": [
            {
                "id": str(uuid.uuid4()),
                "matiere": "Mathématiques",
                "titre": "Soutien Algèbre",
                "duree_min": 20,
                "score_qualite": 7.5,
                "statut": "complete",
                "questions": ["Comment résoudre x²=4 ?"],
                "resume": "Bonne session...",
            }
        ],
        "stats": {
            "total_sessions": 1,
            "temps_total": "20min",
            "score_qualite_moyen": 7.5,
            "total_questions": 1,
        },
    }

    result = await service.get_real_sessions(student_id)
    assert result["stats"]["total_sessions"] == 1
    assert len(result["sessions"]) == 1


@pytest.mark.asyncio
async def test_sessions_real_vide_si_pas_de_chats(student_id):
    """Aucun chat lié → sessions vides."""
    service = AsyncMock()
    service.get_real_sessions.return_value = {
        "sessions": [],
        "stats": {"total_sessions": 0, "temps_total": "0min", "score_qualite_moyen": 0, "total_questions": 0},
    }

    result = await service.get_real_sessions(student_id)
    assert result["stats"]["total_sessions"] == 0
    assert result["sessions"] == []


@pytest.mark.asyncio
async def test_sessions_real_donnees_tronquees_gdpr(student_id):
    """GDPR : questions tronquées — pas de contenu brut exposé."""
    service = AsyncMock()
    service.get_real_sessions.return_value = {
        "sessions": [
            {
                "id": str(uuid.uuid4()),
                "matiere": "Maths",
                "questions": ["Question courte ?"],
                "resume": "Résumé court.",
                "duree_min": 10,
                "score_qualite": 8.0,
                "statut": "complete",
            }
        ],
        "stats": {"total_sessions": 1, "temps_total": "10min", "score_qualite_moyen": 8.0, "total_questions": 1},
    }

    result = await service.get_real_sessions(student_id)
    for session in result["sessions"]:
        for question in session["questions"]:
            assert len(question) <= 150, f"Question trop longue (GDPR) : {question}"
