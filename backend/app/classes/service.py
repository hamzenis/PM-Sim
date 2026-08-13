from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.audit.service import record_audit
from app.auth.service import AuthenticationError, hash_password
from app.db.models import (
    AuthSessionRecord,
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


@dataclass(frozen=True, slots=True)
class AvailableScenario:
    class_id: str
    class_name: str
    revision: ScenarioRevisionRecord


@dataclass(frozen=True, slots=True)
class AssignedScenario:
    """Professor-facing assignment details while retaining API identifiers."""

    id: str
    scenario_id: str
    scenario_name: str
    revision_number: int
    status: str


def import_students(
    session: Session,
    *,
    professor_id: str,
    class_id: str,
    students: list[tuple[str, str]],
) -> list[UserRecord]:
    """Create student accounts and memberships in one transaction."""
    course_class = _active_owned_class(session, class_id, professor_id)
    if not students:
        raise ClassError("at least one student is required")
    normalized = [(username.strip().lower(), password) for username, password in students]
    usernames = [username for username, _password in normalized]
    if any(not username for username in usernames):
        raise ClassError("username is required")
    if len(usernames) != len(set(usernames)):
        raise ClassError("student usernames must be unique")
    existing = session.scalars(
        select(UserRecord.username).where(UserRecord.username.in_(usernames))
    )
    if existing_username := next(iter(existing), None):
        raise ClassError(f"username already exists: {existing_username}")

    now = datetime.now(UTC)
    try:
        users = [
            UserRecord(
                username=username,
                password_hash=hash_password(password),
                role=UserRole.STUDENT,
                created_at=now,
            )
            for username, password in normalized
        ]
    except AuthenticationError as error:
        raise ClassError(str(error)) from error
    session.add_all(users)
    session.flush()
    session.add_all(
        ClassMembershipRecord(class_id=course_class.id, user_id=user.id, created_at=now)
        for user in users
    )
    record_audit(
        session,
        actor_id=professor_id,
        action="class.students_imported",
        target_type="class",
        target_id=course_class.id,
        details={"count": len(users), "usernames": usernames},
    )
    try:
        session.commit()
    except IntegrityError as error:
        session.rollback()
        raise ClassError("student import conflicts with existing data") from error
    return users


def reset_student_password(
    session: Session,
    *,
    professor_id: str,
    class_id: str,
    student_id: str,
    new_password: str,
) -> None:
    course_class = _active_owned_class(session, class_id, professor_id)
    student = session.scalar(
        select(UserRecord)
        .join(ClassMembershipRecord, ClassMembershipRecord.user_id == UserRecord.id)
        .where(
            ClassMembershipRecord.class_id == course_class.id,
            UserRecord.id == student_id,
            UserRecord.role == UserRole.STUDENT,
        )
    )
    if student is None:
        raise ClassError("student membership not found")
    try:
        student.password_hash = hash_password(new_password)
    except AuthenticationError as error:
        raise ClassError(str(error)) from error
    session.execute(delete(AuthSessionRecord).where(AuthSessionRecord.user_id == student.id))
    record_audit(
        session,
        actor_id=professor_id,
        action="student.password_reset",
        target_type="user",
        target_id=student.id,
        details={"class_id": course_class.id, "username": student.username},
    )
    session.commit()


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
    session.flush()
    record_audit(
        session,
        actor_id=professor_id,
        action="class.created",
        target_type="class",
        target_id=course_class.id,
        details={"name": course_class.name},
    )
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
    record_audit(
        session,
        actor_id=professor_id,
        action="class.renamed",
        target_type="class",
        target_id=course_class.id,
        details={"name": normalized},
    )
    session.commit()
    session.refresh(course_class)
    return course_class


def archive_class(session: Session, *, professor_id: str, class_id: str) -> ClassRecord:
    course_class = _owned_class(session, class_id, professor_id)
    if course_class.archived_at is None:
        course_class.archived_at = datetime.now(UTC)
        record_audit(
            session,
            actor_id=professor_id,
            action="class.archived",
            target_type="class",
            target_id=course_class.id,
            details={"name": course_class.name},
        )
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
    record_audit(
        session,
        actor_id=professor_id,
        action="class.student_removed",
        target_type="user",
        target_id=student_id,
        details={"class_id": course_class.id},
    )
    session.commit()


def list_assigned_scenarios(
    session: Session,
    *,
    professor_id: str,
    class_id: str,
) -> list[AssignedScenario]:
    course_class = _owned_class(session, class_id, professor_id)
    statement = (
        select(ScenarioRevisionRecord, ScenarioRecord.name)
        .join(
            ScenarioAvailabilityRecord,
            ScenarioAvailabilityRecord.scenario_revision_id == ScenarioRevisionRecord.id,
        )
        .join(ScenarioRecord, ScenarioRecord.id == ScenarioRevisionRecord.scenario_id)
        .where(ScenarioAvailabilityRecord.class_id == course_class.id)
        .order_by(ScenarioRevisionRecord.id)
    )
    return [
        AssignedScenario(
            id=revision.id,
            scenario_id=revision.scenario_id,
            scenario_name=scenario_name,
            revision_number=revision.revision_number,
            status=revision.status,
        )
        for revision, scenario_name in session.execute(statement)
    ]


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
    record_audit(
        session,
        actor_id=professor_id,
        action="class.scenario_unassigned",
        target_type="scenario_revision",
        target_id=scenario_revision_id,
        details={"class_id": course_class.id},
    )
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
    session.flush()
    record_audit(
        session,
        actor_id=professor_id,
        action="class.student_added",
        target_type="user",
        target_id=student.id,
        details={"class_id": course_class.id, "username": student.username},
    )
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
    session.flush()
    record_audit(
        session,
        actor_id=professor_id,
        action="class.scenario_assigned",
        target_type="scenario_revision",
        target_id=revision.id,
        details={"class_id": course_class.id},
    )
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


def available_scenarios_for_user(session: Session, user_id: str) -> list[AvailableScenario]:
    """List each active class assignment available to a student."""
    statement = (
        select(ScenarioRevisionRecord, ClassRecord)
        .join(
            ScenarioAvailabilityRecord,
            ScenarioAvailabilityRecord.scenario_revision_id == ScenarioRevisionRecord.id,
        )
        .join(ClassRecord, ClassRecord.id == ScenarioAvailabilityRecord.class_id)
        .join(
            ClassMembershipRecord,
            ClassMembershipRecord.class_id == ClassRecord.id,
        )
        .join(ScenarioRecord, ScenarioRecord.id == ScenarioRevisionRecord.scenario_id)
        .where(
            ClassMembershipRecord.user_id == user_id,
            ClassRecord.archived_at.is_(None),
            ScenarioRecord.archived_at.is_(None),
        )
        .order_by(ClassRecord.name, ClassRecord.id, ScenarioRevisionRecord.id)
    )
    return [
        AvailableScenario(class_id=course_class.id, class_name=course_class.name, revision=revision)
        for revision, course_class in session.execute(statement)
    ]


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
