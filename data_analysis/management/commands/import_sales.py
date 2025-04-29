import os
import re
import math
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
from django.utils import timezone
import logging

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


def _open_sheet(xl, sheet_names, header_regex=None):
    """
    주어진 시트명 중 하나를 찾아 열고, 헤더를 찾아 DataFrame을 반환합니다.
    
    Arguments:
        xl: pandas ExcelFile 객체
        sheet_names: 시도할 시트명 목록
        header_regex: 헤더 행을 찾기 위한 정규식 패턴
        
    Returns:
        DataFrame, 사용된 시트명, skiprows 값
    """
    # 사용 가능한 시트명 가져오기
    available_sheets = xl.sheet_names
    logging.info(f"사용 가능한 시트: {available_sheets}")
    
    # 지정된 시트명 중 사용 가능한 시트 찾기
    sheet_to_use = None
    for name in sheet_names:
        if name in available_sheets:
            sheet_to_use = name
            break
    
    # 시트를 찾지 못한 경우
    if not sheet_to_use:
        # 유사한 이름의 시트 시도
        for name in sheet_names:
            for sheet in available_sheets:
                if name.lower() in sheet.lower():
                    sheet_to_use = sheet
                    break
            if sheet_to_use:
                break
        
        # 여전히 시트를 찾지 못한 경우
        if not sheet_to_use:
            raise ValueError(f"시트를 찾을 수 없음: {sheet_names}. 사용 가능한 시트: {available_sheets}")
    
    # 헤더 행을 찾기 위한 skiprows 값
    skiprows = 0
    max_skiprows = 20  # 최대 20행까지 시도
    
    if header_regex:
        # 처음부터 시작해서 헤더 찾기
        for i in range(max_skiprows):
            try:
                # 일단 i개 행을 건너뛰고 읽기
                test_df = xl.parse(sheet_to_use, skiprows=i)
                
                # 컬럼명에 헤더 패턴이 있는지 확인
                header_found = False
                for col in test_df.columns:
                    if isinstance(col, str) and re.search(header_regex, col, re.IGNORECASE):
                        header_found = True
                        break
                
                if header_found:
                    skiprows = i
                    logging.info(f"헤더 발견: skiprows={skiprows}")
                    break
            except:
                continue
    
    # 최종 데이터프레임 가져오기
    df = xl.parse(sheet_to_use, skiprows=skiprows)
    
    # 빈 행과 빈 열 제거
    df = df.dropna(how='all').dropna(axis=1, how='all')
    
    return df, sheet_to_use, skiprows


@transaction.atomic
def import_one_file(path: str, performance_id=None):
    # 0) 원본 파일 SalesData로 저장
    perf_name = extract_title_from_filename(path)
    
    # Performance ID가 제공되면 해당 ID의 Performance 사용
    if performance_id:
        try:
            perf = Performance.objects.get(id=performance_id)
            sales_rec = SalesData.objects.create(
                performance=perf,
                file=ContentFile(open(path, 'rb').read(), name=os.path.basename(path)),
                description='자동 업로드'
            )
        except Performance.DoesNotExist:
            raise ValueError(f"Performance ID {performance_id}를 찾을 수 없습니다.")
    else:
        # 기존 로직 유지
        sales_rec = store_file_and_get_salesdata(path, perf_name)
        perf = sales_rec.performance

    # 1) 엑셀 열기
    xl = pd.ExcelFile(path, engine='openpyxl')

    # 2) Sales Report → Performance (이미 performance가 지정된 경우 스킵)
    if not performance_id:
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
                # 날짜 처리
                if pd.isna(row['날짜']):
                    print(f"회차 {int(row['회차'])}: 날짜 정보 없음, 스킵")
                    continue
                
                date = pd.to_datetime(row['날짜']).date()
                
                # 시간 처리 - 텍스트 제거 및 유효성 검사
                if pd.isna(row['공연 시간']):
                    print(f"회차 {int(row['회차'])}: 시간 정보 없음, 스킵")
                    continue
                    
                time_str = str(row['공연 시간']).strip()
                
                # 유효한 시간 형식에서 숫자 추출
                import re
                time_match = re.search(r'(\d{1,2}):(\d{2})', time_str)
                if time_match:
                    hour, minute = int(time_match.group(1)), int(time_match.group(2))
                    if 0 <= hour <= 23 and 0 <= minute <= 59:
                        time = dt.time(hour, minute)
                    else:
                        print(f"회차 {int(row['회차'])}: 시간 범위 오류 ({hour}:{minute}), 스킵")
                        continue
                else:
                    print(f"회차 {int(row['회차'])}: 시간 형식 오류 ({time_str}), 스킵")
                    continue
                
                obj, _ = PerformanceSession.objects.get_or_create(
                    performance=perf,
                    session_date=date,
                    session_time=time,
                    defaults=dict(
                        round_number=int(row['회차']),
                        day_of_week=row['요일'] if pd.notna(row['요일']) else ''
                    )
                )
                mapping[int(row['회차'])] = obj
                session_objs.append(obj)
                print(f"회차 {int(row['회차'])} 파싱 성공: {date} {time}")
            except Exception as e:
                print(f"Warning: 회차 {int(row['회차']) if pd.notna(row['회차']) else '?'} 날짜/시간 파싱 실패 - {str(e)}")
                continue
            
        except Exception as e:
            print(f"Warning: 회차 처리 실패 - {str(e)}")
            continue
    
    print(f"총 {len(session_objs)}개 회차 파싱 완료")
    return mapping


