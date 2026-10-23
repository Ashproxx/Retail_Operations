import asyncio
from contextlib import asynccontextmanager
from datetime import datetime, timezone, timedelta
from sqlalchemy import select, func
from app.api.schemas import RequestContext, Role
from app.enterprise.data import Sale
from app.enterprise.retail import filters
from app.realtime.data import SalesEvent, WeatherHourly
from app.realtime.stream.ingest import Ingestor
from app.realtime.stream.simulator import events
from app.realtime.connectors.open_meteo import OpenMeteo
from app.realtime.freshness import freshness
from app.realtime.features_online import online


def store_weather(database,result):
    if not result.get('rows'):return 0
    fetched=result['fetched_at'].isoformat();source=result['source']
    with database.session() as session:
        present=set(session.scalars(select(WeatherHourly.observed_at).where(WeatherHourly.source==source,WeatherHourly.fetched_at==fetched)))
        rows=[WeatherHourly(source=source,observed_at=r['observed_at'],fetched_at=fetched,synthetic=False,payload=r) for r in result['rows'] if r['observed_at'] not in present]
        session.add_all(rows)
    return len(rows)


class Realtime:
    def __init__(self,database,settings):
        self.db=database;self.settings=settings;self.ingestor=Ingestor(database);self.weather=OpenMeteo(settings);self.task_status='idle'

    def rows(self,ctx,after=0):
        filters(ctx,{})
        query=select(SalesEvent).where(SalesEvent.id>after)
        if ctx.role!=Role.ADMIN:query=query.where(SalesEvent.store_id.in_(ctx.store_ids))
        with self.db.session() as session:
            return list(session.scalars(query.order_by(SalesEvent.id).limit(100)))

    def status(self,ctx):
        filters(ctx,{});now=datetime.now(timezone.utc)
        clauses=[] if ctx.role==Role.ADMIN else [SalesEvent.store_id.in_(ctx.store_ids)]
        with self.db.session() as session:
            latest=session.scalar(select(func.max(SalesEvent.occurred_at)).where(*clauses))
            recent=list(session.scalars(select(SalesEvent).where(*clauses,SalesEvent.occurred_at>=(now-timedelta(days=8)).isoformat())))
            weather=session.scalar(select(WeatherHourly).where(WeatherHourly.observed_at<=now.isoformat(),WeatherHourly.source=='open-meteo-forecast').order_by(WeatherHourly.fetched_at.desc(),WeatherHourly.observed_at.desc()).limit(1))
        feature_rows=[{'occurred_at':datetime.fromisoformat(r.occurred_at),'received_at':datetime.fromisoformat(r.received_at),'quantity':r.quantity} for r in recent]
        return {'mode':self.settings.stream_mode,'task_status':self.task_status,'sales':freshness(datetime.fromisoformat(latest) if latest else None,now),
                'latest_event':latest,'events_last_minute':sum(r['received_at']>=now-timedelta(minutes=1) for r in feature_rows),
                'features':online(feature_rows,now),'source_labels':sorted({r.source for r in recent}),
                'weather':{'freshness':freshness(datetime.fromisoformat(weather.fetched_at) if weather else None,now),
                           'reading_freshness':freshness(datetime.fromisoformat(weather.observed_at) if weather else None,now),
                           'values':weather.payload if weather else None,'fetch_status':self.weather.last_status,
                           'attribution':'Weather data by Open-Meteo.com','url':'https://open-meteo.com/','licence':'https://creativecommons.org/licenses/by/4.0/'}}

    async def run(self):
        settings=self.settings;ctx=RequestContext(session_id='simulator',principal_id='local-simulator',role='ADMIN')
        sequence=None
        if settings.stream_mode=='simulator':
            with self.db.session() as session:source=list(session.scalars(select(Sale.payload).order_by(Sale.txn_id)))
            if source:
                # Timestamp spacing and arrival rate scale together; provenance stays synthetic.
                start=datetime.now(timezone.utc)-timedelta(seconds=1)
                sequence=events(source,seed=settings.stream_seed,start=start,count=86400,step_seconds=1/settings.stream_speed)
        while True:
            try:
                if settings.weather_enabled:
                    result=await self.weather.fetch();store_weather(self.db,result)
                if sequence is not None:
                    event=next(sequence,None)
                    if event:self.ingestor.ingest(event,ctx)
                    else:sequence=None;self.task_status='simulator_exhausted'
                self.task_status='running'
            except (ValueError,RuntimeError):
                self.task_status='failed_iteration'
            await asyncio.sleep(1/settings.stream_speed if sequence else 60)


def install(api,settings):
    """Explicit composition hook; the showcase app is unchanged until M20 approval."""
    from app.realtime.routes import router
    api.include_router(router)
    original=api.router.lifespan_context
    @asynccontextmanager
    async def lifespan(app):
        async with original(app):
            for table in (SalesEvent.__table__,WeatherHourly.__table__):table.create(app.state.database.engine,checkfirst=True)
            service=Realtime(app.state.database,settings);app.state.realtime=service
            task=asyncio.create_task(service.run())
            try:yield
            finally:
                task.cancel()
                try:await task
                except asyncio.CancelledError:pass
    api.router.lifespan_context=lifespan
