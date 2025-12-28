#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""테스트 통계로 문서 자동 업데이트 - 주석 기반 안전한 방식

문서 규칙:
    총 테스트 수를 표현할 때는 반드시 <!-- AUTO:TEST_COUNT --> 주석을 윗줄에 포함

스크립트 책임 (극도로 제한됨):
    1. <!-- AUTO:TEST_COUNT --> 주석 검색
    2. 다음 줄만 읽음
    3. 그 줄에서 (총 N개), (N개 테스트), (N tests), collected N items, N passed 패턴 치환
    4. 주석이 없는 곳은 절대 건드리지 않음
"""
import json
import re
import sys
from pathlib import Path

# Windows 콘솔 UTF-8 출력 설정
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


def load_test_stats():
    """test_stats.json 로드"""
    stats_file = Path('test_stats.json')
    if not stats_file.exists():
        raise FileNotFoundError(
            "test_stats.json이 없습니다. 먼저 pytest --generate-stats를 실행하세요."
        )

    with stats_file.open('r', encoding='utf-8') as f:
        return json.load(f)


def generate_markdown_table(stats):
    """앱별 통계로 마크다운 테이블 동적 생성

    Returns:
        tuple: (테이블 문자열, 총 테스트 수)
    """
    # 앱 순서 정의 (표시 순서 고정)
    app_order = ['accounts', 'teams', 'members', 'schedules', 'shares', 'mindmaps']

    # 앱명 표시용 매핑
    app_display = {
        'accounts': 'Accounts',
        'teams': 'Teams',
        'members': 'Members',
        'schedules': 'Schedules',
        'shares': 'Shares',
        'mindmaps': 'Mindmaps'
    }

    # 테이블 헤더
    table_lines = [
        "| 앱 | 서비스 | API | SSR | 합계 |",
        "|---|---------|-----|-----|------|"
    ]

    # 총계 계산
    total_service = 0
    total_api = 0
    total_ssr = 0
    total = 0

    # 앱별 행 생성
    for app in app_order:
        if app not in stats:
            continue

        s = stats[app]
        service = s.get('service', 0)
        api = s.get('api', 0)
        ssr = s.get('ssr', 0)
        app_total = s.get('total', 0)

        # API가 없는 앱은 '-' 표시
        api_display = str(api) if api > 0 else '-'

        table_lines.append(
            f"| {app_display[app]} | {service} | {api_display} | {ssr} | {app_total} |"
        )

        total_service += service
        total_api += api
        total_ssr += ssr
        total += app_total

    # 총계 행
    table_lines.append(
        f"| **총계** | **{total_service}** | **{total_api}** | **{total_ssr}** | **{total}** |"
    )

    return '\n'.join(table_lines), total


def update_test_counts_with_comments(content, total_tests):
    """<!-- AUTO:TEST_COUNT --> 주석이 있는 곳만 안전하게 치환

    Args:
        content: 파일 내용
        total_tests: 총 테스트 수

    Returns:
        tuple: (업데이트된 내용, 치환 횟수)
    """
    lines = content.split('\n')
    updated_lines = []
    replacement_count = 0

    i = 0
    while i < len(lines):
        current_line = lines[i]

        # AUTO:TEST_COUNT 주석 발견
        if '<!-- AUTO:TEST_COUNT -->' in current_line:
            updated_lines.append(current_line)  # 주석 라인 유지
            i += 1

            # 다음 라인이 있으면 치환
            if i < len(lines):
                next_line = lines[i]
                original_line = next_line

                # 패턴별 치환 (순서 중요: 구체적인 패턴부터)
                # 1. (총 N개)
                next_line = re.sub(r'\(총 \d+개\)', f'(총 {total_tests}개)', next_line)
                # 2. N개 테스트
                next_line = re.sub(r'\d+개 테스트', f'{total_tests}개 테스트', next_line)
                # 3. (N tests)
                next_line = re.sub(r'\(\d+ tests\)', f'({total_tests} tests)', next_line)
                # 4. collected N items
                next_line = re.sub(r'collected \d+ items', f'collected {total_tests} items', next_line)
                # 5. N passed in
                next_line = re.sub(r'\d+ passed in', f'{total_tests} passed in', next_line)
                # 6. **N개** (테이블 총계)
                next_line = re.sub(r'\*\*\d+개\*\*', f'**{total_tests}개**', next_line)
                # 7. (N개 테스트)
                next_line = re.sub(r'\(\d+개 테스트\)', f'({total_tests}개 테스트)', next_line)
                # 8. "총 N개 테스트" (코드 블록 내)
                next_line = re.sub(r'총 \d+개 테스트', f'총 {total_tests}개 테스트', next_line)
                # 9. "왜 N개인가?" (제목)
                next_line = re.sub(r'왜 \d+개인가\?', f'왜 {total_tests}개인가?', next_line)

                if next_line != original_line:
                    replacement_count += 1

                updated_lines.append(next_line)
                i += 1
            else:
                break
        else:
            updated_lines.append(current_line)
            i += 1

    return '\n'.join(updated_lines), replacement_count


def update_markdown_file(file_path, stats, total_tests):
    """마크다운 파일 업데이트

    Args:
        file_path: 파일 경로
        stats: 테스트 통계 딕셔너리
        total_tests: 총 테스트 수

    Returns:
        int: 치환 횟수
    """
    file_path = Path(file_path)
    if not file_path.exists():
        print(f"[SKIP] {file_path} 파일이 없습니다.")
        return 0

    content = file_path.read_text(encoding='utf-8')
    original_content = content
    replacement_count = 0

    # 1. 테이블 교체 (앱 | 서비스 | API | SSR | 합계 패턴)
    table, _ = generate_markdown_table(stats)
    table_pattern = r'\| 앱 \| 서비스 \| API \| SSR \| 합계 \|.*?\| \*\*총계\*\* \|.*?\|'
    if re.search(table_pattern, content, flags=re.DOTALL):
        content = re.sub(table_pattern, table, content, flags=re.DOTALL)
        replacement_count += 1

    # 2. 주석 기반 테스트 수 치환 (안전함)
    content, count = update_test_counts_with_comments(content, total_tests)
    replacement_count += count

    # 파일 저장 (변경사항이 있을 때만)
    if content != original_content:
        file_path.write_text(content, encoding='utf-8')
        print(f"[OK] {file_path} 업데이트 완료 ({replacement_count}개 항목 변경)")
    else:
        print(f"[SKIP] {file_path} 변경사항 없음")

    return replacement_count


def update_all_docs(stats):
    """모든 문서 업데이트"""
    total_tests = sum(s['total'] for s in stats.values())

    # 업데이트할 파일 목록
    docs_root = Path('docs')
    files_to_update = [
        Path('README.md'),
        Path('CLAUDE.md'),
        docs_root / 'README.md',
        docs_root / 'guides' / 'testing_guide.md',
        docs_root / 'guides' / 'cicd_alb_deployment.md',
        docs_root / 'portfolio' / 'testing.md',
    ]

    updated_count = 0
    total_replacements = 0

    for file_path in files_to_update:
        if file_path.exists():
            count = update_markdown_file(file_path, stats, total_tests)
            if count > 0:
                updated_count += 1
                total_replacements += count

    print(f"\n🎉 총 {total_tests}개 테스트 통계로 {updated_count}개 문서 업데이트 완료!")
    print(f"📊 {total_replacements}개 항목 치환됨")
    print(f"\n💡 사용법: 테스트 수를 표시할 때는 반드시 윗줄에 <!-- AUTO:TEST_COUNT --> 주석 추가")


def main():
    """메인 실행 함수"""
    try:
        stats = load_test_stats()
        update_all_docs(stats)
    except FileNotFoundError as e:
        print(f"❌ 오류: {e}")
        print("📝 사용법: pytest --generate-stats 실행 후 이 스크립트를 실행하세요.")
        return 1
    except Exception as e:
        print(f"❌ 예상치 못한 오류: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == '__main__':
    exit(main())