def parse_session_summary_sheet(xl, perf):
    """회차별판매 시트를 파싱하여 SessionSummary 모델에 저장합니다."""
    
    try:
        # 여러 회차별 시트명 시도 및 헤더에 'R', 'S' 또는 '시간' 포함된 행 찾기
        try:
            # 헤더 정규식 패턴 확장 (다양한 형태의 헤더를 포함)
            header_regex = r'R|S|TOT|시간|공연시간|TIME|회차|No\.|NO\.|차수|일시|공연일자|CAST|객단가|매출액|예매수|점유율'
            
            df, sheet_name, skiprows = _open_sheet(
                xl, ['회차별판매', '판매상세', '회차별', '회차별 판매', '회차별 판매현황', '판매현황', '회차별현황'], 
                header_regex
            )
            print(f"회차별판매 시트: '{sheet_name}' skiprows={skiprows}")
            
            # 가끔 원하는 열이 없는 행에서 헤더를 찾는 경우가 있어서 데이터 샘플을 확인
            print("회차별판매 시트 데이터 샘플:")
            print(df.head(2).to_string(max_cols=10))
            
            # 데이터 검증 - 헤더는 찾았지만 실제 데이터 유효성 확인
            # 모든 열이 NaN인 행의 비율이 높으면 잘못된 헤더일 수 있음
            empty_rows = df.isna().all(axis=1).sum()
            if empty_rows > len(df) * 0.7:  # 70% 이상이 빈 행이면 다시 시도
                print(f"Warning: 회차별판매 시트에 빈 행이 너무 많음 ({empty_rows}/{len(df)})")
                # 다른 skiprows 값으로 다시 시도
                for alt_skip in range(skiprows+1, skiprows+5):
                    try:
                        alt_df = xl.parse(sheet_name, skiprows=alt_skip)
                        # 유효성 확인
                        alt_empty_rows = alt_df.isna().all(axis=1).sum()
                        if alt_empty_rows < len(alt_df) * 0.7:
                            df = alt_df
                            print(f"대체 skiprows={alt_skip}으로 다시 파싱 성공")
                            break
                    except Exception as e:
                        continue
        except ValueError:
            print("Warning: 회차별판매 시트를 찾을 수 없음")
            # 시트를 찾을 수 없으면 빈 SessionSummary을 생성하여 템플릿 렌더링 오류 방지
            create_placeholder_summaries(perf)
            return
            
        print("회차별판매 시트 컬럼:", df.columns.tolist())
        
        # 회차 번호 컬럼 찾기
        round_number_column = None
        round_column_candidates = ['회차', 'No.', 'NO.', 'Round', 'round', '차수', '순번', '공연회차', '공연일시']
        
        for candidate in round_column_candidates:
            if candidate in df.columns:
                round_number_column = candidate
                print(f"회차 번호 컬럼 발견: {round_number_column}")
                break
        
        # 시간 컬럼 찾기
        time_column = None
        time_column_candidates = ['시간', 'TIME', '공연시간', '공연 시간', 'time', '시작시간', '일시', '공연일시', '회차일시']
        
        for candidate in time_column_candidates:
            if candidate in df.columns:
                time_column = candidate
                print(f"시간 컬럼 발견: {time_column}")
                break
        
        # 컬럼명에 없다면 데이터프레임 내용 검색으로 시도
        if not time_column and not round_number_column:
            print("명시적인 시간/회차 컬럼을 찾을 수 없어 데이터에서 찾는 중...")
            
            # 컬럼 내용 확인
            for col in df.columns:
                if not isinstance(col, str):
                    continue
                    
                # 시간 패턴이 있는지 확인
                time_pattern_count = 0
                time_pattern_found = False
                
                for val in df[col].dropna().astype(str)[:10]:
                    if re.search(r'\d{1,2}[:시]\d{2}', val):
                        time_pattern_count += 1
                
                # 30% 이상의 행에 시간 패턴이 있으면 시간 컬럼으로 인식
                if time_pattern_count >= len(df[col].dropna()) * 0.3:
                    time_column = col
                    print(f"내용 기반으로 시간 컬럼 발견: {time_column}")
                    time_pattern_found = True
                    break
                
                # 회차 패턴(숫자)이 있는지 확인
                if not time_pattern_found and not round_number_column:
                    number_pattern_count = 0
                    
                    for val in df[col].dropna()[:10]:
                        if isinstance(val, (int, float)) or (isinstance(val, str) and val.isdigit()):
                            number_pattern_count += 1
                    
                    # 50% 이상이 숫자면 회차 번호 컬럼으로 추정
                    if number_pattern_count >= len(df[col].dropna()) * 0.5:
                        round_number_column = col
                        print(f"내용 기반으로 회차 번호 컬럼 발견: {round_number_column}")
            
        # 여전히 컬럼을 찾지 못했으면 플레이스홀더 생성
        if not time_column and not round_number_column:
            print("Warning: 시간 컬럼과 회차 번호 컬럼 모두 찾을 수 없음")
            create_placeholder_summaries(perf)
            return
        
        # 시간 컬럼 정규화
        if time_column:
            # 시간 컬럼을 'time'으로 통일
            df = df.rename(columns={time_column: 'time'})
            time_column = 'time'
        else:
            print("Warning: 시간 컬럼을 찾을 수 없음. 빈 시간 컬럼 생성")
            df['time'] = ""
            time_column = 'time'
        
        # R, S, TOT 등 열 매핑
        column_search_patterns = {
            r'^R$|^R석$': 'r_count',
            r'^S$|^S석$': 's_count', 
            r'^A$|^A석$': 's_count',  # A석도 S석으로 매핑
            r'^TOT$|^합계$|^전체$|^총계$|^총매수$': 'total_count',
            r'^금액$|^매출액$|^매출$|^REVENUE$|^수익$|^합계금액$': 'total_amount',
            r'^R[점유율]*$|^R석\s*점유율$': 'r_avg',
            r'^S[점유율]*$|^S석\s*점유율$': 's_avg',
            r'^A[점유율]*$|^A석\s*점유율$': 's_avg',  # A석 점유율도 S석으로 매핑
            r'^TOT[점유율]*$|^합계[점유율]*$|^전체[점유율]*$|^총점유율$': 'total_avg',
            r'^금액[점유율]*$|^매출액[점유율]*$|^매출[점유율]*$|^객단가$': 'amount_avg',
        }
        
        column_mappings = {}
        for col in df.columns:
            if not isinstance(col, str):
                continue
                
            for pattern, target in column_search_patterns.items():
                if re.search(pattern, col, re.IGNORECASE):
                    column_mappings[col] = target
                    print(f"컬럼 매핑: '{col}' -> '{target}'")
                    break
        
        # 실제 존재하는 컬럼만 매핑
        if column_mappings:
            df = df.rename(columns=column_mappings)
            print(f"{len(column_mappings)}개 컬럼 매핑 완료")
        else:
            print("Warning: 매핑할 컬럼을 찾지 못함")
        
        # 시간 데이터 정리
        df['time'] = df['time'].astype(str).str.strip()
        
        # 시간 데이터 정규화
        def normalize_time(time_str):
            if pd.isna(time_str) or not time_str or time_str.lower() == 'nan':
                return ''
                
            # 한글 시/분 제거, 콜론 추가
            time_str = str(time_str).strip()
            match = re.search(r'(\d{1,2})[시:]?(\d{2})?', time_str)
            if match:
                hour = int(match.group(1))
                minute = int(match.group(2) or '0')
                if 0 <= hour <= 23 and 0 <= minute <= 59:
                    return f"{hour:02d}:{minute:02d}"
            return time_str
            
        df['time'] = df['time'].apply(normalize_time)
        
        # 세션 요약 데이터 생성
        summaries = []
        for _, row in df.iterrows():
            try:
                session = None
                
                # 1. 회차 번호로 세션 찾기 (회차 번호가 있는 경우)
                if round_number_column and pd.notna(row.get(round_number_column)):
                    try:
                        # 안전하게 정수로 변환
                        round_num = _to_int(row[round_number_column])
                        if round_num > 0:  # 0이 아닌 유효한 회차 번호만 처리
                            session = PerformanceSession.objects.filter(
                                performance=perf,
                                round_number=round_num
                            ).first()
                            
                            if session:
                                print(f"회차 번호 {round_num}으로 세션 찾음: {session}")
                    except (ValueError, TypeError) as e:
                        print(f"Warning: 회차 번호 변환 실패: {str(e)}")
                
                # 2. 공연일시에서 회차 정보 추출 시도 (특수 케이스)
                if not session and round_number_column == '공연일시' and pd.notna(row.get(round_number_column)):
                    date_str = str(row[round_number_column])
                    # 일시에서 회차 번호 추출 시도 (예: "2023.04.01 1회차 15:00")
                    round_match = re.search(r'(\d+)\s*회차', date_str)
                    if round_match:
                        round_num = int(round_match.group(1))
                        session = PerformanceSession.objects.filter(
                            performance=perf,
                            round_number=round_num
                        ).first()
                        if session:
                            print(f"공연일시에서 회차 번호 {round_num} 추출 성공: {session}")
                
                # 3. 시간으로 세션 찾기 (회차 번호로 찾지 못한 경우)
                if not session and time_column:
                    time_str = row['time']
                    if time_str and time_str != 'nan':
                        # 시간 값이 실제 시간인지 확인
                        if ':' in time_str:
                            # 시간으로 세션 찾기
                            session = PerformanceSession.objects.filter(
                                performance=perf,
                                session_time__contains=time_str
                            ).first()
                            
                            if session:
                                print(f"시간 '{time_str}'으로 세션 찾음: {session}")
                
                # 세션을 찾지 못한 경우 행 건너뛰기
                if not session:
                    continue

                # 숫자 필드들을 안전하게 변환
                numeric_fields = ['r_count', 's_count', 'total_count', 'total_amount',
                                'r_avg', 's_avg', 'total_avg', 'amount_avg']
                
                summary_data = {'session': session}
                
                for field in numeric_fields:
                    if field in df.columns:
                        val = _to_int(row.get(field), None)
                        summary_data[field] = val

                summaries.append(SessionSummary(**summary_data))

            except Exception as e:
                print(f"Warning: 행 처리 실패 - {str(e)}")
                continue

        # 벌크 생성 대신 update_or_create 사용
        if summaries:
            # 이전 데이터 먼저 삭제
            try:
                existing = SessionSummary.objects.filter(session__performance=perf)
                if existing.exists():
                    print(f"Deleting {existing.count()} existing session summaries")
                    existing.delete()
            except Exception as e:
                print(f"Warning: Failed to delete existing session summaries: {str(e)}")
                
            try:
                # 다시 생성
                created = []
                for summary_obj in summaries:
                    try:
                        summary, created_flag = SessionSummary.objects.update_or_create(
                            session=summary_obj.session,
                            defaults={
                                'r_count': summary_obj.r_count,
                                's_count': summary_obj.s_count, 
                                'total_count': summary_obj.total_count,
                                'total_amount': summary_obj.total_amount,
                                'r_avg': summary_obj.r_avg,
                                's_avg': summary_obj.s_avg,
                                'total_avg': summary_obj.total_avg,
                                'amount_avg': summary_obj.amount_avg
                            }
                        )
                        if created_flag:
                            created.append(summary)
                    except Exception as detail_e:
                        print(f"Warning: Failed to save summary for session {summary_obj.session}: {str(detail_e)}")
                        
                print(f'Created/updated {len(created)} session summaries')
            except Exception as e:
                print(f"Error handling session summaries: {str(e)}")
        else:
            print("No valid session summaries to create")
            # 유효한 요약이 없으면 플레이스홀더 생성
            create_placeholder_summaries(perf)
                
    except Exception as e:
        print(f"Error in parse_session_summary_sheet: {str(e)}")
        import traceback
        print(traceback.format_exc())
        # 예외 발생 시에도 플레이스홀더 생성
        create_placeholder_summaries(perf)


