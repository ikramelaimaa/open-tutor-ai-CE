"""Tests unitaires — Évaluations Parent"""
import pytest
import uuid
from dataclasses import dataclass, field
from typing import Optional, List


@dataclass
class QCMQuestion:
    id: str
    question: str
    choices: List[str]
    correct_answer: str
    explanation: str = ""

    def is_correct(self, answer: str) -> bool:
        return answer.strip().lower() == self.correct_answer.strip().lower()


@dataclass
class Evaluation:
    id: str
    student_id: str
    matiere: str
    score: Optional[float] = None
    questions: List[QCMQuestion] = field(default_factory=list)
    statut: str = "pending"
    SCORE_SEUIL_REUSSITE: float = 60.0

    def calculer_score(self, reponses: dict) -> float:
        if not self.questions:
            raise ValueError("Aucune question dans l'évaluation")
        correct = sum(1 for q in self.questions if reponses.get(q.id) and q.is_correct(reponses[q.id]))
        return round((correct / len(self.questions)) * 100, 1)

    def est_reussie(self) -> bool:
        if self.score is None:
            return False
        return self.score >= self.SCORE_SEUIL_REUSSITE


@pytest.fixture
def questions_maths():
    return [
        QCMQuestion("q1", "Dérivée de x² ?", ["x", "2x", "x²", "2"], "2x"),
        QCMQuestion("q2", "Que vaut sin(0) ?", ["0", "1", "-1", "π"], "0"),
        QCMQuestion("q3", "Résoudre x² = 4", ["x=2", "x=-2", "x=±2", "x=4"], "x=±2"),
    ]


@pytest.fixture
def evaluation_maths(questions_maths):
    return Evaluation(id=str(uuid.uuid4()), student_id=str(uuid.uuid4()), matiere="Mathématiques", questions=questions_maths)


class TestQCMQuestion:
    def test_bonne_reponse_retourne_true(self, questions_maths):
        assert questions_maths[0].is_correct("2x") is True

    def test_mauvaise_reponse_retourne_false(self, questions_maths):
        assert questions_maths[0].is_correct("x") is False

    def test_reponse_insensible_casse(self, questions_maths):
        assert questions_maths[0].is_correct("2X") is True

    def test_reponse_avec_espaces_acceptee(self, questions_maths):
        assert questions_maths[0].is_correct("  2x  ") is True

    def test_reponse_vide_retourne_false(self, questions_maths):
        assert questions_maths[0].is_correct("") is False


class TestCalculerScore:
    def test_score_100_si_toutes_correctes(self, evaluation_maths):
        assert evaluation_maths.calculer_score({"q1": "2x", "q2": "0", "q3": "x=±2"}) == 100.0

    def test_score_0_si_toutes_incorrectes(self, evaluation_maths):
        assert evaluation_maths.calculer_score({"q1": "x", "q2": "1", "q3": "x=4"}) == 0.0

    def test_score_partiel(self, evaluation_maths):
        assert evaluation_maths.calculer_score({"q1": "2x", "q2": "0", "q3": "x=4"}) == pytest.approx(66.7, rel=0.01)

    def test_score_sans_questions_leve_exception(self):
        eval_vide = Evaluation(id=str(uuid.uuid4()), student_id=str(uuid.uuid4()), matiere="Maths", questions=[])
        with pytest.raises(ValueError, match="Aucune question"):
            eval_vide.calculer_score({})


class TestEstReussie:
    def test_reussie_si_score_superieur_seuil(self, evaluation_maths):
        evaluation_maths.score = 75.0
        assert evaluation_maths.est_reussie() is True

    def test_reussie_si_score_egal_seuil(self, evaluation_maths):
        evaluation_maths.score = 60.0
        assert evaluation_maths.est_reussie() is True

    def test_echouee_si_score_inferieur_seuil(self, evaluation_maths):
        evaluation_maths.score = 55.0
        assert evaluation_maths.est_reussie() is False

    def test_echouee_si_score_nul(self, evaluation_maths):
        evaluation_maths.score = None
        assert evaluation_maths.est_reussie() is False
