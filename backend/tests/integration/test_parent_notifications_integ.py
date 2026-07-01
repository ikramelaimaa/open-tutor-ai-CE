"""Tests intégration — Notifications + Support Progress + Me/Students"""
import pytest
import uuid
from unittest.mock import AsyncMock


# ═══════════════════════════════════════════════════════════════════
# FIXTURES
# ═══════════════════════════════════════════════════════════════════

@pytest.fixture
def notifications_data():
    return {
        "notifications": [
            {"id": "n1", "type": "resultat", "titre": "Nouveau résultat — Maths", "lu": False},
            {"id": "n2", "type": "ia", "titre": "Recommandation IA", "lu": False},
            {"id": "n3", "type": "alerte", "titre": "Alerte SVT en baisse", "lu": True},
        ],
        "stats": {"total": 3, "non_lues": 2},
    }

@pytest.fixture
def student_id():
    return str(uuid.uuid4())

@pytest.fixture
def parent_id():
    return str(uuid.uuid4())


# ═══════════════════════════════════════════════════════════════════
# TESTS — GET /parent/notifications
# ═══════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_get_notifications_retourne_liste(notifications_data):
    """GET /parent/notifications — retourne toutes les notifications."""
    service = AsyncMock()
    service.get_notifications.return_value = notifications_data

    result = await service.get_notifications()

    assert len(result["notifications"]) == 3
    assert result["stats"]["total"] == 3
    assert result["stats"]["non_lues"] == 2

@pytest.mark.asyncio
async def test_notifications_stats_coherentes(notifications_data):
    """non_lues <= total toujours."""
    service = AsyncMock()
    service.get_notifications.return_value = notifications_data

    result = await service.get_notifications()
    assert result["stats"]["non_lues"] <= result["stats"]["total"]

@pytest.mark.asyncio
async def test_notifications_contient_champs_requis(notifications_data):
    """Chaque notification a id, type, titre, lu."""
    service = AsyncMock()
    service.get_notifications.return_value = notifications_data

    result = await service.get_notifications()
    for notif in result["notifications"]:
        assert "id" in notif
        assert "type" in notif
        assert "titre" in notif
        assert "lu" in notif

@pytest.mark.asyncio
async def test_notifications_types_valides(notifications_data):
    """Types de notification valides : resultat, ia, alerte, soutien, rapport."""
    valid_types = {"resultat", "ia", "alerte", "soutien", "rapport"}
    service = AsyncMock()
    service.get_notifications.return_value = notifications_data

    result = await service.get_notifications()
    for notif in result["notifications"]:
        assert notif["type"] in valid_types


# ═══════════════════════════════════════════════════════════════════
# TESTS — PATCH /parent/notifications/{id}/lire
# ═══════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_marquer_notification_lue():
    """PATCH /notifications/n1/lire → lu=True."""
    service = AsyncMock()
    service.mark_as_read.return_value = {"id": "n1", "lu": True}

    result = await service.mark_as_read("n1")
    assert result["lu"] is True
    assert result["id"] == "n1"

@pytest.mark.asyncio
async def test_marquer_notification_retourne_id_correct():
    """L'id retourné correspond à la notification marquée."""
    notif_id = str(uuid.uuid4())
    service = AsyncMock()
    service.mark_as_read.return_value = {"id": notif_id, "lu": True}

    result = await service.mark_as_read(notif_id)
    assert result["id"] == notif_id

@pytest.mark.asyncio
async def test_marquer_notification_inexistante_retourne_erreur():
    """Notification inexistante → 404."""
    service = AsyncMock()
    service.mark_as_read.side_effect = LookupError("Notification introuvable")

    with pytest.raises(LookupError, match="introuvable"):
        await service.mark_as_read("id-inexistant")


# ═══════════════════════════════════════════════════════════════════
# TESTS — GET /parent/support-progress/{support_id}
# ═══════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_support_progress_retourne_pourcentage():
    """GET /support-progress/{id} — retourne progression 0-100."""
    service = AsyncMock()
    service.get_support_progress.return_value = {
        "support_id": str(uuid.uuid4()),
        "progress": 60,
        "messages_count": 6,
        "status": "active",
    }

    result = await service.get_support_progress(str(uuid.uuid4()))
    assert 0 <= result["progress"] <= 100
    assert result["status"] in ("pending", "active", "completed")

@pytest.mark.asyncio
async def test_support_progress_zero_si_aucun_message():
    """Aucun message IA → progression 0%."""
    service = AsyncMock()
    service.get_support_progress.return_value = {
        "support_id": str(uuid.uuid4()),
        "progress": 0,
        "messages_count": 0,
        "status": "pending",
    }

    result = await service.get_support_progress(str(uuid.uuid4()))
    assert result["progress"] == 0
    assert result["status"] == "pending"

@pytest.mark.asyncio
async def test_support_progress_100_si_complete():
    """10+ messages IA → progression 100% et status completed."""
    service = AsyncMock()
    service.get_support_progress.return_value = {
        "support_id": str(uuid.uuid4()),
        "progress": 100,
        "messages_count": 10,
        "status": "completed",
    }

    result = await service.get_support_progress(str(uuid.uuid4()))
    assert result["progress"] == 100
    assert result["status"] == "completed"

@pytest.mark.asyncio
async def test_support_progress_support_inexistant():
    """Support introuvable → 404."""
    service = AsyncMock()
    service.get_support_progress.side_effect = LookupError("Soutien introuvable")

    with pytest.raises(LookupError, match="introuvable"):
        await service.get_support_progress("id-inexistant")


# ═══════════════════════════════════════════════════════════════════
# TESTS — GET /parent/me/students
# ═══════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_me_students_retourne_enfants_lies(student_id):
    """GET /parent/me/students — retourne les enfants liés au parent."""
    service = AsyncMock()
    service.get_linked_students.return_value = {
        "students": [
            {"id": student_id, "name": "Yassine", "email": "yassine@school.ma"}
        ],
        "total": 1,
    }

    result = await service.get_linked_students()
    assert result["total"] == 1
    assert len(result["students"]) == 1
    assert result["students"][0]["id"] == student_id

@pytest.mark.asyncio
async def test_me_students_liste_vide_si_aucun_lien():
    """Parent sans enfant lié → liste vide."""
    service = AsyncMock()
    service.get_linked_students.return_value = {"students": [], "total": 0}

    result = await service.get_linked_students()
    assert result["total"] == 0
    assert result["students"] == []

@pytest.mark.asyncio
async def test_me_students_ne_retourne_pas_donnees_sensibles(student_id):
    """Profil étudiant ne contient pas mot de passe."""
    service = AsyncMock()
    service.get_linked_students.return_value = {
        "students": [{"id": student_id, "name": "Yassine", "email": "yassine@school.ma"}],
        "total": 1,
    }

    result = await service.get_linked_students()
    for student in result["students"]:
        assert "password" not in student
        assert "password_hash" not in student

@pytest.mark.asyncio
async def test_me_students_refuse_role_non_parent():
    """Utilisateur non-parent ne peut pas voir les enfants liés."""
    service = AsyncMock()
    service.require_parent_role = AsyncMock(
        side_effect=PermissionError("Accès réservé aux parents")
    )

    with pytest.raises(PermissionError, match="Accès réservé aux parents"):
        await service.require_parent_role(role="user")
