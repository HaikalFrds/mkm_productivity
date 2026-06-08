from sqlalchemy import Column, Integer, String
from database.session import Base


class User(Base):
    __tablename__ = "user"

    id            = Column(Integer, primary_key=True)
    nik           = Column(String(50), nullable=False, unique=True)
    username      = Column(String(100))
    name          = Column(String(200))
    role          = Column(String(50))
    password_hash = Column(String(256))

    def to_dict(self) -> dict:
        return {
            "id":   self.id,
            "nik":  self.nik,
            "name": self.name,
            "role": self.role,
        }
