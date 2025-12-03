"""
설비 벡터 검색 검증 스크립트
- 전체 설비를 대상으로 벡터 검색 시 자기 자신이 1등인지 확인
- 1등이 아닌 설비들을 리포트로 출력
"""

import oracledb
import requests
import json
from datetime import datetime
from typing import List, Dict, Optional

# ============================================================
# 설정 영역 - 실제 값으로 수정하세요
# ============================================================

# 오라클 DB 연결 정보 (모두 실제 값으로 수정)
DB_CONFIG = {
    'host': '123.123.123.123',
    'port': 1522,
    'service_name': 'EESDB',
    'user': 'your_username',
    'password': 'your_password'
}

# 벡터 API 설정
VECTOR_API_CONFIG = {
    'url': 'http://17.91.220.237:5200/search',  # Vector API 엔드포인트
    'preset_id': 'ko-sbert', # 임베딩 모델 작성
    'top_k': 10,  # Top 10 결과 가져오기
    'threshold': 0.0,  # 모든 결과 가져오기
    'with_payload': True,
    'qdrant': {
        'url': 'http://17.91.220.237:6333',
        'collection': 'your_collection_name', # 실제 컬렉션명으로 수정
        'query_filter': None  # 필요시 필터 설정
    }
}

# 오라클 DB 컬럼명 매핑
# 주의: 오라클 쿼리 결과는 Python에서 자동으로 소문자로 변환됨
ORACLE_EQUIPMENT_ID_FIELD = 'equipmentid'  # ID 컬럼명 (반드시 소문자)
ORACLE_EQUIPMENT_NAME_FIELD = 'equipmentname_k'  # 설비명 컬럼명 (반드시 소문자)

# SQL 쿼리 - 혹시 컬럼이름이 다르면 실제 테이블명과 컬럼명으로 수정하세요. 필터링 내용도 반영 필요..(아마도 826대..)
EQUIPMENT_QUERY = """
SELECT
    EQUIPENTID,
    EQUIPMENTNAME_K
FROM EMSEQUIPMENT
WHERE 여기에 필요한 필터(총 826대가 되도록 해야 함)
"""

# 리포트 출력 파일명
REPORT_FILENAME = f"vector_validation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"

# Qdrant payload 필드명 매핑 (대소문자 구분!)
# 벡터 DB에 저장된 필드명 그대로 입력하세요. 벡터DB 필드 이름 확인 필요.
PAYLOAD_EQUIPMENT_ID_FIELD = 'EQUIPMENTID' 
PAYLOAD_EQUIPMENT_NAME_FIELD = 'EQUIPMENTNAME_K' 

# ============================================================
# 핵심 로직
# ============================================================

def get_all_equipments() -> List[Dict]:
    """오라클 DB에서 전체 설비 조회"""
    print(f"[{datetime.now()}] DB 연결 시작...")

    connection = oracledb.connect(
        host=DB_CONFIG['host'],
        port=DB_CONFIG['port'],
        service_name=DB_CONFIG['service_name'],
        user=DB_CONFIG['user'],
        password=DB_CONFIG['password']
    )

    cursor = connection.cursor()
    cursor.execute(EQUIPMENT_QUERY)

    # 컬럼명을 소문자로 가져오기
    columns = [col[0].lower() for col in cursor.description]

    equipments = []
    for row in cursor:
        equipment = dict(zip(columns, row))
        equipments.append(equipment)

    cursor.close()
    connection.close()

    print(f"[{datetime.now()}] 총 {len(equipments)}개 설비 조회 완료")
    return equipments


