import os
import re
import datetime as dt
import pandas as pd
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.db import transaction
from data_analysis.models import (
    Performance, SeatGrade, PerformanceSession, SessionSummary,
    SessionSeatGradeSales, DailySales, InvitationRecord,
    TicketOpenEvent, SalesData
)

class Command(BaseCommand):
    help = "엑셀 판매현황 파일을 DB에 적재"

    def add_arguments(self, parser):
        parser.add_argument('files', nargs='+', type=str)

    def handle(self, *args, **options):
        for path in options['files']:
            self.stdout.write(f'▶ importing {path}')
            try:
                import_one_file(path)
                self.stdout.write(self.style.SUCCESS('   done\n'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'   실패: {str(e)}\n'))


def import_one_file(path: str):
    # 0) 원본 파일 SalesData로 저장
    perf_name = extract_title_from_filename(path)
    sales_rec = store_file_and_get_salesdata(path, perf_name)

    # 1) 엑셀 열기
    xl = pd.ExcelFile(path, engine='openpyxl')

    # 2) Sales Report → Performance
    perf = parse_sales_report(xl, perf_name)

    # 3) 공연회차 시트 → PerformanceSession
    sessions = parse_sessions_sheet(xl, perf)

    # 4) 회차별판매 시트 → SessionSummary
    parse_session_summary_sheet(xl, perf)

    # 5) 판매상세 시트 → SessionSeatGradeSales
    parse_detail_sheet(xl, sessions, perf)

    # 6) Daily / 일별 증감 → DailySales
    parse_daily_sheet(xl, perf)

    # 7) 초대내역 → InvitationRecord
    parse_invitation_sheet(xl, sessions)

    # 8) 티켓오픈결과 → TicketOpenEvent
    parse_open_result_sheet(xl, perf)

    sales_rec.description = "자동 적재 완료"
    sales_rec.save()


@transaction.atomic
def parse_sales_report(xl, perf_name):
    df = xl.parse('Sales Report', header=None).dropna(how='all')
    # 기간 · 공연장 같은 키워드를 찾아 정규식으로 추출
    period = df[df[0].astype(str).str.contains('공연기간')].iloc[0,0]
    print(f"Period string: {period}")
    m = re.search(r'(\d{4})년\s*(\d{1,2})월\s*(\d{1,2})일.*?(\d{4})년\s*(\d{1,2})월\s*(\d{1,2})일', period)
    if not m:
        raise ValueError(f"Failed to extract dates from: {period}")
    print(f"Matched groups: {m.groups()}")
    start = dt.date(int(m[1]), int(m[2]), int(m[3]))
    end = dt.date(int(m[4]), int(m[5]), int(m[6]))
    venue = df[df[0].astype(str).str.contains('공연장')].iloc[0,0].split(':')[-1].strip()

    perf, _ = Performance.objects.get_or_create(
        name=perf_name,
        defaults=dict(genre='musical', venue=venue,
                     start_date=start, end_date=end)
    )
    return perf


def parse_sessions_sheet(xl, perf):
    # 첫 번째 행을 헤더로 사용
    df = xl.parse('공연회차', skiprows=3)
    session_objs, mapping = [], {}
    
    # 컬럼명 확인
    print(f"공연회차 시트 컬럼:", df.columns.tolist())
    
    for _, row in df.iterrows():
        try:
            # 회차 번호가 없거나 숫자가 아닌 경우 스킵
            if pd.isna(row['회차']) or not isinstance(row['회차'], (int, float)):
                continue
                
            # 날짜와 시간 파싱
            try:
                date = pd.to_datetime(row['날짜']).date()
                time_str = str(row['공연 시간']).strip()
                
                # 시간 형식이 올바른지 확인
                if not re.match(r'^\d{1,2}:\d{2}$', time_str):
                    continue
                    
                time = pd.to_datetime(time_str).time()
                
                obj, _ = PerformanceSession.objects.get_or_create(
                    performance=perf,
                    session_date=date,
                    session_time=time,
                    defaults=dict(
                        round_number=int(row['회차']),
                        day_of_week=row['요일']
                    )
                )
                mapping[int(row['회차'])] = obj
                session_objs.append(obj)
            except Exception as e:
                print(f"Warning: Failed to parse date/time - {str(e)}")
                continue
            
        except Exception as e:
            print(f"Warning: Failed to parse session row - {str(e)}")
            continue
    
    return mapping


