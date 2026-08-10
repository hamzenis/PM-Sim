from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import (
    ClassMembershipRecord,
    ClassRecord,
    RevisionStatus,
    ScenarioAvailabilityRecord,
    ScenarioRecord,
    ScenarioRevisionRecord,
    UserRecord,
    UserRole,
)


class ClassError(ValueError):
    pass


def create_class(session: Session, *, professor_id: str, name: str) -> ClassRecord:
    normalized = name.strip()
    if not normalized:
        raise ClassError("class name is required")
    professor = session.get(UserRecord, professor_id)
    if professor is None or professor.role != UserRole.PROFESSOR:
        raise ClassError("professor not found")
    course_class = ClassRecord(
        name=normalized,
        professor_id=professor_id,
        created_at=datetime.now(UTC),
    )
    session.add(course_class)
    session.commit()
    session.refresh(course_class)
    return course_class


def list_professor_classes(session: Session, professor_id: str) -> list[ClassRecord]:
    statement = (
        select(ClassRecord)
        .where(
            ClassRecord.professor_id == professor_id,
            ClassRecord.archived_at.is_(None),
        )
        .order_by(ClassRecord.name, ClassRecord.id)
    )
    return list(session.scalars(statement))


def rename_class(
    session: Session,
    *,
    professor_id: str,
    class_id: str,
    name: str,
) -> ClassRecord:
    course_class = _active_owned_class(session, class_id, professor_id)
    normalized = name.strip()
    if not normalized:
        raise ClassError("class name is required")
    course_class.name = normalized
    session.commit()
    session.refresh(course_class)
    return course_class


def archive_class(session: Session, *, professor_id: str, class_id: str) -> ClassRecord:
    course_class = _owned_class(session, class_id, professor_id)
    if course_class.archived_at is None:
        course_class.archived_at = datetime.now(UTC)
        session.commit()
        session.refresh(course_class)
    return course_class


def list_students(session: Session, *, professor_id: str, class_id: str) -> list[UserRecord]:
    course_class = _owned_class(session, class_id, professor_id)
    statement = (
        select(UserRecord)
        .join(ClassMembershipRecord, ClassMembershipRecord.user_id == UserRecord.id)
        .where(ClassMembershipRecord.class_id == course_class.id)
        .order_by(UserRecord.username, UserRecord.id)
    )
    return list(session.scalars(statement))


def remove_student(
    session: Session,
    *,
    professor_id: str,
    class_id: str,
    student_id: str,
) -> None:
    course_class = _active_owned_class(session, class_id, professor_id)
    membership = session.scalar(
        select(ClassMembershipRecord).where(
            ClassMembershipRecord.class_id == course_class.id,
            ClassMembershipRecord.user_id == student_id,
        )
    )
    if membership is None:
        raise ClassError("student membership not found")
    session.delete(membership)
    session.commit()


def list_assigned_scenarios(
    session: Session,
    *,
    professor_id: str,
    class_id: str,
) -> list[ScenarioRevisionRecord]:
    course_class = _owned_class(session, class_id, professor_id)
    statement = (
        select(ScenarioRevisionRecord)
        .join(
            ScenarioAvailabilityRecord,
            ScenarioAvailabilityRecord.scenario_revision_id == ScenarioRevisionRecord.id,
        )
        .where(ScenarioAvailabilityRecord.class_id == course_class.id)
        .order_by(ScenarioRevisionRecord.id)
    )
    return list(session.scalars(statement))


def unassign_scenario(
    session: Session,
    *,
    professor_id: str,
    class_id: str,
    scenario_revision_id: str,
) -> None:
    course_class = _active_owned_class(session, class_id, professor_id)
    availability = session.scalar(
        select(ScenarioAvailabilityRecord).where(
            ScenarioAvailabilityRecord.class_id == course_class.id,
            ScenarioAvailabilityRecord.scenario_revision_id == scenario_revision_id,
        )
    )
    if availability is None:
        raise ClassError("scenario assignment not found")
    session.delete(availability)
    session.commit()


def add_student(
    session: Session,
    *,
    professor_id: str,
    class_id: str,
    username: str,
) -> ClassMembershipRecord:
    course_class = _active_owned_class(session, class_id, professor_id)
    student = session.scalar(
        select(UserRecord).where(
            UserRecord.username == username.strip().lower(),
            UserRecord.role == UserRole.STUDENT,
        )
    )
    if student is None:
        raise ClassError("student not found")
    existing = session.scalar(
        select(ClassMembershipRecord).where(
            ClassMembershipRecord.class_id == course_class.id,
            ClassMembershipRecord.user_id == student.id,
        )
    )
    if existing is not None:
        return existing
    membership = ClassMembershipRecord(
        class_id=course_class.id,
        user_id=student.id,
        created_at=datetime.now(UTC),
    )
    session.add(membership)
    session.commit()
    session.refresh(membership)
    return membership