def vector_search(equipment_name: str) -> List[Dict]:
    """벡터 검색으로 Top K 결과 가져오기"""

    headers = {
        'Content-Type': 'application/json'
    }

    # API Key가 설정되어 있으면 헤더에 추가
    if VECTOR_API_CONFIG.get('api_key'):
        headers['X-API-Key'] = VECTOR_API_CONFIG['api_key']

    payload = {
        'text': equipment_name,
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


def find_rank(search_results: List[Dict], target_equipment_name: str) -> Optional[int]:
    """
    검색 결과에서 해당 설비명이 몇 등인지 찾기

    Args:
        search_results: 벡터 검색 결과 리스트
        target_equipment_name: 찾고자 하는 설비명

    Returns:
        순위 (1부터 시작), 못 찾으면 None
    """
    for idx, result in enumerate(search_results, start=1):
        # payload에서 설비명 필드 확인 (설정한 필드명 사용)
        result_equipment_name = result.get('payload', {}).get(PAYLOAD_EQUIPMENT_NAME_FIELD, '')

        if result_equipment_name == target_equipment_name:
            return idx

    return None


def validate_all_equipments():
    """전체 설비에 대한 벡터 검색 검증 수행"""

    print("=" * 60)
    print("설비 벡터 검색 검증 시작")
    print("=" * 60)

    # 1. 전체 설비 조회
    equipments = get_all_equipments()
    total_count = len(equipments)

    if total_count == 0:
        print("⚠️ 조회된 설비가 없습니다.")
        return

    # 2. 각 설비별 벡터 검색 및 순위 확인
    non_first_rank_items = []

    print(f"\n[{datetime.now()}] 벡터 검색 검증 시작...")

    for idx, equipment in enumerate(equipments, start=1):
        equipment_id = equipment.get(ORACLE_EQUIPMENT_ID_FIELD)
        equipment_name = equipment.get(ORACLE_EQUIPMENT_NAME_FIELD)

        print(f"[{idx}/{total_count}] 검증 중: {equipment_name} (ID: {equipment_id})", end='')

        # 벡터 검색 수행
        search_results = vector_search(equipment_name)

        if not search_results:
            print(" ⚠️ 검색 결과 없음")
            non_first_rank_items.append({
                'equipment_id': equipment_id,
                'equipment_name': equipment_name,
                'rank': None,
                'top_5': []
            })
            continue

        # 순위 찾기
        rank = find_rank(search_results, equipment_name)

        if rank == 1:
            print(" ✅ 1등")
        else:
            print(f" ❌ {rank}등" if rank else " ❌ Top10 밖")

            # Top 10 정보 추출
            top_results = []
            for i, result in enumerate(search_results[:10], start=1):
                top_results.append({
                    'rank': i,
                    'name': result.get('payload', {}).get(PAYLOAD_EQUIPMENT_NAME_FIELD, 'N/A'),
                    'score': result.get('score', 0)
                })

            non_first_rank_items.append({
                'equipment_id': equipment_id,
                'equipment_name': equipment_name,
                'rank': rank,
                'top_results': top_results
            })

    # 3. 리포트 생성
    print(f"\n[{datetime.now()}] 검증 완료!")
    export_report(non_first_rank_items, total_count)


def export_report(non_first_rank_items: List[Dict], total_count: int):
    """1등이 아닌 항목들 리포트 출력"""

    with open(REPORT_FILENAME, 'w', encoding='utf-8') as f:
        # 헤더
        f.write("=" * 80 + "\n")
        f.write("설비 벡터 검색 검증 리포트\n")
        f.write(f"생성 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 80 + "\n\n")

        # 요약
        f.write(f"전체 설비 수: {total_count}개\n")
        f.write(f"1등이 아닌 설비 수: {len(non_first_rank_items)}개\n")
        f.write(f"검증 성공률: {((total_count - len(non_first_rank_items)) / total_count * 100):.2f}%\n")
        f.write("\n" + "=" * 80 + "\n\n")

        # 상세 내역
        if non_first_rank_items:
            f.write("1등이 아닌 설비 상세 내역\n")
            f.write("-" * 80 + "\n\n")

            for idx, item in enumerate(non_first_rank_items, start=1):
                f.write(f"{idx}. 설비 ID: {item['equipment_id']}\n")
                f.write(f"   설비명: {item['equipment_name']}\n")
                f.write(f"   실제 순위: {item['rank']}등\n" if item['rank'] else "   실제 순위: Top10 밖\n")
                f.write(f"   Top 10 검색 결과:\n")

                for top_item in item['top_results']:
                    f.write(f"      {top_item['rank']}등: {top_item['name']} (유사도: {top_item['score']:.4f})\n")

                f.write("\n")
        else:
            f.write("✅ 모든 설비가 벡터 검색 시 1등으로 검색됩니다.\n")

    print(f"\n✅ 리포트 생성 완료: {REPORT_FILENAME}")
    print(f"   1등이 아닌 설비: {len(non_first_rank_items)}개")


if __name__ == "__main__":
    try:
        validate_all_equipments()
    except KeyboardInterrupt:
        print("\n\n⚠️ 사용자에 의해 중단되었습니다.")
    except Exception as e:
        print(f"\n\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
