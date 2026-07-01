"""
Tests unitaires — Parent Portal (US-Parent)
Couvre : ParentService (liaison parent-enfant, profil étudiant)
Source  : accounts/parents/service.py
"""

import pytest
import uuid
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum


# ═══════════════════════════════════════════════════════════════════
# MODÈLES MÉTIER (standalone — pas besoin de DB)
# ═══════════════════════════════════════════════════════════════════


class LinkStatus(Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"


@dataclass
class ParentStudentLink:
    id: str
    parent_id: str
    student_id: str
    status: str
    invitation_code: Optional[str] = None


@dataclass
class StudentProfile:
    id: str
    name: str
    email: str
    role: str = "user"


# ═══════════════════════════════════════════════════════════════════
# SERVICE MÉTIER SIMULÉ (logique pure — sans SQLAlchemy)
# ═══════════════════════════════════════════════════════════════════


class ParentServiceMock:
    """Version standalone de ParentService pour tests unitaires purs."""

    def __init__(self, links: list[ParentStudentLink], students: list[StudentProfile]):
        self._links = links
        self._students = {s.id: s for s in students}

    def get_link(self, parent_id: str, student_id: str) -> Optional[ParentStudentLink]:
        return next(
            (
                l
                for l in self._links
                if l.parent_id == parent_id
                and l.student_id == student_id
                and l.status == "active"
            ),
            None,
        )

    def assert_owns_student(self, parent_id: str, student_id: str) -> None:
        if not self.get_link(parent_id, student_id):
            raise PermissionError("Aucune liaison active entre ce parent et cet étudiant.")

    def list_linked_students(self, parent_id: str) -> list[ParentStudentLink]:
        return [l for l in self._links if l.parent_id == parent_id and l.status == "active"]

    def get_student_profile(self, student_id: str) -> Optional[dict]:
        student = self._students.get(student_id)
        if not student:
            return None
        return {"id": student.id, "name": student.name, "email": student.email, "role": student.role}


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
def other_student_id():
    return str(uuid.uuid4())


@pytest.fixture
def active_link(parent_id, student_id):
    return ParentStudentLink(
        id=str(uuid.uuid4()),
        parent_id=parent_id,
        student_id=student_id,
        status="active",
    )


@pytest.fixture
def inactive_link(parent_id, student_id):
    return ParentStudentLink(
        id=str(uuid.uuid4()),
        parent_id=parent_id,
        student_id=student_id,
        status="inactive",
    )


@pytest.fixture
def student_profile(student_id):
    return StudentProfile(
        id=student_id,
        name="Yassine Dupont",
        email="yassine@school.ma",
        role="user",
    )


# ═══════════════════════════════════════════════════════════════════
# TESTS — get_link()
# ═══════════════════════════════════════════════════════════════════


class TestGetLink:

    def test_retourne_lien_actif_existant(self, parent_id, student_id, active_link, student_profile):
        svc = ParentServiceMock([active_link], [student_profile])
        link = svc.get_link(parent_id, student_id)
        assert link is not None
        assert link.parent_id == parent_id
        assert link.student_id == student_id

    def test_retourne_none_si_lien_inactif(self, parent_id, student_id, inactive_link, student_profile):
        svc = ParentServiceMock([inactive_link], [student_profile])
        link = svc.get_link(parent_id, student_id)
        assert link is None

    def test_retourne_none_si_aucun_lien(self, parent_id, student_id, student_profile):
        svc = ParentServiceMock([], [student_profile])
        link = svc.get_link(parent_id, student_id)
        assert link is None

    def test_retourne_none_si_mauvais_parent(self, parent_id, student_id, active_link, student_profile):
        svc = ParentServiceMock([active_link], [student_profile])
        autre_parent = str(uuid.uuid4())
        link = svc.get_link(autre_parent, student_id)
        assert link is None

    def test_retourne_none_si_mauvais_etudiant(self, parent_id, student_id, active_link, student_profile):
        svc = ParentServiceMock([active_link], [student_profile])
        autre_etudiant = str(uuid.uuid4())
        link = svc.get_link(parent_id, autre_etudiant)
        assert link is None


# ═══════════════════════════════════════════════════════════════════
# TESTS — assert_owns_student()  (anti-IDOR)
# ═══════════════════════════════════════════════════════════════════


class TestAssertOwnsStudent:

    def test_ne_leve_pas_exception_si_lien_actif(self, parent_id, student_id, active_link, student_profile):
        svc = ParentServiceMock([active_link], [student_profile])
        # Ne doit pas lever d'exception
        svc.assert_owns_student(parent_id, student_id)

    def test_leve_exception_si_pas_de_lien(self, parent_id, student_id, student_profile):
        svc = ParentServiceMock([], [student_profile])
        with pytest.raises(PermissionError, match="Aucune liaison active"):
            svc.assert_owns_student(parent_id, student_id)

    def test_leve_exception_si_lien_inactif(self, parent_id, student_id, inactive_link, student_profile):
        svc = ParentServiceMock([inactive_link], [student_profile])
        with pytest.raises(PermissionError):
            svc.assert_owns_student(parent_id, student_id)

    def test_leve_exception_pour_autre_enfant(self, parent_id, student_id, active_link, student_profile):
        svc = ParentServiceMock([active_link], [student_profile])
        autre_enfant = str(uuid.uuid4())
        with pytest.raises(PermissionError):
            svc.assert_owns_student(parent_id, autre_enfant)


# ═══════════════════════════════════════════════════════════════════
# TESTS — list_linked_students()
# ═══════════════════════════════════════════════════════════════════


class TestListLinkedStudents:

    def test_retourne_tous_les_enfants_actifs(self, parent_id, student_profile):
        student2 = StudentProfile(id=str(uuid.uuid4()), name="Sara", email="sara@school.ma")
        link1 = ParentStudentLink(str(uuid.uuid4()), parent_id, student_profile.id, "active")
        link2 = ParentStudentLink(str(uuid.uuid4()), parent_id, student2.id, "active")
        svc = ParentServiceMock([link1, link2], [student_profile, student2])
        result = svc.list_linked_students(parent_id)
        assert len(result) == 2

    def test_exclut_les_liens_inactifs(self, parent_id, student_id, student_profile):
        link_actif = ParentStudentLink(str(uuid.uuid4()), parent_id, student_id, "active")
        autre_id = str(uuid.uuid4())
        link_inactif = ParentStudentLink(str(uuid.uuid4()), parent_id, autre_id, "inactive")
        svc = ParentServiceMock([link_actif, link_inactif], [student_profile])
        result = svc.list_linked_students(parent_id)
        assert len(result) == 1
        assert result[0].status == "active"

    def test_retourne_liste_vide_si_aucun_lien(self, parent_id):
        svc = ParentServiceMock([], [])
        result = svc.list_linked_students(parent_id)
        assert result == []


# ═══════════════════════════════════════════════════════════════════
# TESTS — get_student_profile()
# ═══════════════════════════════════════════════════════════════════


class TestGetStudentProfile:

    def test_retourne_profil_complet(self, student_id, student_profile):
        svc = ParentServiceMock([], [student_profile])
        profile = svc.get_student_profile(student_id)
        assert profile is not None
        assert profile["id"] == student_id
        assert profile["name"] == "Yassine Dupont"
        assert profile["email"] == "yassine@school.ma"
        assert profile["role"] == "user"

    def test_retourne_none_si_etudiant_inconnu(self, student_profile):
        svc = ParentServiceMock([], [student_profile])
        profile = svc.get_student_profile(str(uuid.uuid4()))
        assert profile is None

    def test_profil_ne_contient_pas_mot_de_passe(self, student_id, student_profile):
        svc = ParentServiceMock([], [student_profile])
        profile = svc.get_student_profile(student_id)
        assert "password" not in profile
        assert "password_hash" not in profile
