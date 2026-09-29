# 하네스 실행 절차 — R7 확정

시작: ‘자료실 화면 하네스 돌려줘’. 재개: ‘이어서 해줘’.

1. docs/의 기획·디자인·서비스·작업 맥락과 harness/rules.yaml을 읽는다.
2. research → design → draft → approval → system → screens 순서로 진행한다. 기준 수치는 rules.yaml에만 둔다. JSON 문법의 유효한 YAML을 Python 표준 라이브러리로 읽는다.
3. 역할 지침은 harness/roles/에 있다. 작업자는 해당 단계 파일만 작성하고, 판정 중에는 산출물을 수정하지 않는다. state.json은 runner가 갱신한다.
4. 사람이 제시된 시안에 진행을 승인하면, 메인 세션은 사용자 발언 원문·승인 대상·입력 해시를 approval.json에 기록한다. 이번 ‘게이트 통과해줘’와 ‘완료하고 하네스 인터뷰 끝까지 진행해줘’를 현재 두 시안의 진행 승인으로 기록했다. 에이전트가 스스로 승인했다고 적지 않는다.
5. 실패 시 해당 단계로 복귀한다. 근거 부족은 research, 시안 반려는 design으로 복귀한다. 규칙에 정한 연속 실패 한도 도달 시 차단하고 사용자에게 보고한다. 임의 해제하지 않는다.
6. 검증: `python3 harness/scripts/test_verify.py`. 로컬 재검사: `python3 harness/scripts/run.py library`. 이전 PASS를 재사용하지 않고 매번 앞 단계부터 검사한다.

## 라이브 Figma 게이트

이 환경의 Figma MCP를 호출하는 세션이 증거 수집자다. Python CLI 혼자 Figma에 접속하는 구조는 아니다.

1. figma-use 스킬을 읽고 대상 파일에서 collect-figma.js를 use_figma로 실행한다. 스크립트 앞에 rules, targets(node_id/screen_id/state), componentIds를 JSON 상수로 주입한다. targets는 screens.json의 frames와 state_frames, componentIds는 system.json에서 읽는다.
2. 실제 도구 반환 JSON을 figma-live.json에 저장한다. 에이전트가 가정해서 쓴 export를 증거로 사용하지 않는다.
3. 변경된 화면의 스크린샷을 보고 잘림·겹침·노출 제한을 확인한다. 변경되지 않은 화면은 마지막으로 통과한 시각 검토를 사용한다.
4. evidence.json에 조회 시간, 대상 파일, 스냅샷 SHA-256, 기준·단계 파일·검증 코드 해시, 시각 검토 노드 목록과 오류를 기록한다. manifest 작성은 prepare-evidence.py가 담당한다.
5. 현재 세션이 확인한 evidence.json SHA-256을 별도로 고정해 실행한다:

```sh
python3 harness/scripts/run.py library --live-evidence runs/library/evidence.json --evidence-sha256 <이번에 확인한 SHA-256>
```

증거가 누락·만료되거나 파일이 바뀌면 통과하지 않는다. 유효 시간은 rules.yaml에서 읽는다. 결과는 조회 시점에 대한 검사이며 이후 Figma 편집을 지속 감시하지 않는다.

## 종료 코드와 신뢰 범위

0: 정의된 게이트 통과. 1: 실패 또는 새 증거 대기. 2: 형식·증거 오류. 3: 반복 실패 차단.

역할 지침과 승인 기록은 협력적 작업 규약이다. OS ACL이나 Figma 서명 기반 인증은 아니다. 같은 계정으로 파일을 임의 수정하는 공격자를 방어한다고 주장하지 않는다.
현재 범위는 Figma 디자인 결과다. 실제 로그인·검색·파일 다운로드 서버 구현이나 동작 테스트는 포함하지 않는다. 전체 디자인 문서의 모든 정성적 기준을 기계로 판정하지 않으며, 자동 검사와 시각 검토를 함께 사용한다.