def create_placeholder_summaries(perf):
    """세션별 요약 데이터가 없는 경우 빈 데이터를 생성합니다."""
    print(f"Creating placeholder summaries for performance {perf.id}")
    sessions = PerformanceSession.objects.filter(performance=perf)
    
    for session in sessions:
        SessionSummary.objects.update_or_create(
            session=session,
            defaults={
                'r_count': 0,
                's_count': 0,
                'total_count': 0,
                'total_amount': 0
            }
        )
    print(f"Created {sessions.count()} placeholder summaries")


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
    """Daily 시트를 파싱하여 DailySales 모델에 저장합니다."""
    daily_sales_count = 0
    
    # Daily 시트가 없으면 넘어감
    if 'Daily' not in xl.sheet_names and '일별 증감' not in xl.sheet_names:
        print("Daily 또는 일별 증감 시트를 찾을 수 없습니다.")
        return daily_sales_count
    
    try:
        # 사용 가능한 시트 선택
        sheet_name = 'Daily' if 'Daily' in xl.sheet_names else '일별 증감'
        print(f"{sheet_name} 시트 사용")
        
        # 첫 5행은 일반적으로 헤더이므로 건너뜀
        df = None
        
        # 여러 방식으로 파싱 시도 (헤더 위치가 다를 수 있음)
        for skip_rows in range(0, 6):
            try:
                # 인덱스 컬럼이 있는 경우와 없는 경우 모두 시도
                for index_col in [0, None]:
                    try:
                        # 시도 1: 기본 파싱
                        temp_df = xl.parse(sheet_name, skiprows=skip_rows, index_col=index_col)
                        
                        # 빈 데이터프레임 무시
                        if temp_df.empty:
                            continue
                            
                        print(f"시도: skiprows={skip_rows}, index_col={index_col}, 데이터 형태: {temp_df.shape}")
                        
                        # 데이터 샘플 출력
                        print("데이터 샘플:")
                        print(temp_df.head(2).to_string())
                        
                        # 유효한 데이터인지 확인
                        # 인덱스나 컬럼에 날짜가 있는지 확인
                        has_date = False
                        
                        # 인덱스 확인
                        if index_col is not None:
                            for idx in temp_df.index[:10]:
                                if isinstance(idx, (dt.datetime, dt.date, pd.Timestamp)) or (
                                    isinstance(idx, str) and re.search(r'(\d+)[/\-\.월](\d+)[/\-\.일]', str(idx))):
                                    has_date = True
                                    print(f"인덱스에서 날짜 형식 발견: {idx}")
                                    break
                        
                        # 컬럼 확인
                        if not has_date:
                            for col in temp_df.columns:
                                if isinstance(col, (dt.datetime, dt.date, pd.Timestamp)) or (
                                    isinstance(col, str) and re.search(r'(\d+)[/\-\.월](\d+)[/\-\.일]', str(col))):
                                    has_date = True
                                    print(f"컬럼에서 날짜 형식 발견: {col}")
                                    break
                        
                        # 최소 1개 이상의 숫자 컬럼 확인
                        has_numbers = False
                        for col in temp_df.columns:
                            # NaN이 아닌 값 중에서 숫자의 비율 확인
                            values = temp_df[col].dropna()
                            if values.empty:
                                continue
                                
                            # 문자열이면 숫자만 추출해서 확인
                            num_count = sum(1 for x in values if isinstance(x, (int, float)) or 
                                          (isinstance(x, str) and re.match(r'^[-+]?\d*\.?\d+$', re.sub(r'[,\s]', '', str(x)))))
                            
                            if num_count > 0:
                                has_numbers = True
                                print(f"숫자 데이터가 있는 컬럼 발견: {col}")
                                break
                        
                        # 날짜와 숫자가 모두 있으면 적합한 데이터프레임으로 판단
                        if has_date and has_numbers:
                            df = temp_df
                            print(f"적합한 데이터 형식 발견 (skiprows={skip_rows}, index_col={index_col})")
                            break
                    except Exception as e:
                        print(f"파싱 실패 (skiprows={skip_rows}, index_col={index_col}): {str(e)}")
                        continue
                
                # 적합한 데이터프레임을 찾았으면 루프 종료
                if df is not None:
                    break
            except Exception as e:
                print(f"전체 파싱 시도 {skip_rows} 실패: {str(e)}")
                continue
        
        # 데이터프레임 파싱 실패
        if df is None:
            print("Daily 시트 파싱 실패: 적합한 데이터 형식을 찾을 수 없음")
            
            # 마지막 시도: 표 형식이 완전히 다를 수 있음, 원시 데이터 로드
            try:
                raw_df = xl.parse(sheet_name)
                print("원시 데이터 로드, 날짜/판매 데이터 수동 식별 시도")
                
                # 데이터 확인
                print(raw_df.head(3).to_string())
                
                # 각 컬럼별로 데이터 타입 확인
                for col in raw_df.columns:
                    col_type = raw_df[col].dtype
                    non_na = raw_df[col].dropna().tolist()[:3]
                    print(f"컬럼 '{col}': 타입={col_type}, 샘플값={non_na}")
                
                # 대안 처리 방법은 향후 구현할 수 있음
                return 0
            except Exception as e:
                print(f"최종 파싱 시도 실패: {str(e)}")
                return 0
        
        # 숫자 컬럼 식별
        numeric_cols = []
        for col in df.columns:
            # 각 컬럼의 숫자 데이터 비율 확인
            values = df[col].dropna()
            if values.empty:
                continue
                
            num_count = sum(1 for x in values if isinstance(x, (int, float)) or 
                           (isinstance(x, str) and re.match(r'^[-+]?\d*\.?\d+$', re.sub(r'[,\s]', '', str(x)))))
            
            # 20% 이상이 숫자면 숫자 컬럼으로 간주
            if num_count > 0 and num_count >= len(values) * 0.2:
                numeric_cols.append(col)
                
        print(f"숫자 컬럼 {len(numeric_cols)}개 식별됨:", numeric_cols)
        
        if not numeric_cols:
            print("숫자 데이터가 포함된 컬럼을 찾을 수 없습니다.")
            return daily_sales_count
        
        # 처리 대상 행을 저장할 리스트
        valid_rows = []
        
        # 날짜 컬럼이 인덱스인 경우
        if df.index.name is not None or (df.index.dtype != 'object' and not pd.api.types.is_integer_dtype(df.index)):
            print("인덱스를 날짜 컬럼으로 사용")
            
            for idx, row in df.iterrows():
                # 인덱스 타입 확인
                idx_str = str(idx)
                
                # 요약 행 건너뛰기 (예: '2월 계', '3월 계', '합계', '주차' 등)
                if (isinstance(idx, str) and ('계' in idx or 'total' in idx.lower() or '합계' in idx or '주차' in idx)) or \
                   (isinstance(idx, str) and not any(c.isdigit() for c in idx)):
                    print(f"요약 행 '{idx}' 건너뜀")
                    continue
                
                try:
                    # 날짜 파싱
                    date_val = None
                    
                    # 1. 이미 날짜 객체인 경우
                    if isinstance(idx, (dt.datetime, dt.date, pd.Timestamp)):
                        date_val = idx.date() if hasattr(idx, 'date') else idx
                        print(f"날짜 객체 인식: {date_val}")
                    
                    # 2. 문자열 날짜 처리
                    elif isinstance(idx, str):
                        # 월/일 패턴 (예: "2월 1일", "3.15", "02-22")
                        kr_pattern = re.search(r'(\d+)[\s]*[월\./-][\s]*(\d+)[\s]*[일]?', idx)
                        if kr_pattern:
                            month, day = int(kr_pattern.group(1)), int(kr_pattern.group(2))
                            
                            # 년도 추정
                            if perf and hasattr(perf, 'start_date') and perf.start_date:
                                year = perf.start_date.year
                                
                                # 월에 따른 연도 조정
                                if month <= 2 and perf.start_date.month >= 11:
                                    year += 1
                                elif month >= 11 and hasattr(perf, 'end_date') and perf.end_date and perf.end_date.month <= 2:
                                    year -= 1
                            else:
                                year = dt.datetime.now().year
                                
                            try:
                                date_val = dt.date(year, month, day)
                                print(f"날짜 패턴 인식: {idx} -> {date_val}")
                            except ValueError as e:
                                print(f"날짜 생성 실패 ({month}/{day}): {str(e)}")
                                continue
                        else:
                            # 다른 날짜 형식 시도
                            try:
                                date_val = pd.to_datetime(idx).date()
                                print(f"문자열 날짜 변환: {idx} -> {date_val}")
                            except:
                                print(f"날짜 변환 실패: {idx}")
                                continue
                    
                    # 유효한 날짜 확인
                    if not date_val:
                        continue
                    
                    # 유효한 날짜 범위 확인 (1900-2100년)
                    if date_val.year < 1900 or date_val.year > 2100:
                        print(f"날짜가 유효 범위를 벗어남: {date_val}, 건너뜀")
                        continue
                    
                    # 행의 숫자 데이터 추출
                    row_numeric_data = {'date': date_val, 'values': []}
                    for col in numeric_cols:
                        try:
                            val = row[col]
                            
                            # NaN 건너뛰기
                            if pd.isna(val):
                                continue
                                
                            # 문자열이면 숫자 추출
                            if isinstance(val, str):
                                val = re.sub(r'[^\d.-]', '', val)
                                if not val:
                                    continue
                                try:
                                    val = float(val)
                                except:
                                    continue
                            
                            # 숫자라면 추가 (0이 아닌 값만)
                            if isinstance(val, (int, float)) and val != 0:
                                row_numeric_data['values'].append(val)
                        except Exception as e:
                            continue
                    
                    # 최소 하나의 유효 숫자가 있어야 함
                    if row_numeric_data['values']:
                        valid_rows.append(row_numeric_data)
                except Exception as e:
                    print(f"행 처리 실패 (인덱스={idx}): {str(e)}")
                    continue
        
        # 날짜 컬럼을 찾아야 하는 경우
        else:
            print("날짜 컬럼 찾기 시도")
            date_col = None
            
            # 컬럼명으로 날짜 컬럼 찾기
            for col in df.columns:
                if isinstance(col, str) and ('날짜' in col or 'date' in col.lower() or re.search(r'^\d{1,2}[/\-\.]\d{1,2}$', col)):
                    date_col = col
                    print(f"날짜 컬럼 발견: {col}")
                    break
            
            # 컬럼명으로 찾지 못한 경우 데이터 타입으로 찾기
            if not date_col:
                for col in df.columns:
                    # 해당 컬럼의 값 중 30% 이상이 날짜 형식인지 확인
                    values = df[col].dropna()
                    if values.empty:
                        continue
                    
                    date_count = 0
                    for val in values:
                        if isinstance(val, (dt.datetime, dt.date, pd.Timestamp)) or (
                            isinstance(val, str) and re.search(r'(\d+)[/\-\.월](\d+)[/\-\.일]', str(val))):
                            date_count += 1
                    
                    if date_count > 0 and date_count >= len(values) * 0.3:
                        date_col = col
                        print(f"날짜 컬럼 발견 (데이터 타입 기준): {col}")
                        break
            
            # 날짜 컬럼을 찾지 못한 경우
            if not date_col:
                print("날짜 컬럼을 찾을 수 없습니다.")
                return daily_sales_count
            
            for _, row in df.iterrows():
                try:
                    date_val = row[date_col]
                    
                    # 요약 행 건너뛰기
                    if isinstance(date_val, str) and ('계' in date_val or 'total' in date_val.lower() or '합계' in date_val):
                        continue
                    
                    # 날짜 파싱
                    parsed_date = None
                    
                    # 1. 날짜 객체인 경우
                    if isinstance(date_val, (dt.datetime, dt.date, pd.Timestamp)):
                        parsed_date = date_val.date() if hasattr(date_val, 'date') else date_val
                    
                    # 2. 문자열 날짜 처리
                    elif isinstance(date_val, str):
                        # 월/일 패턴
                        kr_pattern = re.search(r'(\d+)[\s]*[월\./-][\s]*(\d+)[\s]*[일]?', date_val)
                        if kr_pattern:
                            month, day = int(kr_pattern.group(1)), int(kr_pattern.group(2))
                            
                            # 년도 추정
                            if perf and hasattr(perf, 'start_date') and perf.start_date:
                                year = perf.start_date.year
                                
                                # 월에 따른 연도 조정
                                if month <= 2 and perf.start_date.month >= 11:
                                    year += 1
                                elif month >= 11 and hasattr(perf, 'end_date') and perf.end_date and perf.end_date.month <= 2:
                                    year -= 1
                            else:
                                year = dt.datetime.now().year
                                
                            try:
                                parsed_date = dt.date(year, month, day)
                            except ValueError:
                                continue
                        else:
                            # 다른 날짜 형식 시도
                            try:
                                parsed_date = pd.to_datetime(date_val).date()
                            except:
                                continue
                    
                    # 유효한 날짜 확인
                    if not parsed_date or parsed_date.year < 1900 or parsed_date.year > 2100:
                        continue
                    
                    # 행의 숫자 데이터 추출
                    row_numeric_data = {'date': parsed_date, 'values': []}
                    for col in numeric_cols:
                        try:
                            val = row[col]
                            
                            # NaN 건너뛰기
                            if pd.isna(val):
                                continue
                                
                            # 문자열이면 숫자 추출
                            if isinstance(val, str):
                                val = re.sub(r'[^\d.-]', '', val)
                                if not val:
                                    continue
                                try:
                                    val = float(val)
                                except:
                                    continue
                            
                            # 숫자라면 추가 (0이 아닌 값만)
                            if isinstance(val, (int, float)) and val != 0:
                                row_numeric_data['values'].append(val)
                        except Exception as e:
                            continue
                    
                    # 최소 하나의 유효 숫자가 있어야 함
                    if row_numeric_data['values']:
                        valid_rows.append(row_numeric_data)
                except Exception as e:
                    continue
        
        # 유효한 행이 없는 경우
        if not valid_rows:
            print("유효한 판매 데이터가 없습니다.")
            return daily_sales_count
        
        print(f"총 {len(valid_rows)}개의 유효한 행 발견")
        
        # 각 행 처리 및 DB 저장
        objs = []
        for row_data in valid_rows:
            date_val = row_data['date']
            values = row_data['values']
            
            # 값 분류 (양수/음수)
            positive_values = sorted([v for v in values if v > 0])
            
            # 판매량과 금액 추정
            r_count = s_count = amount = 0
            
            # 판매량: 작은 양수값 2개를 R석과 S석 판매량으로 추정
            if len(positive_values) >= 2:
                # 100 미만인 값들을 판매량으로 우선 고려
                small_vals = [v for v in positive_values if v < 100]
                if len(small_vals) >= 2:
                    r_count, s_count = int(small_vals[0]), int(small_vals[1])
                else:
                    # 작은 값 2개를 판매량으로 추정
                    r_count, s_count = int(positive_values[0]), int(positive_values[1])
            elif len(positive_values) == 1:
                r_count = int(positive_values[0])
            
            # 금액: 가장 큰 값을 매출액으로 추정
            if positive_values:
                # 10000 이상인 값을 매출액으로 우선 고려
                large_vals = [v for v in positive_values if v >= 10000]
                if large_vals:
                    amount = int(max(large_vals))
                elif positive_values:
                    # 큰 값이 없으면 가장 큰 값을 매출액으로 추정
                    amount = int(max(positive_values))
            
            # 최소한 금액이나 판매량 중 하나는 있어야 함
            if amount == 0 and r_count + s_count == 0:
                continue
                
            # PostgreSQL integer 범위 제한 (2^31-1 = 2,147,483,647)
            sold_count = min(r_count + s_count, 2147483647)
            amount = min(amount, 2147483647)
            
            print(f"일별 판매 데이터: {date_val} - 매출={amount:,}원, 판매량={sold_count}석")
            
            # 중복 생성 방지: update_or_create 사용
            daily_sales, created = DailySales.objects.update_or_create(
                performance=perf,
                date=date_val,
                defaults={
                    'sold_count_total': sold_count,
                    'revenue_total': amount,
                    'delta_count': 0,
                    'delta_revenue': 0
                }
            )
            
            if created:
                objs.append(daily_sales)
                
        daily_sales_count = len(objs)
        print(f"총 {daily_sales_count}개 일별 판매 데이터 저장/업데이트 완료")
                
    except Exception as e:
        print(f"Daily 시트 파싱 실패: {str(e)}")
        import traceback
        print(traceback.format_exc())
        
    return daily_sales_count


