import enum

from sqlalchemy import (Column, BIGINT, INTEGER, SMALLINT, VARCHAR, TEXT, TIMESTAMP, DATE, ForeignKey, BOOLEAN, func,
                        Enum)
from .base import Base


#  Creating enum types
class LivingConditionsEnum(enum.Enum):
    FLAT = "FLAT"
    HOUSE = "HOUSE"


class EducationsEnum(enum.Enum):
    SECONDARY = "SECONDARY"
    SECONDARY_SPECIAL = "SECONDARY_SPECIAL"
    BACHELOR = "BACHELOR"
    MASTER = "MASTER"


class OriginsEnum(enum.Enum):
    FAMILIAR = "FAMILIAR"
    TELEGRAM = "TELEGRAM"
    INSTAGRAM = "INSTAGRAM"
    FACEBOOK = "FACEBOOK"
    OTHER = "OTHER"


class WorkingStylesEnum(enum.Enum):
    COLLECTIVE = "COLLECTIVE"
    INDIVIDUAL = "INDIVIDUAL"


# Creating database tables
class Forms(Base):
    __tablename__ = "forms"

    form_id = Column(INTEGER, primary_key=True, autoincrement=True)
    full_name = Column(VARCHAR(255), nullable=False)
    birth_date = Column(DATE, nullable=False)
    phonenum = Column(VARCHAR(20), nullable=False)
    address = Column(VARCHAR(255), nullable=False)
    living_conditions = Column(Enum(LivingConditionsEnum), nullable=False)
    education = Column(Enum(EducationsEnum), nullable=False)
    marital_status = Column(BOOLEAN, nullable=False)
    business_trip = Column(BOOLEAN, nullable=False)
    military_service = Column(BOOLEAN, nullable=False)
    criminal_record = Column(TEXT, nullable=False)
    driver_license = Column(VARCHAR(10), nullable=False)
    personal_car = Column(VARCHAR(64), nullable=False)
    origin = Column(Enum(OriginsEnum), nullable=False)
    salary_last_job = Column(VARCHAR(255), nullable=False)
    overwork_agreement = Column(BOOLEAN, nullable=False)
    force_majeure_salary_agreement = Column(BOOLEAN, nullable=False)
    working_style = Column(Enum(WorkingStylesEnum), nullable=False)
    health = Column(VARCHAR(255), nullable=False)
    photo_id = Column(TEXT, nullable=False)
    registered_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)


class Departments(Base):
    __tablename__ = "departments"

    department_id = Column(SMALLINT, primary_key=True, autoincrement=True)
    title = Column(VARCHAR(255), nullable=False, unique=True)
    description = Column(TEXT, nullable=True)
    photo_id = Column(TEXT, nullable=True)


class FormsDepartments(Base):
    __tablename__ = "forms_departments"

    form_id = Column(INTEGER, ForeignKey("forms.form_id", ondelete="CASCADE"), primary_key=True)
    department_id = Column(SMALLINT, ForeignKey("departments.department_id", ondelete="RESTRICT"), primary_key=True)


class SelfAssessment(Base):
    __tablename__ = "self_assessment"

    assessment_id = Column(INTEGER, primary_key=True, autoincrement=True)
    form_id = Column(INTEGER, ForeignKey("forms.form_id", ondelete="CASCADE"), nullable=False)
    type = Column(VARCHAR(32), nullable=False)
    text = Column(TEXT, nullable=False)


class Universities(Base):
    __tablename__ = "universities"

    university_id = Column(INTEGER, primary_key=True, autoincrement=True)
    form_id = Column(INTEGER, ForeignKey("forms.form_id", ondelete="CASCADE"), primary_key=True, nullable=False)
    name = Column(VARCHAR(255), nullable=False)
    faculty = Column(VARCHAR(255), nullable=False)
    finished_at = Column(SMALLINT, nullable=False)


class WorkedCompanies(Base):
    __tablename__ = "worked_companies"

    company_id = Column(INTEGER, primary_key=True, autoincrement=True)
    form_id = Column(INTEGER, ForeignKey("forms.form_id", ondelete="CASCADE"), nullable=False)
    name = Column(VARCHAR(255), nullable=False)
    position = Column(VARCHAR(255), nullable=False)
    started_at = Column(DATE, nullable=False)
    finished_at = Column(DATE, nullable=True)


