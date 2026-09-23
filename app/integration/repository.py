"""SQL-backed validated domain records; no invented business rows at startup."""
import hashlib
import json
from datetime import datetime, timezone, timedelta
from sqlalchemy import JSON, String, DateTime, select, delete
from sqlalchemy.orm import Mapped, mapped_column
from app.models.database import Base
from app.api.schemas import Role
from app.security.policy import authorize, AccessDenied
from app.core.exceptions import DataValidationError
from app.integration.registry import REGISTRY, contracts

class DomainRow(Base):
    __tablename__ = 'domain_records'
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    agent: Mapped[str] = mapped_column(String(80), index=True)
    store_id: Mapped[str] = mapped_column(String(128), index=True)
    payload: Mapped[dict] = mapped_column(JSON)

class StoreRow(Base):
    __tablename__ = 'stores'
    id: Mapped[str] = mapped_column(String(128), primary_key=True)
    name: Mapped[str] = mapped_column(String(128), unique=True)

class StateRow(Base):
    __tablename__ = 'session_state'
    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    payload: Mapped[dict] = mapped_column(JSON)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

class ReceiptRow(Base):
    __tablename__ = 'request_receipts'
    request_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    owner: Mapped[str] = mapped_column(String(64), index=True)
    feedback: Mapped[dict | None] = mapped_column(JSON, nullable=True)

class ManifestRow(Base):
    __tablename__ = 'signed_rag_manifest'
    chunk_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    signature: Mapped[str] = mapped_column(String(64))


def owner(context):
    return hashlib.sha256(json.dumps([context.principal_id, context.session_id]).encode()).hexdigest()

class Repository:
    def __init__(self, database):
        self.database = database
        Base.metadata.create_all(database.engine)

    def stores(self, context):
        with self.database.session() as session:
            query = select(StoreRow)
            if context.role != Role.ADMIN:
                query = query.where(StoreRow.id.in_(context.store_ids))
            return {r.id:r.name for r in session.scalars(query)}

    def add_records(self, agent, records, *, store_names=None):
        model, _, _ = contracts(agent)
        rows = [model.model_validate(r).model_dump(mode='json') for r in records]
        prepared = []
        for r in rows:
            key = [agent]+[r[k] for k in REGISTRY[agent].key_fields]
            identity = hashlib.sha256(json.dumps(key).encode()).hexdigest()
            prepared.append(DomainRow(id=identity,agent=agent,store_id=r['store_id'],payload=r))
        if len({r.id for r in prepared}) != len(prepared):
            raise DataValidationError('Duplicate record identities')
        with self.database.session() as session:
            for row in prepared:
                if session.get(DomainRow,row.id):
                    raise DataValidationError('Existing observations are immutable; provide a new date/version')
                session.add(row)
                if not session.get(StoreRow,row.store_id):
                    session.add(StoreRow(id=row.store_id,name=(store_names or {}).get(row.store_id,row.store_id)))
                    session.flush()
        return len(rows)

    def records(self, agent, context, store_id=None):
        action = REGISTRY[agent].action
        if context.role == Role.ADMIN or store_id is not None:
            authorize(context,action,store_id)
        else:
            if not context.store_ids: raise AccessDenied('No authorized stores')
            for sid in context.store_ids: authorize(context,action,sid)
        with self.database.session() as session:
            query = select(DomainRow).where(DomainRow.agent==agent)
            if store_id is not None: query=query.where(DomainRow.store_id==store_id)
            elif context.role != Role.ADMIN: query=query.where(DomainRow.store_id.in_(context.store_ids))
            return [r.payload for r in session.scalars(query)]

    def memory(self, context):
        with self.database.session() as session:
            row=session.get(StateRow,owner(context))
            if not row: return None
            if row.updated_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc)-timedelta(hours=24):
                session.delete(row)
                return None
            return row.payload

    def remember(self, context, payload):
        with self.database.session() as session:
            session.execute(delete(StateRow).where(StateRow.updated_at < datetime.now(timezone.utc)-timedelta(hours=24)))
            session.merge(StateRow(key=owner(context),payload=payload,updated_at=datetime.now(timezone.utc)))

    def receipt(self, context):
        with self.database.session() as session:
            session.add(ReceiptRow(request_id=str(context.request_id),owner=owner(context),feedback=None))

    def feedback(self, context, request):
        with self.database.session() as session:
            row=session.get(ReceiptRow,str(request.request_id))
            if row is None or row.owner != owner(context): raise AccessDenied('Unknown request')
            row.feedback={'rating':request.rating,'comment':request.comment}
