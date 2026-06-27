# SecuLog 뉴스레터 자동 생성 규칙

## 역할
매일 보안 뉴스 마크다운 파일을 읽어 seculog JSON 브리핑 파일을 생성한다.

## 입력 파일
- 위치: `~/knowledge/news/security_news_YYYY-MM-DD.md`
- 형식: 마크다운, 뉴스 10개 내외, 각 항목에 제목/출처/요약/URL 포함

## 출력 파일
- 위치: `data/YYYY-MM-DD.json` (이 폴더 기준)
- 반드시 **유효한 JSON**만 출력, 마크다운 코드블록 감싸기 금지

## JSON 스키마 (반드시 준수)

```json
{
  "tagline": "글로벌 정보보안 뉴스레터",
  "title": "보안 브리핑",
  "date_display": "YYYY년 M월 D일 요일",
  "date_short": "YYYY.MM.DD",
  "sources_line": "The Hacker News · BleepingComputer · SecurityWeek · Dark Reading",
  "sections": [
    {
      "label": "취약점 & 공격",
      "type": "cards",
      "items": [/* severity card 목록 */]
    },
    {
      "label": "침해 사고",
      "type": "cards",
      "items": [/* incident card 목록 */]
    },
    {
      "label": "동향 & 분석",
      "type": "trends",
      "items": [/* trend 목록 */]
    }
  ]
}
```

### card 항목 스키마
```json
{
  "severity": "critical|high|medium|incident",
  "source": "출처 사이트명",
  "headline": "한국어 제목 (핵심 정보 포함, 50자 이내)",
  "url": "원문 URL",
  "summary": "2~3문장 한국어 요약 (기술적 맥락·영향·권고 포함)"
}
```

### trend 항목 스키마
```json
{
  "lead": "동향 키워드 (굵게 표시됨)",
  "body": "2~3문장 분석 텍스트"
}
```

## 작성 규칙

### 섹션 구성
- **취약점 & 공격**: CVE, 패치, 익스플로잇 뉴스. severity 내림차순 정렬 (critical → high → medium)
- **침해 사고**: 실제 침해·데이터 유출 사건. severity는 항상 "incident"
- **동향 & 분석**: 섹션 없을 경우 생략 가능. 3~4개 인사이트 도출

### severity 기준
| 값 | 기준 |
|---|---|
| critical | CVSS 9.0+, 제로데이 악용, CISA KEV 긴급, 광범위 영향 |
| high | CVSS 7.0~8.9, 실제 악용 확인, 주요 인프라 영향 |
| medium | CVSS 4.0~6.9, 패치 권고, 제한적 영향 |
| incident | 실제 침해·데이터 유출 사건 |

### 제목 작성법
- 고유명사·CVE 번호는 원문 그대로 유지
- "— " 구분자로 핵심 위험/영향 병기 예: `포티넷 FortiGate — SSL VPN 자격증명 86,644건 유출`
- 클릭베이트 금지, 기술적 사실 중심

### 요약 작성법
- 1문장: 무슨 취약점/사건인가
- 1문장: 영향 범위 또는 공격 방식
- 1문장: 권고 조치 또는 현황

### 동향 분석
- 뉴스 항목들에서 공통 패턴·시사점을 도출
- 인덱스가 아닌 분석가 관점의 인사이트

## 날짜 표기
- 요일: 월화수목금토일
- 예: `2026년 6월 26일 금요일`
- Python: `["월","화","수","목","금","토","일"][weekday]`

## 실행 순서
1. `~/knowledge/news/security_news_YYYY-MM-DD.md` 읽기 (Read 도구)
2. 뉴스 항목 분류 및 JSON 구조 작성
3. `data/YYYY-MM-DD.json` 저장 (Write 도구)
4. 완료 메시지만 출력: `✅ data/YYYY-MM-DD.json 생성 완료 (N개 뉴스)`
