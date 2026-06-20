from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class Client(Base):
    __tablename__ = "client"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), index=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(80), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relations v6.0
    interventions: Mapped[list["Intervention"]] = relationship(back_populates="client")
    invoices: Mapped[list["Invoice"]] = relationship(back_populates="client")
    tickets: Mapped[list["Ticket"]] = relationship(back_populates="client")


class Machine(Base):
    __tablename__ = "machine"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    bios_serial: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    machine_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    manufacturer: Mapped[str | None] = mapped_column(String(255), nullable=True)
    model: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_intervention: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Relations v6.0
    interventions: Mapped[list["Intervention"]] = relationship(back_populates="machine")


class User(Base):
    __tablename__ = "user"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    role: Mapped[str] = mapped_column(String(80), default="technicien")  # admin | technicien
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_login: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Part(Base):
    __tablename__ = "part"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    part_type: Mapped[str] = mapped_column(String(80))  # ssd, hdd, ram, cpu, gpu
    brand: Mapped[str | None] = mapped_column(String(255), nullable=True)
    model: Mapped[str | None] = mapped_column(String(255), nullable=True)
    serial_number: Mapped[str | None] = mapped_column(String(255), nullable=True)
    capacity_gb: Mapped[int | None] = mapped_column(Integer, nullable=True)
    quantity: Mapped[int] = mapped_column(Integer, default=1)
    purchase_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    notes: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Intervention(Base):
    __tablename__ = "intervention"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    client_id: Mapped[int | None] = mapped_column(ForeignKey("client.id"), nullable=True)
    machine_id: Mapped[int | None] = mapped_column(ForeignKey("machine.id"), nullable=True)
    title: Mapped[str] = mapped_column(String(255))
    machine_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    bios_serial: Mapped[str | None] = mapped_column(String(255), nullable=True)
    health_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    data_loss_risk: Mapped[str | None] = mapped_column(String(80), nullable=True)
    disk_risk: Mapped[str | None] = mapped_column(String(80), nullable=True)
    offline_windows: Mapped[str | None] = mapped_column(String(80), nullable=True)
    status: Mapped[str] = mapped_column(String(80), default="nouvelle")
    archive_path: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    report_path: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relations v6.0
    client: Mapped["Client | None"] = relationship(back_populates="interventions")
    machine: Mapped["Machine | None"] = relationship(back_populates="interventions")
    invoice: Mapped["Invoice | None"] = relationship(back_populates="intervention", uselist=False)
    tickets: Mapped[list["Ticket"]] = relationship(back_populates="intervention")


class Invoice(Base):
    __tablename__ = "invoice"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    intervention_id: Mapped[int | None] = mapped_column(ForeignKey("intervention.id"), nullable=True)
    client_id: Mapped[int | None] = mapped_column(ForeignKey("client.id"), nullable=True)
    invoice_number: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    amount: Mapped[float] = mapped_column(Float)
    tax: Mapped[float] = mapped_column(Float, default=0.0)
    total: Mapped[float] = mapped_column(Float)
    status: Mapped[str] = mapped_column(String(50), default="draft")  # draft, sent, paid, cancelled
    due_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    notes: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    intervention: Mapped["Intervention | None"] = relationship(back_populates="invoice")
    client: Mapped["Client | None"] = relationship(back_populates="invoices")


class Ticket(Base):
    __tablename__ = "ticket"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    intervention_id: Mapped[int | None] = mapped_column(ForeignKey("intervention.id"), nullable=True)
    client_id: Mapped[int | None] = mapped_column(ForeignKey("client.id"), nullable=True)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="open")  # open, in_progress, resolved, closed
    priority: Mapped[str] = mapped_column(String(50), default="medium")  # low, medium, high, critical
    time_spent_minutes: Mapped[int] = mapped_column(Integer, default=0)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    intervention: Mapped["Intervention | None"] = relationship(back_populates="tickets")
    client: Mapped["Client | None"] = relationship(back_populates="tickets")


