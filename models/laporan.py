from sqlalchemy import (
    Column, Integer, String, Float, Boolean, Date, Time, Text, ForeignKey,
)
from sqlalchemy.orm import relationship
from database.session import Base


class DailyReport(Base):
    __tablename__ = "daily_report"

    id           = Column(Integer, primary_key=True)
    user_id      = Column(Integer, ForeignKey("user.id"))
    shift_id     = Column(Integer, ForeignKey("shift.id"))
    section_id   = Column(Integer, ForeignKey("section.id"))
    date         = Column(Date,    nullable=False)
    coordinator  = Column(String(200))
    approved_by  = Column(String(200))
    checked_by   = Column(String(200))
    status       = Column(String(50), default="draft")

    section     = relationship("Section", back_populates="reports")
    shift       = relationship("Shift",   back_populates="reports")
    productions = relationship("DailyProduction", back_populates="report", cascade="all, delete-orphan")
    problems    = relationship("ProblemRecord",    back_populates="report", cascade="all, delete-orphan")
    manpower    = relationship("Manpower",         back_populates="report", cascade="all, delete-orphan")
    absen       = relationship("Absen",            back_populates="report", cascade="all, delete-orphan")
    inhouse     = relationship("InhouseClaim",     back_populates="report", cascade="all, delete-orphan")


class DailyProduction(Base):
    __tablename__ = "daily_production"

    id           = Column(Integer, primary_key=True)
    report_id    = Column(Integer, ForeignKey("daily_report.id"), nullable=False)
    model        = Column(String(100))
    plan_unit    = Column(Float, default=0)
    actual_unit  = Column(Float, default=0)
    plan_whour   = Column(Float, default=0)
    actual_whour = Column(Float, default=0)
    ot_2h        = Column(Boolean, default=False)
    ot_3h        = Column(Boolean, default=False)
    ot_11h       = Column(Boolean, default=False)

    report = relationship("DailyReport", back_populates="productions")


class ProblemRecord(Base):
    __tablename__ = "problem_record"

    id                = Column(Integer, primary_key=True)
    report_id         = Column(Integer, ForeignKey("daily_report.id"), nullable=False)
    category_id       = Column(Integer, ForeignKey("problem_category.id"), nullable=True)
    ra_number         = Column(String(100))
    description       = Column(Text)
    cause             = Column(Text)
    corrective_action = Column(Text)
    pic               = Column(String(200))
    start_time        = Column(Time)
    end_time          = Column(Time)
    down_time         = Column(Float, default=0.0)
    loss_time         = Column(Float, default=0.0)
    date              = Column(Date)

    report   = relationship("DailyReport",    back_populates="problems")
    category = relationship("ProblemCategory")


class Manpower(Base):
    __tablename__ = "manpower"

    id          = Column(Integer, primary_key=True)
    report_id   = Column(Integer, ForeignKey("daily_report.id"), nullable=False)
    role        = Column(String(200))
    plan_count  = Column(Integer, default=0)
    act_count   = Column(Integer, default=0)

    report = relationship("DailyReport", back_populates="manpower")


class Absen(Base):
    __tablename__ = "absen"

    id         = Column(Integer, primary_key=True)
    report_id  = Column(Integer, ForeignKey("daily_report.id"), nullable=False)
    no         = Column(Integer)
    nama       = Column(String(200))
    nik        = Column(String(50))
    shop       = Column(String(100))
    keterangan = Column(String(200))

    report = relationship("DailyReport", back_populates="absen")


class InhouseClaim(Base):
    __tablename__ = "inhouse_claim"

    id        = Column(Integer, primary_key=True)
    report_id = Column(Integer, ForeignKey("daily_report.id"), nullable=False)
    tanggal   = Column(Date)
    model     = Column(String(100))
    op_no_st  = Column(String(100))
    item      = Column(String(200))
    qty       = Column(Float, default=0)
    satuan    = Column(String(50))
    penyebab  = Column(Text)
    tindakan  = Column(Text)
    faktor    = Column(String(200))
    stop_hr   = Column(Float, default=0)
    lost_hr   = Column(Float, default=0)
    status    = Column(String(100))

    report = relationship("DailyReport", back_populates="inhouse")