def parse_session_summary_sheet(xl, perf):
    """판매상세 시트를 파싱하여 SessionSummary 모델에 저장합니다."""
    try:
        df = xl.parse('판매상세', skiprows=3)
    except Exception as e:
        print(f"Warning: Failed to parse '판매상세' sheet - {str(e)}")
        return
    
    # 컬럼명 매핑 시도
    column_mappings = {
        '요일': 'day_of_week',
        '시간': 'time',
        'R': 'r_count',
        'S': 's_count',
        'TOT': 'total_count',
        '금액': 'total_amount',
        'R.1': 'r_avg',
        'S.1': 's_avg',
        'TOT.1': 'total_avg',
        '금액.1': 'amount_avg',
    }
    
    # 실제 존재하는 컬럼만 매핑
    valid_mappings = {k: v for k, v in column_mappings.items() if k in df.columns}
    if not valid_mappings:
        print("Warning: No valid columns found in '판매상세' sheet")
        return
        
    df = df.rename(columns=valid_mappings)

    # 시간 데이터 정리
    df['time'] = df['time'].astype(str).str.strip()
    df['time'] = df['time'].apply(lambda x: x + ':00' if ':' not in x else x)
    df = df.dropna(subset=['time'])  # 빈 행 제거

    # 세션 요약 데이터 생성
    summaries = []
    for _, row in df.iterrows():
        try:
            time_str = str(row['time']).strip()
            if ':' not in time_str:
                time_str += ':00'
                
            session = PerformanceSession.objects.filter(
                performance=perf,
                session_time=time_str
            ).first()
            
            if not session:
                continue

            summary_data = {
                'session': session
            }
            
            # 숫자 필드들을 안전하게 변환
            numeric_fields = ['r_count', 's_count', 'total_count', 'total_amount',
                            'r_avg', 's_avg', 'total_avg', 'amount_avg']
            
            for field in numeric_fields:
                if field in df.columns:
                    try:
                        value = float(row[field]) if pd.notna(row[field]) else None
                        summary_data[field] = value
                    except (ValueError, TypeError):
                        summary_data[field] = None

            summaries.append(SessionSummary(**summary_data))

        except Exception as e:
            print(f"Warning: Failed to process row - {str(e)}")
            continue

    # 벌크 생성
    if summaries:
        SessionSummary.objects.bulk_create(summaries, ignore_conflicts=True)
        print(f'Created {len(summaries)} session summaries')
    else:
        print("No valid session summaries to create")


def parse_detail_sheet(xl, sessions, perf):
    df = xl.parse('판매상세', skiprows=3)
    
    # 좌석등급 컬럼(R/S/A…)을 수집
    grade_cols = []
    for col in df.columns:
        if isinstance(col, str) and len(col) <= 2:
            if col in ['R', 'S', 'A', 'B', 'C', 'D']:  # 유효한 좌석등급만 포함
                grade_cols.append(col)
    
    # SeatGrade 사전 확보
    grades = {g.name:g for g in SeatGrade.objects.filter(performance=perf)}
    for g_name in grade_cols:
        if g_name not in grades:
            grades[g_name] = SeatGrade.objects.create(performance=perf, name=g_name, price=0)

    objs = []
    for _, row in df.iterrows():
        try:
            # 회차 번호가 없거나 숫자가 아닌 경우 스킵
            if not isinstance(row.get('No.'), (int, float)) or pd.isna(row.get('No.')):
                continue
                
            ses = sessions.get(int(row['No.']))
            if not ses:
                continue
                
            for g in grade_cols:
                try:
                    sold_count = float(row.get(f'{g}_판매', 0) or 0)
                    revenue = float(row.get(f'{g}_매출', 0) or 0)
                    occupancy = float(row.get(f'{g}_점유율', 0) or 0)
                    
                    objs.append(SessionSeatGradeSales(
                        session=ses,
                        seat_grade=grades[g],
                        sold_count=int(sold_count),
                        revenue=int(revenue),
                        occupancy_rate=occupancy
                    ))
                except Exception as e:
                    print(f"Warning: Failed to process grade {g} - {str(e)}")
                    continue
                    
        except Exception as e:
            print(f"Warning: Failed to process detail row - {str(e)}")
            continue
            
    if objs:
        SessionSeatGradeSales.objects.bulk_create(objs, ignore_conflicts=True)
        print(f"Created {len(objs)} seat grade sales records")


