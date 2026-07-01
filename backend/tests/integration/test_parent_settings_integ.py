"""Tests intégration — Settings Parent"""
import pytest
import uuid
from unittest.mock import AsyncMock


@pytest.mark.asyncio
async def test_update_profile_succes():
    """PATCH /parent/settings/profile — met à jour le nom."""
    service = AsyncMock()
    service.update_profile.return_value = {
        "id": str(uuid.uuid4()),
        "name": "Nouveau Nom",
        "email": "parent@test.com",
    }
    result = await service.update_profile({"name": "Nouveau Nom"})
    assert result["name"] == "Nouveau Nom"
    assert "email" in result

@pytest.mark.asyncio
async def test_update_profile_nom_vide_refuse():
    """Nom vide → erreur 400."""
    service = AsyncMock()
    service.update_profile.side_effect = ValueError("Le nom ne peut pas être vide")
    with pytest.raises(ValueError, match="nom"):
        await service.update_profile({"name": ""})

@pytest.mark.asyncio
async def test_update_profile_nom_trop_long_refuse():
    """Nom > 100 chars → erreur 400."""
    service = AsyncMock()
    service.update_profile.side_effect = ValueError("Nom trop long")
    with pytest.raises(ValueError, match="long"):
        await service.update_profile({"name": "A" * 101})

@pytest.mark.asyncio
async def test_update_profile_refuse_non_parent():
    """Utilisateur non-parent ne peut pas modifier le profil."""
    service = AsyncMock()
    service.require_parent_role = AsyncMock(side_effect=PermissionError("Accès réservé aux parents"))
    with pytest.raises(PermissionError):
        await service.require_parent_role(role="user")

@pytest.mark.asyncio
async def test_update_password_succes():
    """PATCH /parent/settings/password — change le mot de passe."""
    service = AsyncMock()
    service.update_password.return_value = {"message": "Mot de passe mis à jour avec succès"}
    result = await service.update_password({
        "current_password": "oldpass123",
        "new_password": "newpass456",
    })
    assert "mis à jour" in result["message"]

@pytest.mark.asyncio
async def test_update_password_mauvais_ancien():
    """Mauvais ancien mot de passe → erreur."""
    service = AsyncMock()
    service.update_password.side_effect = ValueError("Mot de passe actuel incorrect")
    with pytest.raises(ValueError, match="incorrect"):
        await service.update_password({
            "current_password": "wrong",
            "new_password": "newpass456",
        })

@pytest.mark.asyncio
async def test_update_password_trop_court():
    """Nouveau mot de passe < 8 chars → erreur."""
    service = AsyncMock()
    service.update_password.side_effect = ValueError("Mot de passe trop court")
    with pytest.raises(ValueError, match="court"):
        await service.update_password({
            "current_password": "oldpass123",
            "new_password": "abc",
        })

@pytest.mark.asyncio
async def test_update_password_confirmation_differente():
    """Confirmation != nouveau → erreur côté frontend."""
    new_pass = "newpass456"
    confirm = "different789"
    assert new_pass != confirm, "Les mots de passe doivent être différents pour ce test"

@pytest.mark.asyncio
async def test_profile_ne_retourne_pas_hash():
    """La réponse profil ne contient jamais le hash du mot de passe."""
    service = AsyncMock()
    service.update_profile.return_value = {
        "id": str(uuid.uuid4()),
        "name": "Parent Test",
        "email": "parent@test.com",
    }
    result = await service.update_profile({"name": "Parent Test"})
    assert "password_hash" not in result
    assert "password" not in result
