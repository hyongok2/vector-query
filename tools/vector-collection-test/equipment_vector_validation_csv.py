"""
설비 벡터 검색 검증 스크립트 (CSV 입력 기반)
- CSV 파일에서 설비 정보와 호출명 읽기
- 각 호출명으로 벡터 검색하여 설비 ID 기준 순위 확인
- 표 형태 리포트 + CSV 파일 생성
"""

import csv
import requests
import json
from datetime import datetime
from typing import List, Dict, Optional

# ============================================================
# 설정 영역 - 실제 값으로 수정하세요
# ============================================================

# 입력 파일 경로 (.csv, .txt, .tsv 모두 가능)
INPUT_CSV_FILE = 'equipment_test_list.csv'  # 실제 파일 경로로 수정
INPUT_FILE_DELIMITER = ','  # 구분자: ',' (CSV) 또는 '\t' (TSV/탭)

# CSV 파일 컬럼명 (첫 행)
CSV_COLUMNS = {
    'equipment_id': '설비ID',       # 실제 CSV 컬럼명으로 수정
    'equipment_name': '설비명',     # 실제 CSV 컬럼명으로 수정
    'call_name_1': '설비호출1',     # 실제 CSV 컬럼명으로 수정
    'call_name_2': '설비호출2',     # 실제 CSV 컬럼명으로 수정
    'call_name_3': '설비호출3',     # 실제 CSV 컬럼명으로 수정
    'call_name_4': '설비호출4'      # 실제 CSV 컬럼명으로 수정
}

# 벡터 API 설정
VECTOR_API_CONFIG = {
    'url': 'http://17.91.220.237:5200/search',  # Vector API 엔드포인트
    'preset_id': 'ko-sbert',
    'top_k': 10,  # Top 10 결과 가져오기
    'threshold': 0.0,  # 모든 결과 가져오기
    'with_payload': True,
    'qdrant': {
        'url': 'http://17.91.220.237:6333',
        'collection': 'your_collection_name',  # 실제 컬렉션명으로 수정
        'query_filter': None  # 필요시 필터 설정
    }
}

# Qdrant payload 필드명 매핑 (대소문자 구분!)
PAYLOAD_EQUIPMENT_ID_FIELD = 'EQUIPMENTID'  # 벡터 DB에 저장된 설비 ID 필드명

# 리포트 출력 파일명
TIMESTAMP = datetime.now().strftime('%Y%m%d_%H%M%S')
REPORT_TXT_FILE = f"vector_validation_report_csv_{TIMESTAMP}.txt"
REPORT_CSV_FILE = f"vector_validation_report_csv_{TIMESTAMP}.csv"

# ============================================================
# 핵심 로직
# ============================================================

def load_equipment_from_csv() -> List[Dict]:
    """CSV 파일에서 설비 정보 로드"""
    print(f"[{datetime.now()}] CSV 파일 로드 중: {INPUT_CSV_FILE}")

    equipments = []

    try:
        with open(INPUT_CSV_FILE, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f, delimiter=INPUT_FILE_DELIMITER)

            for row in reader:
                equipment = {
                    'id': row.get(CSV_COLUMNS['equipment_id'], '').strip(),
                    'name': row.get(CSV_COLUMNS['equipment_name'], '').strip(),
                    'call_names': [
                        row.get(CSV_COLUMNS['equipment_name'], '').strip(),  # 설비명
                        row.get(CSV_COLUMNS['call_name_1'], '').strip(),
                        row.get(CSV_COLUMNS['call_name_2'], '').strip(),
                        row.get(CSV_COLUMNS['call_name_3'], '').strip(),
                        row.get(CSV_COLUMNS['call_name_4'], '').strip()
                    ]
                }

                # 빈 호출명 제거
                equipment['call_names'] = [name for name in equipment['call_names'] if name]

                if equipment['id'] and equipment['call_names']:
                    equipments.append(equipment)

        print(f"[{datetime.now()}] 총 {len(equipments)}개 설비 로드 완료")
        return equipments

    except FileNotFoundError:
        print(f"❌ 파일을 찾을 수 없습니다: {INPUT_CSV_FILE}")
        return []
    except Exception as e:
        print(f"❌ CSV 파일 로드 실패: {e}")
        return []


