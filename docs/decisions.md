# R3–R8 기본값 확정

사용자가 남은 라운드 기본값 적용과 게이트 실행을 승인했다.

- R3: 리서치 → 설계 → 시안 → 사람 승인 → 시스템 → 전체 화면.
- R4: runs/<slug>/<stage>.json, 규칙은 harness/rules.yaml, 상태는 state.json.
- R5: 출처 수·화면 수·권한·상태·프레임·서체·색상·그림자를 검사한다. 사람 승인은 시안 뒤 1곳. 반복 실패 한도는 규칙 파일에서 읽는다.
- R6: research/design/draft/system/screens 역할은 해당 JSON만 작성한다. judge는 산출물을 고치지 않는다. 실행 상태는 runner만 기록한다.
- R7: AGENTS.md와 harness/runbook.md가 실행 절차를 정의한다.
- R8: 각 게이트 정상·실패 및 상태 전이 테스트. 실제 디자인 통과와 합성 테스트 통과는 구별한다.

## 충돌 해소

- design.md의 예시 modal/toast에는 shadow 언급이 있으나 전체 원칙과 Don't의 그림자 금지 규칙을 우선한다.
- 자료실 파일은 새 빈 파일이며 Code Connect, 기존 화면, 변수, 스타일이 없다.
- 지정 서체 Pretendard를 도구가 제공하지 않는다. 대체 서체 사용은 사용자 응답 전까지 미확정이다.
- 파일 기반 승인과 역할 지침은 협력적인 실행 규약이며 OS 수준 권한 격리는 아니다. 에이전트가 직접 파일을 수정하는 공격까지 막았다고 주장하지 않는다.
- 실제 Figma 결과는 도구 재조회와 시각 검토가 필요하다. 로컬 JSON만으로 최종 통과하지 않는다.

## 최신 변경
사용자가 Noto Sans로 변경을 승인했다. 한글 화면이므로 도구에서 제공하는 Noto Sans KR Regular/Medium/Bold를 사용한다. 기존 Pretendard 대기 조건은 해소됐다.

## 최종 구현
R7/R8 완료 시 라이브 증거 브리지를 구현했다. 과거 미구현 기록보다 docs/interview-complete.md와 harness/runbook.md의 현재 상태를 우선한다.
