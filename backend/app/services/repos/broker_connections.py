from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.orm import BrokerConnection, BrokerConnectionStatus, BrokerName


@dataclass(frozen=True)
class BrokerConnectionRepository:
    session: Session

    def get_by_name(self, broker_name: BrokerName) -> BrokerConnection | None:
        stmt = select(BrokerConnection).where(BrokerConnection.broker_name == broker_name)
        return self.session.execute(stmt).scalars().first()

    def get_or_create(self, broker_name: BrokerName) -> BrokerConnection:
        row = self.get_by_name(broker_name)
        if row is not None:
            return row
        row = BrokerConnection(
            broker_name=broker_name,
            status=BrokerConnectionStatus.DISCONNECTED,
            config_metadata={},
            encrypted_secrets={},
        )
        self.session.add(row)
        self.session.commit()
        self.session.refresh(row)
        return row

    def update(self, row: BrokerConnection) -> BrokerConnection:
        self.session.add(row)
        self.session.commit()
        self.session.refresh(row)
        return row
