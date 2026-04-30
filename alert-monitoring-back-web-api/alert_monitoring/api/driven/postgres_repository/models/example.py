from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column, declarative_base

from alert_monitoring.api.domain.models.identification_types_enum import IdentificationTypesEnum


Base = declarative_base()


class ExampleMO(Base):
    __tablename__ = "o_examples"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(nullable=False)
    description: Mapped[str] = mapped_column(nullable=False)
    creation_time: Mapped[datetime] = mapped_column(nullable=False)
    identification_type: Mapped[IdentificationTypesEnum] = mapped_column(nullable=False)
    identification: Mapped[str] = mapped_column(nullable=False)
    number_of_days_in_week: Mapped[int] = mapped_column(nullable=False, name='days_in_week')

    class Meta:
        ordering = ('name',)
