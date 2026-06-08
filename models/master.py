from sqlalchemy import Column, Integer, String, Float, Time, ForeignKey
from sqlalchemy.orm import relationship
from database.session import Base


class Section(Base):
    __tablename__ = "section"

    id   = Column(Integer, primary_key=True)
    code = Column(String(100))
    name = Column(String(200), nullable=False)

    reports    = relationship("DailyReport", back_populates="section")
    shop_models = relationship("ShopModel",  back_populates="section", cascade="all, delete-orphan")
    work_centers = relationship("WorkCenter", back_populates="section", cascade="all, delete-orphan")

    def to_dict(self) -> dict:
        return {"id": self.id, "name": self.name}


class Shift(Base):
    __tablename__ = "shift"

    id              = Column(Integer, primary_key=True)
    name            = Column(String(100), nullable=False)
    start_time      = Column(Time)
    end_time        = Column(Time)
    total_hours     = Column(Float, default=0.0)
    preparation_min = Column(Float, default=15.0)
    other_min       = Column(Float, default=10.0)

    reports = relationship("DailyReport", back_populates="shift")

    def to_dict(self) -> dict:
        return {
            "id":              self.id,
            "name":            self.name,
            "start_time":      str(self.start_time)[:5] if self.start_time else "",
            "end_time":        str(self.end_time)[:5]   if self.end_time   else "",
            "total_hours":     float(self.total_hours     or 0),
            "preparation_min": float(self.preparation_min or 15),
            "other_min":       float(self.other_min       or 10),
        }


class ProblemGroup(Base):
    __tablename__ = "problem_group"

    id        = Column(Integer, primary_key=True)
    name      = Column(String(200))
    order_num = Column(Integer)

    categories = relationship("ProblemCategory", back_populates="group")

    def to_dict(self) -> dict:
        return {"id": self.id, "name": self.name}


class ProblemCategory(Base):
    __tablename__ = "problem_category"

    id        = Column(Integer, primary_key=True)
    group_id  = Column(Integer, ForeignKey("problem_group.id"))
    code      = Column(String(100))
    name      = Column(String(200))
    order_num = Column(Integer)

    group = relationship("ProblemGroup", back_populates="categories")

    def to_dict(self) -> dict:
        return {
            "id":         self.id,
            "group_id":   self.group_id,
            "group_name": self.group.name if self.group else "",
            "code":       self.code,
            "name":       self.name,
            "order_num":  self.order_num,
            "parent_id":  None,
        }


class ShopModel(Base):
    __tablename__ = "shop_model"

    id           = Column(Integer, primary_key=True)
    section_id   = Column(Integer, ForeignKey("section.id"), nullable=False)
    model_name   = Column(String(100), nullable=False)
    working_hour = Column(Float, default=0.0)
    cycle_time   = Column(Float, default=0.0)

    section = relationship("Section", back_populates="shop_models")

    def to_dict(self) -> dict:
        return {
            "id":           self.id,
            "model_name":   self.model_name,
            "working_hour": float(self.working_hour or 0),
            "cycle_time":   float(self.cycle_time   or 0),
        }


class WorkCenter(Base):
    __tablename__ = "work_center"

    id         = Column(Integer, primary_key=True)
    section_id = Column(Integer, ForeignKey("section.id"), nullable=False)
    name       = Column(String(100), nullable=False)

    section = relationship("Section", back_populates="work_centers")

    def to_dict(self) -> dict:
        return {"id": self.id, "name": self.name}
