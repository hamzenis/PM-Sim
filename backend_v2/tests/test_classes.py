from datetime import UTC, datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.auth.service import create_user
from app.classes.service import (
    ClassError,
    add_student,
    assign_scenario,
    available_scenario_revisions,
    create_class,
    user_can_access_revision,
)
from app.db.models import (
    Base,
    RevisionStatus,
    ScenarioRecord,
    ScenarioRevisionRecord,
    UserRole,
)


@pytest.fixture
def session(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'classes.db'}")
    Base.metadata.create_all(engine)
    with Session(engine, expire_on_commit=False) as database_session:
        yield database_session


def users(session: Session):
    professor = create_user(
        session,
        username="professor",
        password="professor-password",
        role=UserRole.PROFESSOR,
    )
    student = create_user(
        session,
        username="student",
        password="student-password",
        role=UserRole.STUDENT,
    )
    return professor, student


def published_revision(session: Session):
    now = datetime.now(UTC)
    scenario = ScenarioRecord(name="Scenario", created_at=now)
    revision = ScenarioRevisionRecord(
        scenario=scenario,
        revision_number=1,
        schema_version=1,
        status=RevisionStatus.PUBLISHED,
        definition={},
        created_at=now,
        published_at=now,
    )
    session.add(scenario)
    session.commit()
    return revision


def test_professor_can_group_student_and_publish_scenario_to_class(session: Session) -> None:
    professor, student = users(session)
    course_class = create_class(session, professor_id=professor.id, name="PM 2026")
    membership = add_student(
        session,
        professor_id=professor.id,
        class_id=course_class.id,
        username=student.username,
    )
    revision = published_revision(session)
    availability = assign_scenario(
        session,
        professor_id=professor.id,
        class_id=course_class.id,
        scenario_revision_id=revision.id,
    )
    assert membership.user_id == student.id
    assert availability.scenario_revision_id == revision.id
    assert user_can_access_revision(session, student.id, revision.id) is True
    assert available_scenario_revisions(session, student.id) == [revision]


def test_professor_cannot_modify_another_professors_class(session: Session) -> None:
    professor, student = users(session)
    other = create_user(
        session,
        username="other-professor",
        password="other-password",
        role=UserRole.PROFESSOR,
    )
    course_class = create_class(session, professor_id=professor.id, name="Owned")
    with pytest.raises(ClassError, match="class not found"):
        add_student(
            session,
            professor_id=other.id,
            class_id=course_class.id,
            username=student.username,
        )


def test_duplicate_membership_and_availability_are_idempotent(session: Session) -> None:
    professor, student = users(session)
    course_class = create_class(session, professor_id=professor.id, name="PM")
    first_member = add_student(
        session,
        professor_id=professor.id,
        class_id=course_class.id,
        username=student.username,
    )
    second_member = add_student(
        session,
        professor_id=professor.id,
        class_id=course_class.id,
        username=student.username,
    )
    revision = published_revision(session)
    first_availability = assign_scenario(
        session,
        professor_id=professor.id,
        class_id=course_class.id,
        scenario_revision_id=revision.id,
    )
    second_availability = assign_scenario(
        session,
        professor_id=professor.id,
        class_id=course_class.id,
        scenario_revision_id=revision.id,
    )
    assert first_member.id == second_member.id
    assert first_availability.id == second_availability.id
