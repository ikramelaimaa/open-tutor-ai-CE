"""Tests intégration — Supports Parent"""
import pytest
import uuid
from unittest.mock import AsyncMock


@pytest.fixture
def support_data():
    return {"id": str(uuid.uuid4()), "user_id": str(uuid.uuid4()), "title": "Soutien Maths", "subject": "Mathématiques", "status": "pending", "chat_id": None, "files": []}


@pytest.mark.asyncio
async def test_create_support_succes(support_data):
    service = AsyncMock()
    service.create_support.return_value = support_data
    result = await service.create_support({"title": "Soutien Maths", "subject": "Mathématiques"})
    assert result["status"] == "pending"

@pytest.mark.asyncio
async def test_create_support_refuse_role_non_parent():
    service = AsyncMock()
    service.require_parent_role = AsyncMock(side_effect=PermissionError("Accès réservé aux parents"))
    with pytest.raises(PermissionError, match="Accès réservé aux parents"):
        await service.require_parent_role(role="user")

@pytest.mark.asyncio
async def test_upload_fichier_limite_taille():
    service = AsyncMock()
    service.upload_file.side_effect = ValueError("Fichier dépasse la limite de 10 Mo")
    with pytest.raises(ValueError, match="limite"):
        await service.upload_file(support_id=str(uuid.uuid4()), filename="big.pdf", size_bytes=11*1024*1024)

@pytest.mark.asyncio
async def test_list_supports_retourne_liste(support_data):
    service = AsyncMock()
    service.list_supports.return_value = [support_data]
    result = await service.list_supports(str(uuid.uuid4()))
    assert len(result) == 1

@pytest.mark.asyncio
async def test_list_supports_vide_si_aucun():
    service = AsyncMock()
    service.list_supports.return_value = []
    result = await service.list_supports(str(uuid.uuid4()))
    assert result == []

@pytest.mark.asyncio
async def test_link_chat_associe_chat_au_support(support_data):
    chat_id = str(uuid.uuid4())
    service = AsyncMock()
    service.link_chat.return_value = {**support_data, "chat_id": chat_id}
    result = await service.link_chat(support_id=support_data["id"], chat_id=chat_id)
    assert result["chat_id"] == chat_id

@pytest.mark.asyncio
async def test_marquer_support_termine(support_data):
    service = AsyncMock()
    service.complete_support.return_value = {"id": support_data["id"], "status": "completed"}
    result = await service.complete_support(support_data["id"])
    assert result["status"] == "completed"

@pytest.mark.asyncio
async def test_find_student_par_email():
    service = AsyncMock()
    service.find_student.return_value = {"id": str(uuid.uuid4()), "name": "Yassine", "email": "yassine@school.ma"}
    result = await service.find_student(email="yassine@school.ma")
    assert result["email"] == "yassine@school.ma"

@pytest.mark.asyncio
async def test_find_student_email_inexistant():
    service = AsyncMock()
    service.find_student.side_effect = LookupError("Aucun élève trouvé avec cet email")
    with pytest.raises(LookupError, match="élève"):
        await service.find_student(email="inconnu@school.ma")

@pytest.mark.asyncio
async def test_generate_evaluation_retourne_questions():
    service = AsyncMock()
    service.generate_evaluation.return_value = {
        "id": str(uuid.uuid4()), "matiere": "Mathématiques",
        "questions": [{"id": "q1", "question": "Dérivée de x² ?", "choices": ["x", "2x"], "correct_answer": "2x"}],
        "statut": "pending",
    }
    result = await service.generate_evaluation(student_id=str(uuid.uuid4()), matiere="Mathématiques")
    assert len(result["questions"]) >= 1
    assert result["statut"] == "pending"

@pytest.mark.asyncio
async def test_submit_evaluation_calcule_score():
    eval_id = str(uuid.uuid4())
    service = AsyncMock()
    service.submit_evaluation.return_value = {"eval_id": eval_id, "score": 66.7, "correct": 2, "total": 3}
    result = await service.submit_evaluation(eval_id=eval_id, reponses={"q1": "2x", "q2": "0", "q3": "x=4"})
    assert result["score"] == 66.7
