# tomeido · Projects

[tomeido.github.io](https://tomeido.github.io/)에서 공개 프로젝트와 홈페이지 링크를 소개합니다.

프로젝트 카드가 `index.html`에 정적 HTML로 저장되어 있어 JavaScript나 GitHub API가 작동하지 않아도 전체 목록과 링크를 볼 수 있습니다. JavaScript는 검색·필터·정렬과 배경 효과에 사용합니다. 저장소 개수와 별점은 표시하지 않습니다.

## 프로젝트 업데이트

Python 3.9 이상에서 실행합니다. 추가 패키지나 GitHub 토큰은 필요하지 않습니다.

```bash
python3 scripts/update_projects.py
```

이 명령은 GitHub의 공개 저장소 목록을 페이지별로 가져와 `data/projects.json`에 선정된 프로젝트의 언어와 최근 변경일을 갱신합니다. 최근 push 순서로 카드를 생성하고 페이지의 갱신일을 UTC 날짜로 바꿉니다. 설명과 분류, 사이트 링크는 검토한 데이터를 유지합니다. 브라우저에서 API를 호출하거나 자동 예약 작업을 실행하지 않습니다.

프로젝트를 추가하거나 설명을 고치려면 `data/projects.json`을 편집한 뒤 위 명령을 실행합니다.

```json
{
  "name": "repository-name",
  "category": "computational",
  "description": "프로젝트를 소개하는 한국어 설명",
  "demo": "https://example.com/"
}
```

- `name`: `tomeido` 계정의 공개 원본 저장소 이름. 포크는 포함할 수 없습니다.
- `category`: `computational`, `web`, `ai`, `tools` 중 하나.
- `description`: 직접 검토한 소개 문구.
- `demo`: 선택 항목. 실제 접속과 프로젝트의 일치 여부를 확인한 HTTPS 주소만 입력합니다. GitHub의 homepage 값은 자동으로 복사하지 않습니다.

중복 이름, 누락된 저장소, 비공개·포크 저장소, 잘못된 분류·날짜·URL, API 오류 또는 HTML 구역 누락이 발견되면 `index.html`을 수정하지 않고 종료합니다. 생성되는 구역은 `<!-- PROJECTS:START -->`와 `<!-- PROJECTS:END -->` 사이입니다. 카드 내용을 직접 수정하면 다음 실행에서 덮어쓰므로 데이터 파일을 수정해 주세요.

공개 저장소 API 응답 배열을 JSON으로 저장해 두었다면 네트워크 없이도 갱신할 수 있습니다. 모든 페이지를 합친 스냅샷을 사용하세요.

```bash
python3 scripts/update_projects.py --snapshot /path/to/public-repos.json
```

실행 후 `git diff`와 로컬 화면을 확인하고 변경된 데이터, 스크립트, `index.html`을 함께 커밋합니다. GitHub Pages는 저장소에 반영된 정적 페이지를 배포합니다.

## 로컬 미리보기

```bash
python3 -m http.server 8000
```

브라우저에서 `http://localhost:8000`을 엽니다. 다른 HTML 파일로 생성 결과를 확인하려면 업데이트 명령에 `--index /path/to/index.html`을 추가합니다. 해당 파일에도 프로젝트 구역 마커와 `id="updated-date"`인 `<time>` 요소가 있어야 합니다.
