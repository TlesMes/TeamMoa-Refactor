# TeamMoa

**TeamMoa**는 팀 단위 협업을 위한 Django 기반 웹 애플리케이션입니다. 팀 생성, 팀원 관리, 마인드맵, 일정, 게시판 등 다양한 협업 기능을 제공합니다.

## 주요 기능

- **팀 관리**
  - 팀 생성, 팀원 초대/관리, 팀 정보 수정, 팀 해산
  - 팀 초대코드 복사 및 팀 검색 기능

- **마인드맵**
  - 팀별 마인드맵 생성 및 노드 추가/수정/상세조회
  - 마인드맵 내 댓글 기능

- **게시판(공유)**
  - 팀별 게시글 작성, 수정, 삭제, 파일 첨부 및 다운로드
  - 게시글 검색 및 페이징

- **일정 관리**
  - 팀별 일정(개발 단계) 추가, 수정, 삭제

- **회원/계정 관리**
  - 회원가입, 로그인, 비밀번호 변경, 프로필 수정
  - 이메일 인증 및 사용자 권한 관리

## 폴더 구조

- `accounts/` : 사용자 인증 및 계정 관리
- `teams/` : 팀 관련 기능
- `members/` : 팀원 및 할 일 관리
- `mindmaps/` : 마인드맵 기능
- `schedules/` : 일정 관리
- `shares/` : 팀별 게시판(공지사항, 파일 공유)
- `static/` : 정적 파일(CSS, JS, 이미지 등)
- `templates/` : 공통 템플릿

## 설치 및 실행

1. 패키지 설치
    ```sh
    pip install -r requirements.txt
    ```

2. 마이그레이션 적용
    ```sh
    python manage.py migrate
    ```

3. 개발 서버 실행
    ```sh
    python manage.py runserver
    ```

4. (선택) 관리자 계정 생성
    ```sh
    python manage.py createsuperuser
    ```

## 환경 변수

`.env` 파일에 이메일 인증 등 필요한 환경 변수를 설정해야 합니다.
- `EMAIL_HOST_USER`
- `EMAIL_HOST_PASSWORD`
- 기타 Django SECRET_KEY 등

## TODO

자세한 내용은 [TODO](https://www.notion.so/TeamMoa-TODO-2465f76345eb804dbb01f9f5b8dc972d?source=copy_link)를 참고하세요.

---

**TeamMoa**는 팀 협업의 효율성을 높이기 위해 다양한 기능을 통합 제공하는 플랫폼입니다.