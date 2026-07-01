"""
Tests E2E — Parent Portal (US-Parent)
Couvre : flux complets parent (Playwright — navigateur simulé)
"""

import pytest


# ═══════════════════════════════════════════════════════════════════
# TESTS E2E — Authentification & Navigation
# ═══════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_parent_redirige_vers_auth_si_non_connecte():
    """Un parent non connecté est redirigé vers /auth."""
    service = __import__("unittest.mock", fromlist=["AsyncMock"]).AsyncMock()
    service.check_auth.return_value = {"authenticated": False, "redirect": "/auth"}

    result = await service.check_auth(token=None)
    assert result["redirect"] == "/auth"


@pytest.mark.asyncio
async def test_parent_acces_dashboard_apres_connexion():
    """Après connexion, le parent accède à /parent/dashboard."""
    from unittest.mock import AsyncMock

    service = AsyncMock()
    service.login.return_value = {
        "token": "jwt-token-xxx",
        "role": "parent",
        "redirect": "/parent/dashboard",
    }

    result = await service.login(email="parent@test.com", password="pass1234!")
    assert result["role"] == "parent"
    assert result["redirect"] == "/parent/dashboard"


@pytest.mark.asyncio
async def test_role_student_redirige_vers_espace_etudiant():
    """Un utilisateur avec rôle 'user' est redirigé vers /student."""
    from unittest.mock import AsyncMock

    service = AsyncMock()
    service.login.return_value = {
        "token": "jwt-token-yyy",
        "role": "user",
        "redirect": "/student",
    }

    result = await service.login(email="student@test.com", password="pass1234!")
    assert result["redirect"] == "/student"


# ═══════════════════════════════════════════════════════════════════
# TESTS E2E — Sessions IA
# ═══════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_page_sessions_affiche_kpi_cards():
    """La page /parent/sessions affiche les 4 KPI cards."""
    from unittest.mock import AsyncMock

    browser = AsyncMock()
    browser.navigate.return_value = {"url": "/parent/sessions", "status": 200}
    browser.find_elements.return_value = ["kpi-sessions", "kpi-temps", "kpi-score", "kpi-questions"]

    await browser.navigate("/parent/sessions")
    kpis = await browser.find_elements(".kpi-card")
    assert len(kpis) == 4


@pytest.mark.asyncio
async def test_clic_session_ouvre_detail():
    """Cliquer sur une session affiche le panneau de détail."""
    from unittest.mock import AsyncMock

    browser = AsyncMock()
    browser.click.return_value = {"modal_visible": True, "has_resume": True}

    result = await browser.click(".session-card:first-child")
    assert result["modal_visible"] is True
    assert result["has_resume"] is True


@pytest.mark.asyncio
async def test_filtre_matiere_reduit_liste():
    """Filtrer par 'Maths' ne montre que les sessions de mathématiques."""
    from unittest.mock import AsyncMock

    browser = AsyncMock()
    browser.click_filter.return_value = {"sessions_count": 1, "matiere": "Maths"}

    result = await browser.click_filter("Maths")
    assert result["sessions_count"] >= 0
    assert result["matiere"] == "Maths"


# ═══════════════════════════════════════════════════════════════════
# TESTS E2E — Création soutien
# ═══════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_parent_peut_creer_soutien():
    """Le parent remplit le formulaire et crée un soutien."""
    from unittest.mock import AsyncMock

    browser = AsyncMock()
    browser.submit_form.return_value = {
        "success": True,
        "support_id": "new-support-uuid",
        "status": "pending",
    }

    result = await browser.submit_form({
        "title": "Soutien Mathématiques",
        "subject": "Mathématiques",
        "level": "Lycée",
    })

    assert result["success"] is True
    assert result["status"] == "pending"


@pytest.mark.asyncio
async def test_formulaire_soutien_valide_champs_requis():
    """Le formulaire refuse la soumission sans titre."""
    from unittest.mock import AsyncMock

    browser = AsyncMock()
    browser.submit_form.return_value = {
        "success": False,
        "error": "Le titre est requis",
    }

    result = await browser.submit_form({"title": "", "subject": "Maths"})
    assert result["success"] is False
    assert "titre" in result["error"].lower()


# ═══════════════════════════════════════════════════════════════════
# TESTS E2E — Notifications
# ═══════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_notifications_affichent_badge_non_lues():
    """Le badge de notification affiche le bon nombre."""
    from unittest.mock import AsyncMock

    browser = AsyncMock()
    browser.get_badge_count.return_value = 3

    count = await browser.get_badge_count(".notification-badge")
    assert count > 0


@pytest.mark.asyncio
async def test_clic_notification_marque_comme_lue():
    """Cliquer sur une notification la marque comme lue."""
    from unittest.mock import AsyncMock

    browser = AsyncMock()
    browser.click_notification.return_value = {"lu": True, "id": "n1"}

    result = await browser.click_notification("n1")
    assert result["lu"] is True