def _to_int(val, default=0):
    """
    다양한 입력 유형(문자열, float, NaN 등)을 안전하게 정수로 변환합니다.
    변환할 수 없는 경우 default 값을 반환합니다.
    """
    try:
        if pd.isna(val) or val is None:
            return default
            
        if isinstance(val, (int, float)):
            return int(val)
            
        if isinstance(val, str):
            # 쉼표 제거 후 정수로 변환
            cleaned = re.sub(r'[^\d.-]', '', val)
            if cleaned:
                return int(float(cleaned))
                
        return default
    except (ValueError, TypeError):
        return default


def parse_invitation_sheet(xl, sessions):
    """초대내역 시트를 파싱하여 InvitationRecord 모델에 저장합니다."""
    try:
        # 여러 시트명 시도 및 다양한 헤더 검색
        try:
            header_regex = r'회차|단체명|인원|비고|초대|인원수|초대단체|일자|행사'
            df, sheet_name, skiprows = _open_sheet(
                xl, ['초대내역', '초대', '초대 내역', '행사초대', 'INVITATION', '초대권', '초대명단'], 
                header_regex
            )
            logging.info(f"초대내역 시트: '{sheet_name}' skiprows={skiprows}")
            
            # 데이터 샘플 확인
            logging.info("초대내역 시트 데이터 샘플:")
            logging.info(df.head(2).to_string(max_cols=10))
            
            # 빈 행이 많으면 다른 skiprows로 다시 시도
            empty_rows = df.isna().all(axis=1).sum()
            if empty_rows > len(df) * 0.7:
                logging.warning(f"초대내역 시트에 빈 행이 너무 많음 ({empty_rows}/{len(df)})")
                for alt_skip in range(skiprows+1, skiprows+5):
                    try:
                        alt_df = xl.parse(sheet_name, skiprows=alt_skip)
                        alt_empty_rows = alt_df.isna().all(axis=1).sum()
                        if alt_empty_rows < len(alt_df) * 0.7:
                            df = alt_df
                            logging.info(f"대체 skiprows={alt_skip}으로 다시 파싱 성공")
                            break
                    except:
                        continue
        except ValueError:
            logging.warning("초대내역 시트를 찾을 수 없음")
            return
            
        logging.info("초대내역 시트 컬럼: %s", df.columns.tolist())
        
        # 필수 컬럼 확인
        required_columns = ['회차', '단체명', '인원']
        missing_columns = [col for col in required_columns if not any(col in str(c) for c in df.columns)]
        
        if missing_columns:
            print(f"Warning: 초대내역 시트에 필요한 컬럼 누락: {missing_columns}")
            alternative_columns = {
                '회차': ['No.', 'NO.', 'round', 'Round', '차수', '순번'],
                '단체명': ['단체', '단체 명', '기관', '기관명', '소속', '이름', '고객명'],
                '인원': ['인원수', '인원 수', '수량', '매수', '티켓수']
            }
            
            # 대체 컬럼 찾기
            column_mapping = {}
            for required, alternatives in alternative_columns.items():
                if required in missing_columns:
                    for alt in alternatives:
                        matching_columns = [c for c in df.columns if alt in str(c)]
                        if matching_columns:
                            column_mapping[matching_columns[0]] = required
                            logging.info(f"대체 컬럼 사용: '{matching_columns[0]}' -> '{required}'")
                            break
            
            # 대체 컬럼으로 DataFrame 업데이트
            if column_mapping:
                df = df.rename(columns=column_mapping)
                # 대체 후 다시 확인
                missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                logging.warning(f"필수 컬럼을 찾을 수 없어 초대내역 처리 중단: {missing_columns}")
                return
        
        # 기존 초대내역 삭제
        try:
            deleted = InvitationRecord.objects.filter(performance=perf).delete()
            logging.info(f"기존 초대내역 삭제: {deleted}")
        except Exception as e:
            logging.warning(f"기존 초대내역 삭제 실패 - {str(e)}")
        
        records_to_create = []
        
        # 데이터가 없는 경우
        if df.empty:
            logging.warning("초대내역 시트에 데이터가 없음")
            return
            
        # 각 행 처리
        for _, r in df.iterrows():
            try:
                # 1. 유효한 회차 번호 확인
                if pd.isna(r.get('회차')):
                    continue
                    
                round_num = _to_int(r['회차'])
                if round_num <= 0:
                    continue
                
                # 2. 단체명 가져오기 (없을 경우 '개인' 처리)
                group_name = str(r.get('단체명', '개인')).strip()
                if pd.isna(group_name) or group_name.lower() == 'nan':
                    group_name = '개인'
                
                # 3. 인원수 가져오기
                count = _to_int(r.get('인원', 0))
                if count <= 0:
                    logging.warning(f"유효하지 않은 인원수 {r.get('인원')}, 해당 초대내역 건너뜀")
                    continue
                
                # 4. 회차 객체 가져오기
                session = PerformanceSession.objects.filter(
                    performance=perf,
                    round_number=round_num
                ).first()
                
                if not session:
                    logging.warning(f"회차 {round_num}에 해당하는 세션을 찾을 수 없음, 해당 초대내역 건너뜀")
                    continue
                
                # 5. 레코드 생성
                records_to_create.append(
                    InvitationRecord(
                        performance=perf,
                        session=session,
                        group_name=group_name,
                        invited_count=count
                    )
                )
                
            except Exception as e:
                logging.warning(f"초대내역 행 처리 중 오류 - {str(e)}")
        
        # 벌크 생성
        if records_to_create:
            try:
                created = InvitationRecord.objects.bulk_create(records_to_create)
                logging.info(f"{len(created)}개 초대내역 레코드 생성 완료")
            except Exception as e:
                logging.error(f"Error: 초대내역 레코드 생성 실패 - {str(e)}")
        else:
            logging.warning("생성할 초대내역 레코드가 없음")
            
    except Exception as e:
        logging.error(f"Error in parse_invitation_sheet: {str(e)}")
        import traceback
        logging.error(traceback.format_exc())