class Trips(Base):
    __tablename__ = "trips"

    trip_id = Column(INTEGER, primary_key=True, autoincrement=True)
    form_id = Column(INTEGER, ForeignKey("forms.form_id", ondelete="CASCADE"), nullable=False)
    country = Column(VARCHAR(255), nullable=False)
    reason = Column(VARCHAR(255), nullable=False)
    traveled_at = Column(DATE, nullable=False)


class Languages(Base):
    __tablename__ = "languages"

    language_id = Column(INTEGER, primary_key=True, autoincrement=True)
    form_id = Column(INTEGER, ForeignKey("forms.form_id", ondelete="CASCADE"), nullable=False)
    name = Column(VARCHAR(32), nullable=False)
    level = Column(SMALLINT, nullable=False)


class Applications(Base):
    __tablename__ = "applications"

    application_id = Column(INTEGER, primary_key=True, autoincrement=True)
    form_id = Column(INTEGER, ForeignKey("forms.form_id", ondelete="CASCADE"), nullable=False)
    name = Column(VARCHAR(32), nullable=False)
    level = Column(SMALLINT, nullable=False)


class Users(Base):
    __tablename__ = "users"

    telegram_id = Column(BIGINT, primary_key=True)
    username = Column(VARCHAR(255), nullable=True)
    telegram_name = Column(VARCHAR(255), nullable=False)
    form_id = Column(INTEGER, ForeignKey("forms.form_id", ondelete="SET NULL"), unique=True, nullable=True)
    is_employee = Column(BOOLEAN, server_default="FALSE")
    registered_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)


class Salaries(Base):
    __tablename__ = "salaries"

    salary_id = Column(INTEGER, primary_key=True, autoincrement=True)
    user_id = Column(BIGINT, ForeignKey("users.telegram_id", ondelete="CASCADE"), nullable=False)
    assigner_id = Column(BIGINT, ForeignKey("users.telegram_id", ondelete="SET NULL"), nullable=False)
    amount = Column(INTEGER, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    given_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)


class Fines(Base):
    __tablename__ = "fines"

    fine_id = Column(INTEGER, primary_key=True, autoincrement=True)
    user_id = Column(BIGINT, ForeignKey("users.telegram_id", ondelete="CASCADE"), nullable=False)
    assigner_id = Column(BIGINT, ForeignKey("users.telegram_id", ondelete="SET NULL"), nullable=False)
    amount = Column(INTEGER, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    given_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)


class Bonuses(Base):
    __tablename__ = "bonuses"

    bonus_id = Column(INTEGER, primary_key=True, autoincrement=True)
    user_id = Column(BIGINT, ForeignKey("users.telegram_id", ondelete="CASCADE"), nullable=False)
    assigner_id = Column(BIGINT, ForeignKey("users.telegram_id", ondelete="SET NULL"), nullable=False)
    amount = Column(INTEGER, nullable=False)
    title = Column(VARCHAR(255), nullable=False)
    description = Column(TEXT, nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)


class Tasks(Base):
    __tablename__ = "tasks"

    task_id = Column(INTEGER, primary_key=True, autoincrement=True)
    user_id = Column(BIGINT, ForeignKey("users.telegram_id", ondelete="CASCADE"), nullable=False)
    assigner_id = Column(BIGINT, ForeignKey("users.telegram_id", ondelete="SET NULL"), nullable=False)
    title = Column(VARCHAR(255), nullable=False)
    description = Column(TEXT, nullable=True)
    status = Column(VARCHAR(32), nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    finished_at = Column(TIMESTAMP, nullable=True)


class Appreciations(Base):
    __tablename__ = "appreciations"

    appreciation_id = Column(INTEGER, primary_key=True, autoincrement=True)
    user_id = Column(BIGINT, ForeignKey("users.telegram_id", ondelete="CASCADE"), nullable=False)
    sender_id = Column(BIGINT, ForeignKey("users.telegram_id", ondelete="SET NULL"), nullable=False)
    text = Column(TEXT, nullable=True)
    sent_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)


class Complaints(Base):
    __tablename__ = "complaints"

    complaint_id = Column(INTEGER, primary_key=True, autoincrement=True)
    user_id = Column(BIGINT, ForeignKey("users.telegram_id", ondelete="CASCADE"), nullable=False)
    sender_id = Column(BIGINT, ForeignKey("users.telegram_id", ondelete="SET NULL"), nullable=False)
    text = Column(TEXT, nullable=True)
    sent_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
