"""Domain Agents - 도메인별 실행 Agent

실제 비즈니스 로직을 수행하는 Agent들입니다.
현재는 보관용으로, 필요시 개별 import하여 사용합니다.

구조:
- collection/: 데이터 수집 (collector, preprocessor)
- analysis/: 분석 (sentiment, keyword, problem, hashtag, competitor, trends)
- insight/: 인사이트 생성
- content/: 콘텐츠 생성 (ad_creative, storyboard, video)
- report/: 리포트 생성
- ops/: 운영 (dashboard, sales, inventory)
- toolkit/: 공용 유틸리티
"""

# 현재는 Mock 모드로 동작하므로 직접 import하지 않음
# 필요시 개별 모듈에서 import

__all__ = [
    "collection",
    "analysis",
    "insight",
    "content",
    "report",
    "ops",
    "toolkit",
]