def parse_open_result_sheet(xl, perf):
    """티켓오픈결과 시트를 파싱하여 TicketOpenEvent 모델에 저장합니다."""
    try:
        # 여러 시트명 시도
        try:
            header_regex = r'회차|일시|오픈일|예매오픈|티켓오픈|판매시작|예매시작|좌석수|공연일|예매처|R석|S석|예매가능석|잔여석'
            df, sheet_name, skiprows = _open_sheet(
                xl, ['티켓오픈결과', '티켓오픈', '티켓 오픈', '티켓오픈 현황', '예매오픈', '오픈결과', '오픈현황'], 
                header_regex
            )
            logging.info(f"티켓오픈결과 시트: '{sheet_name}' skiprows={skiprows}")
            
            # 데이터 샘플 확인
            logging.info("티켓오픈결과 시트 데이터 샘플:")
            logging.info(df.head(2).to_string(max_cols=10))
            
        except ValueError:
            logging.warning("티켓오픈결과 시트를 찾을 수 없음")
            return
            
        logging.info("티켓오픈결과 시트 컬럼: %s", df.columns.tolist())
        
        # 필요한 컬럼 매핑
        column_mappings = {}
        field_candidates = {
            'date': ['일시', '일자', '오픈일', '오픈일시', '티켓오픈일', '예매오픈일', '판매일'],
            'time': ['시간', '오픈시간', '티켓오픈시간', '예매오픈시간'],
            'round_number': ['회차', 'No.', 'NO.', 'Round', 'round', '차수', '공연회차'],
            'ticketing_site': ['예매처', '판매처', '예매사이트', '티켓판매처', '사이트'],
            'seat_count': ['좌석수', '총좌석', '총좌석수', '총석', '전체석'],
            'r_count': ['R석', 'R석수', 'R잔여석', 'R매진율', 'R석오픈수'], 
            's_count': ['S석', 'S석수', 'S잔여석', 'S매진율', 'S석오픈수'],
            'remaining_count': ['잔여석', '잔여좌석', '남은좌석', '예매가능석']
        }
        
        for target, candidates in field_candidates.items():
            for candidate in candidates:
                for col in df.columns:
                    if isinstance(col, str) and candidate in col:
                        column_mappings[col] = target
                        logging.info(f"티켓오픈 컬럼 매핑: '{col}' -> '{target}'")
                        break
                if target in column_mappings.values():
                    break
        
        # 필수 컬럼이 모두 있는지 확인 (최소한 date 또는 time 중 하나, round_number는 필수)
        has_date_or_time = 'date' in column_mappings.values() or 'time' in column_mappings.values()
        has_round = 'round_number' in column_mappings.values()
        
        if not has_date_or_time or not has_round:
            missing = []
            if not has_date_or_time:
                missing.append("일시/시간")
            if not has_round:
                missing.append("회차")
                
            logging.warning(f"티켓오픈결과 필수 컬럼 누락: {', '.join(missing)}")
            
            # 컬럼 추정 시도
            if not has_round:
                # 첫 번째 열이 회차일 가능성이 높음
                if len(df.columns) > 0:
                    first_col = df.columns[0]
                    if first_col not in column_mappings:
                        numeric_count = 0
                        for val in df[first_col].dropna()[:10]:
                            if isinstance(val, (int, float)) or (isinstance(val, str) and val.strip().isdigit()):
                                numeric_count += 1
                        if numeric_count >= len(df[first_col].dropna()[:10]) * 0.5:
                            column_mappings[first_col] = 'round_number'
                            has_round = True
                            logging.info(f"'round_number' 컬럼 추정: '{first_col}'")
            
            # 추정 후에도 필수 컬럼이 없으면 중단
            has_date_or_time = 'date' in column_mappings.values() or 'time' in column_mappings.values()
            has_round = 'round_number' in column_mappings.values()
            
            if not has_date_or_time or not has_round:
                logging.warning("티켓오픈결과 필수 컬럼을 찾을 수 없어 처리 중단")
                return
        
        # 데이터프레임 컬럼 이름 변경
        df = df.rename(columns={col: target for col, target in column_mappings.items()})
        
        # 필수 컬럼이 없으면 빈 컬럼 추가
        for column in ['date', 'time', 'ticketing_site', 'seat_count', 'r_count', 's_count', 'remaining_count']:
            if column not in df.columns:
                df[column] = None
                
        # 데이터 정리
        df['round_number'] = df['round_number'].apply(lambda x: _to_int(x) if pd.notna(x) else None)
        
        # 숫자 컬럼 정리
        for column in ['seat_count', 'r_count', 's_count', 'remaining_count']:
            df[column] = df[column].apply(lambda x: _to_int(x) if pd.notna(x) else 0)
        
        # 일시 처리
        def process_date_time(row):
            date_str = ''
            
            # 날짜 컬럼에서 데이터 추출
            if pd.notna(row.get('date')):
                date_val = row['date']
                if isinstance(date_val, datetime.datetime):
                    date_str = date_val.strftime('%Y-%m-%d')
                elif isinstance(date_val, str):
                    # 날짜 형식 추출 시도
                    date_match = re.search(r'(\d{2,4})[/\-년.]?(\d{1,2})[/\-월.]?(\d{1,2})', date_val)
                    if date_match:
                        year, month, day = date_match.groups()
                        # 연도가 2자리인 경우 2000년대로 추정
                        if len(year) == 2:
                            year = f"20{year}"
                        date_str = f"{year}-{int(month):02d}-{int(day):02d}"
            
            # 시간 컬럼에서 데이터 추출
            time_str = ''
            if pd.notna(row.get('time')):
                time_val = row['time']
                if isinstance(time_val, datetime.time):
                    time_str = time_val.strftime('%H:%M')
                elif isinstance(time_val, str):
                    # 시간 형식 추출 시도
                    time_match = re.search(r'(\d{1,2})[시:](\d{1,2})', time_val)
                    if time_match:
                        hour, minute = time_match.groups()
                        time_str = f"{int(hour):02d}:{int(minute):02d}"
            
            # 날짜와 시간 결합
            if date_str and time_str:
                return f"{date_str} {time_str}"
            elif date_str:
                return f"{date_str} 00:00"
            elif time_str:
                # 날짜가 없으면 공연 시작일을 사용
                if perf.start_date:
                    return f"{perf.start_date.strftime('%Y-%m-%d')} {time_str}"
                else:
                    return f"2000-01-01 {time_str}"
            else:
                return None
        
        # 일시 데이터 생성
        df['datetime'] = df.apply(process_date_time, axis=1)
        
        # 티켓오픈 이벤트 생성
        events = []
        for _, row in df.iterrows():
            try:
                # 빈 행 건너뛰기
                if pd.isna(row['round_number']) or pd.isna(row['datetime']):
                    continue
                
                # 세션 찾기
                session = None
                try:
                    session = PerformanceSession.objects.filter(
                        performance=perf,
                        round_number=row['round_number']
                    ).first()
                except Exception as session_error:
                    logging.warning(f"세션 검색 실패: {str(session_error)}")
                
                if not session:
                    logging.warning(f"회차 {row['round_number']}에 해당하는 세션을 찾을 수 없음")
                    continue
                
                # 티켓 오픈 시각 파싱
                ticket_open_time = None
                try:
                    if row['datetime']:
                        ticket_open_time = datetime.datetime.strptime(row['datetime'], '%Y-%m-%d %H:%M')
                except ValueError:
                    logging.warning(f"날짜/시간 형식 오류: {row['datetime']}")
                    continue
                
                # 티켓오픈 이벤트 생성
                events.append(TicketOpenEvent(
                    session=session,
                    ticket_open_time=ticket_open_time,
                    ticketing_site=str(row['ticketing_site']).strip() if pd.notna(row['ticketing_site']) else '',
                    seat_count=row['seat_count'],
                    r_count=row['r_count'],
                    s_count=row['s_count'],
                    remaining_count=row['remaining_count']
                ))
            except Exception as record_error:
                logging.warning(f"티켓오픈 이벤트 생성 실패: {str(record_error)}")
                continue
        
        # 기존 이벤트 삭제 후 새로 생성
        if events:
            try:
                existing = TicketOpenEvent.objects.filter(session__performance=perf)
                if existing.exists():
                    logging.info(f"{existing.count()}개 기존 티켓오픈 이벤트 삭제")
                    existing.delete()
                
                TicketOpenEvent.objects.bulk_create(events)
                logging.info(f'{len(events)}개 티켓오픈 이벤트 생성 완료')
            except Exception as bulk_error:
                logging.error(f"티켓오픈 이벤트 저장 실패: {str(bulk_error)}")
        else:
            logging.warning("티켓오픈 이벤트가 없음")
            
    except Exception as e:
        logging.error(f"티켓오픈결과 시트 처리 중 오류 발생: {str(e)}")
        import traceback
        logging.error(traceback.format_exc())


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