def parse_daily_sheet(xl, perf):
    for sheet in ('Daily', '일별 증감'):
        if sheet not in xl.sheet_names:
            continue
            
        df = xl.parse(sheet, skiprows=3)
        print(f"{sheet} 시트 컬럼:", df.columns.tolist())
        
        objs = []
        for _, row in df.iterrows():
            try:
                # 날짜가 없거나 합계/소계 행은 스킵
                if pd.isna(row['Unnamed: 0']) or any(x in str(row['Unnamed: 0']) for x in ('계', 'TOTAL')):
                    continue
                    
                # R석과 S석의 판매량과 매출 합계
                sold_count = float(row.get('R', 0) or 0) + float(row.get('S', 0) or 0)
                revenue = float(row.get('금액', 0) or 0)
                
                # 증감량 계산
                delta_count = float(row.get('TOT.1', 0) or 0)
                delta_revenue = float(row.get('금액.1', 0) or 0)
                
                objs.append(DailySales(
                    performance=perf,
                    date=dt.date.today(),  # 임시로 오늘 날짜 사용
                    sold_count_total=int(sold_count),
                    revenue_total=revenue,
                    delta_count=int(delta_count),
                    delta_revenue=delta_revenue
                ))
            except Exception as e:
                print(f"Warning: Failed to parse {sheet} row - {str(e)}")
                continue
        
        if objs:
            DailySales.objects.bulk_create(objs, ignore_conflicts=True)


def parse_invitation_sheet(xl, sessions):
    if '초대내역' not in xl.sheet_names:
        return
    df = xl.parse('초대내역').dropna(subset=['회차'])
    for _, r in df.iterrows():
        ses = sessions.get(int(r['회차']))
        if not ses:
            continue
        InvitationRecord.objects.get_or_create(
            session=ses,
            seat_grade=None,
            invited_count=r['인원'],
            requester=r['요청자'],
            purpose=r['용도'],
            issued=r['발권']=='Y'
        )


def parse_open_result_sheet(xl, perf):
    if '티켓오픈결과' not in xl.sheet_names:
        return
    df = xl.parse('티켓오픈결과').dropna(subset=['OPEN'])
    objs = []
    for _, r in df.iterrows():
        objs.append(TicketOpenEvent(
            performance=perf,
            name=r['차수'],
            open_date=pd.to_datetime(r['OPEN']).date(),
            reservation_rate=r['예매율'],
            reservation_count=r['예매건수'],
            revenue_estimated=r['매출']
        ))
    TicketOpenEvent.objects.bulk_create(objs, ignore_conflicts=True)


def extract_title_from_filename(path):
    base = os.path.basename(path)
    return re.split(r'[_ ]', base, 1)[1].split('_')[0]


def store_file_and_get_salesdata(path, perf_name):
    perf, _ = Performance.objects.get_or_create(
        name=perf_name,
        defaults=dict(
            genre='musical',
            start_date=dt.date(2025, 3, 14),  # 임시 날짜
            end_date=dt.date(2025, 5, 18)     # 임시 날짜
        )
    )
    with open(path, 'rb') as f:
        sd = SalesData.objects.create(
            performance=perf,
            file=ContentFile(f.read(), name=os.path.basename(path)),
            description='자동 업로드'
        )
    return sd 