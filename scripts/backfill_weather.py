"""Explicit approved ERA5 backfill; no automatic download at normal app startup."""
import argparse,asyncio,json
from datetime import date,timedelta
from pathlib import Path
from app.services.database_service import Database
from app.realtime.config import RealtimeSettings
from app.realtime.connectors.open_meteo import OpenMeteo
from app.realtime.data import WeatherHourly
from app.realtime.service import store_weather


async def main_async(args):
    settings=RealtimeSettings(weather_enabled=True)
    result=await OpenMeteo(settings).fetch(start=args.start,end=args.end)
    expected=((args.end-args.start).days+1)*24
    rows=result['rows']
    timestamps=[r['observed_at'] for r in rows]
    if len(rows)!=expected or len(set(timestamps))!=expected or any(r[k] is None for r in rows for k in ['temperature_2m','precipitation','weather_code']):
        raise SystemExit(f'Backfill incomplete ({len(rows)} / {expected} hours); nothing imported')
    if timestamps[0][:10]!=args.start.isoformat() or timestamps[-1][:10]!=args.end.isoformat():
        raise SystemExit('Backfill date range mismatch')
    db=Database('sqlite:///'+args.database.resolve().as_posix())
    try:
        WeatherHourly.__table__.create(db.engine,checkfirst=True)
        inserted=store_weather(db,result)
    finally:db.close()
    report={'source':result['source'],'synthetic':False,'expected_hours':expected,'received_hours':len(rows),'inserted_hours':inserted,
            'start':args.start.isoformat(),'end':args.end.isoformat(),'fetched_at':result['fetched_at'].isoformat(),
            'host':'archive-api.open-meteo.com','sent':'coordinates, date range and weather variable names only',
            'attribution':result['attribution'],'licence':result['licence'],
            'warning':'ERA5 reanalysis is not an archived forecast; not safe as a future-known historical covariate.'}
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report))


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--database',type=Path,required=True)
    parser.add_argument('--start',type=date.fromisoformat,default=date(2025,9,29));parser.add_argument('--end',type=date.fromisoformat,default=date(2026,9,29))
    parser.add_argument('--output',type=Path,default=Path('validation-output/realtime/weather-backfill.json'))
    args=parser.parse_args()
    if not args.database.is_file():parser.error('Provide an existing candidate database')
    asyncio.run(main_async(args))


if __name__=='__main__':main()