def assign_scenario(
    session: Session,
    *,
    professor_id: str,
    class_id: str,
    scenario_revision_id: str,
) -> ScenarioAvailabilityRecord:
    course_class = _active_owned_class(session, class_id, professor_id)
    revision = session.get(ScenarioRevisionRecord, scenario_revision_id)
    if revision is None or revision.status != RevisionStatus.PUBLISHED:
        raise ClassError("a published scenario revision is required")
    scenario = session.get(ScenarioRecord, revision.scenario_id)
    if scenario is None or scenario.owner_id != professor_id or scenario.archived_at is not None:
        raise ClassError("published scenario revision not found")
    existing = session.scalar(
        select(ScenarioAvailabilityRecord).where(
            ScenarioAvailabilityRecord.class_id == course_class.id,
            ScenarioAvailabilityRecord.scenario_revision_id == revision.id,
        )
    )
    if existing is not None:
        return existing
    availability = ScenarioAvailabilityRecord(
        class_id=course_class.id,
        scenario_revision_id=revision.id,
        created_at=datetime.now(UTC),
    )
    session.add(availability)
    session.commit()
    session.refresh(availability)
    return availability


def available_scenario_revisions(
    session: Session,
    user_id: str,
) -> list[ScenarioRevisionRecord]:
    statement = (
        select(ScenarioRevisionRecord)
        .join(
            ScenarioAvailabilityRecord,
            ScenarioAvailabilityRecord.scenario_revision_id == ScenarioRevisionRecord.id,
        )
        .join(
            ClassMembershipRecord,
            ClassMembershipRecord.class_id == ScenarioAvailabilityRecord.class_id,
        )
        .join(ClassRecord, ClassRecord.id == ClassMembershipRecord.class_id)
        .join(ScenarioRecord, ScenarioRecord.id == ScenarioRevisionRecord.scenario_id)
        .where(
            ClassMembershipRecord.user_id == user_id,
            ClassRecord.archived_at.is_(None),
            ScenarioRecord.archived_at.is_(None),
        )
        .distinct()
        .order_by(ScenarioRevisionRecord.id)
    )
    return list(session.scalars(statement))


def user_can_access_revision(session: Session, user_id: str, revision_id: str) -> bool:
    statement = (
        select(ScenarioAvailabilityRecord.id)
        .join(
            ClassMembershipRecord,
            ClassMembershipRecord.class_id == ScenarioAvailabilityRecord.class_id,
        )
        .join(ClassRecord, ClassRecord.id == ClassMembershipRecord.class_id)
        .join(
            ScenarioRevisionRecord,
            ScenarioRevisionRecord.id == ScenarioAvailabilityRecord.scenario_revision_id,
        )
        .join(ScenarioRecord, ScenarioRecord.id == ScenarioRevisionRecord.scenario_id)
        .where(
            ClassMembershipRecord.user_id == user_id,
            ScenarioAvailabilityRecord.scenario_revision_id == revision_id,
            ClassRecord.archived_at.is_(None),
            ScenarioRecord.archived_at.is_(None),
        )
    )
    return session.scalar(statement) is not None


def accessible_class_for_revision(
    session: Session,
    *,
    user_id: str,
    revision_id: str,
    class_id: str | None = None,
) -> str | None:
    """Resolve the class through which a student may start this scenario revision."""
    statement = (
        select(ClassMembershipRecord.class_id)
        .join(
            ScenarioAvailabilityRecord,
            ScenarioAvailabilityRecord.class_id == ClassMembershipRecord.class_id,
        )
        .join(ClassRecord, ClassRecord.id == ClassMembershipRecord.class_id)
        .where(
            ClassMembershipRecord.user_id == user_id,
            ScenarioAvailabilityRecord.scenario_revision_id == revision_id,
            ClassRecord.archived_at.is_(None),
        )
        .order_by(ClassMembershipRecord.class_id)
    )
    if class_id is not None:
        statement = statement.where(ClassMembershipRecord.class_id == class_id)
    return session.scalar(statement)


def _owned_class(session: Session, class_id: str, professor_id: str) -> ClassRecord:
    course_class = session.get(ClassRecord, class_id)
    if course_class is None or course_class.professor_id != professor_id:
        raise ClassError("class not found")
    return course_class


def _active_owned_class(session: Session, class_id: str, professor_id: str) -> ClassRecord:
    course_class = _owned_class(session, class_id, professor_id)
    if course_class.archived_at is not None:
        raise ClassError("class is archived")
    return course_class