def vector_search(query_text: str) -> List[Dict]:
    """벡터 검색으로 Top K 결과 가져오기"""

    headers = {
        'Content-Type': 'application/json'
    }

    payload = {
        'text': query_text,
        'preset_id': VECTOR_API_CONFIG['preset_id'],
        'top_k': VECTOR_API_CONFIG['top_k'],
        'threshold': VECTOR_API_CONFIG['threshold'],
        'with_payload': VECTOR_API_CONFIG['with_payload'],
        'qdrant': VECTOR_API_CONFIG['qdrant']
    }

    try:
        response = requests.post(
            VECTOR_API_CONFIG['url'],
            headers=headers,
            json=payload,
            timeout=30
        )
        response.raise_for_status()

        result = response.json()
        return result.get('hits', [])

    except requests.exceptions.RequestException as e:
        print(f"⚠️ 벡터 검색 API 호출 실패: {e}")
        return []


def find_rank_by_id(search_results: List[Dict], target_equipment_id: str) -> Optional[int]:
    """
    검색 결과에서 해당 설비 ID가 몇 등인지 찾기

    Args:
        search_results: 벡터 검색 결과 리스트
        target_equipment_id: 찾고자 하는 설비 ID

    Returns:
        순위 (1부터 시작), 못 찾으면 None
    """
    for idx, result in enumerate(search_results, start=1):
        result_equipment_id = str(result.get('payload', {}).get(PAYLOAD_EQUIPMENT_ID_FIELD, ''))

        if result_equipment_id == target_equipment_id:
            return idx

    return None


def validate_equipments_from_csv():
    """CSV 파일 기반 전체 설비 벡터 검색 검증"""

    print("=" * 80)
    print("설비 벡터 검색 검증 시작 (CSV 기반)")
    print("=" * 80)

    # 1. CSV 파일에서 설비 정보 로드
    equipments = load_equipment_from_csv()

    if not equipments:
        print("⚠️ 로드된 설비가 없습니다.")
        return

    total_equipment_count = len(equipments)
    total_search_count = sum(len(eq['call_names']) for eq in equipments)

    # 2. 각 설비별 벡터 검색 및 순위 확인
    validation_results = []
    total_first_rank_count = 0

    print(f"\n[{datetime.now()}] 벡터 검색 검증 시작...")
    print(f"총 {total_equipment_count}개 설비, {total_search_count}회 검색 예정\n")

    for eq_idx, equipment in enumerate(equipments, start=1):
        equipment_id = equipment['id']
        equipment_name = equipment['name']
        call_names = equipment['call_names']

        print(f"[{eq_idx}/{total_equipment_count}] {equipment_name} (ID: {equipment_id})")

        # 각 호출명별 검색 결과
        search_ranks = []

        for call_idx, call_name in enumerate(call_names, start=1):
            # 벡터 검색 수행
            search_results = vector_search(call_name)

            if not search_results:
                print(f"  [{call_idx}] \"{call_name}\" → ⚠️ 검색 실패")
                search_ranks.append({
                    'call_name': call_name,
                    'rank': None,
                    'score': 0,
                    'status': 'FAIL'
                })
                continue

            # 설비 ID 기준 순위 찾기
            rank = find_rank_by_id(search_results, equipment_id)

            if rank == 1:
                status = 'OK'
                total_first_rank_count += 1
                symbol = '✅'
            elif rank is None:
                status = 'NOT_FOUND'
                symbol = '❌'
            else:
                status = 'LOW_RANK'
                symbol = '❌'

            # 유사도 점수 가져오기
            score = 0
            if rank:
                score = search_results[rank - 1].get('score', 0)

            search_ranks.append({
                'call_name': call_name,
                'rank': rank,
                'score': score,
                'status': status
            })

            rank_text = f"{rank}등" if rank else "Top10 밖"
            print(f"  [{call_idx}] \"{call_name}\" → {symbol} {rank_text} (유사도: {score:.4f})")

        # 성공률 계산
        success_count = sum(1 for r in search_ranks if r['status'] == 'OK')
        success_rate = (success_count / len(search_ranks) * 100) if search_ranks else 0

        validation_results.append({
            'equipment_id': equipment_id,
            'equipment_name': equipment_name,
            'search_ranks': search_ranks,
            'success_count': success_count,
            'success_rate': success_rate
        })

        print(f"  → 성공률: {success_count}/{len(search_ranks)} ({success_rate:.1f}%)\n")

    # 3. 리포트 생성
    print(f"[{datetime.now()}] 검증 완료!")
    export_reports(validation_results, total_equipment_count, total_search_count, total_first_rank_count)


def export_reports(validation_results: List[Dict], total_equipment_count: int,
                   total_search_count: int, total_first_rank_count: int):
    """텍스트 리포트 + CSV 리포트 생성"""

    # 통계 계산
    success_rate_overall = (total_first_rank_count / total_search_count * 100) if total_search_count > 0 else 0

    # 성공률별 설비 분류
    success_rate_distribution = {
        '100%': 0,
        '80%+': 0,
        '60%+': 0,
        '40%+': 0,
        '20%+': 0,
        '0%': 0
    }

    for result in validation_results:
        rate = result['success_rate']
        if rate == 100:
            success_rate_distribution['100%'] += 1
        elif rate >= 80:
            success_rate_distribution['80%+'] += 1
        elif rate >= 60:
            success_rate_distribution['60%+'] += 1
        elif rate >= 40:
            success_rate_distribution['40%+'] += 1
        elif rate > 0:
            success_rate_distribution['20%+'] += 1
        else:
            success_rate_distribution['0%'] += 1

    # 1. 텍스트 리포트 생성
    export_text_report(validation_results, total_equipment_count, total_search_count,
                       total_first_rank_count, success_rate_overall, success_rate_distribution)

    # 2. CSV 리포트 생성
    export_csv_report(validation_results)


def export_text_report(validation_results: List[Dict], total_equipment_count: int,
                       total_search_count: int, total_first_rank_count: int,
                       success_rate_overall: float, success_rate_distribution: Dict):
    """텍스트 형태 리포트 생성"""

    with open(REPORT_TXT_FILE, 'w', encoding='utf-8') as f:
        # 헤더
        f.write("=" * 100 + "\n")
        f.write("설비 벡터 검색 검증 리포트 (CSV 기반)\n")
        f.write(f"생성 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 100 + "\n\n")

        # 요약 통계
        f.write("[ 요약 통계 ]\n")
        f.write(f"전체 설비 수: {total_equipment_count}개\n")
        f.write(f"전체 검색 수: {total_search_count}회\n")
        f.write(f"1등 검색 성공: {total_first_rank_count}회 ({success_rate_overall:.2f}%)\n")
        f.write(f"1등 실패: {total_search_count - total_first_rank_count}회 ({100 - success_rate_overall:.2f}%)\n\n")

        # 성공률 분포
        f.write("[ 성공률 분포 ]\n")
        f.write(f"  100% 성공 (전체 1등): {success_rate_distribution['100%']}개 설비\n")
        f.write(f"  80% 이상 성공: {success_rate_distribution['80%+']}개 설비\n")
        f.write(f"  60% 이상 성공: {success_rate_distribution['60%+']}개 설비\n")
        f.write(f"  40% 이상 성공: {success_rate_distribution['40%+']}개 설비\n")
        f.write(f"  20% 이상 성공: {success_rate_distribution['20%+']}개 설비\n")
        f.write(f"  0% 성공 (전체 실패): {success_rate_distribution['0%']}개 설비\n\n")

        f.write("=" * 100 + "\n\n")

        # 표 형태 상세 리포트
        f.write("[ 설비별 검색 결과 ]\n\n")

        # 테이블 헤더
        header = f"{'설비ID':<15} | {'설비명':<30} | {'호출1':<8} | {'호출2':<8} | {'호출3':<8} | {'호출4':<8} | {'호출5':<8} | {'성공률':<8}"
        f.write(header + "\n")
        f.write("-" * len(header) + "\n")

        # 데이터 행
        for result in validation_results:
            equipment_id = result['equipment_id']
            equipment_name = result['equipment_name'][:28]  # 길이 제한
            search_ranks = result['search_ranks']
            success_rate = result['success_rate']

            # 각 호출명별 순위 표시
            rank_displays = []
            for rank_info in search_ranks[:5]:  # 최대 5개
                rank = rank_info['rank']
                status = rank_info['status']

                if status == 'OK':
                    display = f"1등 ✅"
                elif status == 'FAIL':
                    display = "실패 ⚠️"
                elif rank is None:
                    display = "Top10밖❌"
                else:
                    display = f"{rank}등 ❌"

                rank_displays.append(display)

            # 부족한 열 채우기
            while len(rank_displays) < 5:
                rank_displays.append("-")

            row = f"{equipment_id:<15} | {equipment_name:<30} | {rank_displays[0]:<8} | {rank_displays[1]:<8} | {rank_displays[2]:<8} | {rank_displays[3]:<8} | {rank_displays[4]:<8} | {success_rate:>6.1f}%"
            f.write(row + "\n")

        f.write("\n" + "=" * 100 + "\n")

    print(f"\n✅ 텍스트 리포트 생성 완료: {REPORT_TXT_FILE}")


def export_csv_report(validation_results: List[Dict]):
    """CSV 형태 리포트 생성 (Excel 분석용)"""

    with open(REPORT_CSV_FILE, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.writer(f)

        # 헤더 작성
        writer.writerow([
            '설비ID', '설비명',
            '호출1_검색어', '호출1_순위', '호출1_유사도',
            '호출2_검색어', '호출2_순위', '호출2_유사도',
            '호출3_검색어', '호출3_순위', '호출3_유사도',
            '호출4_검색어', '호출4_순위', '호출4_유사도',
            '호출5_검색어', '호출5_순위', '호출5_유사도',
            '성공횟수', '전체횟수', '성공률(%)'
        ])

        # 데이터 행 작성
        for result in validation_results:
            equipment_id = result['equipment_id']
            equipment_name = result['equipment_name']
            search_ranks = result['search_ranks']
            success_count = result['success_count']
            success_rate = result['success_rate']
            total_count = len(search_ranks)

            row = [equipment_id, equipment_name]

            # 최대 5개 호출명 정보
            for i in range(5):
                if i < len(search_ranks):
                    rank_info = search_ranks[i]
                    row.extend([
                        rank_info['call_name'],
                        rank_info['rank'] if rank_info['rank'] else 'Top10밖',
                        f"{rank_info['score']:.4f}"
                    ])
                else:
                    row.extend(['', '', ''])

            row.extend([success_count, total_count, f"{success_rate:.2f}"])

            writer.writerow(row)

    print(f"✅ CSV 리포트 생성 완료: {REPORT_CSV_FILE}")
    print(f"   → Excel에서 열어 정렬/필터링 가능")


if __name__ == "__main__":
    try:
        validate_equipments_from_csv()
    except KeyboardInterrupt:
        print("\n\n⚠️ 사용자에 의해 중단되었습니다.")
    except Exception as e:
        print(f"\n\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
