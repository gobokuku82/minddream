"""Intent Classifier - 3-depth 계층적 Intent 분류기

Phase 1: Cognitive Layer 고도화
Domain → Category → Subcategory 3단계 분류

Enum, Pydantic 모델, 계층 매핑은 models/intent.py (SSOT)에서 import.
"""

import json
from typing import Dict, Any, Optional, List

from backend.app.core.logging import get_logger, LogContext
from backend.app.dream_agent.llm_manager import get_llm_client
from backend.app.dream_agent.models.intent import (
    IntentDomain,
    IntentCategory,
    IntentSubcategory,
    HierarchicalIntent,
    DOMAIN_TO_CATEGORIES,
    CATEGORY_TO_SUBCATEGORIES,
)

logger = get_logger(__name__)


# ============================================================
# Intent Classifier
# ============================================================

class IntentClassifier:
    """3-depth 계층적 Intent 분류기"""

    def __init__(self):
        self.llm_client = get_llm_client()
        self.log = LogContext(logger, node="IntentClassifier")

    async def classify(
        self,
        user_input: str,
        context: Optional[Dict[str, Any]] = None
    ) -> HierarchicalIntent:
        """
        3단계 계층적 Intent 분류

        Args:
            user_input: 사용자 입력
            context: 이전 대화 컨텍스트

        Returns:
            HierarchicalIntent
        """
        self.log.info(f"Classifying intent for: '{user_input[:50]}...'")

        try:
            # Step 1: Domain 분류
            domain_result = await self._classify_domain(user_input, context)
            domain = domain_result["domain"]
            domain_confidence = domain_result["confidence"]

            self.log.debug(f"Domain: {domain} (confidence: {domain_confidence})")

            # Step 2: Category 분류
            category_result = await self._classify_category(
                user_input, domain, context
            )
            category = category_result["category"]
            category_confidence = category_result["confidence"]

            self.log.debug(f"Category: {category} (confidence: {category_confidence})")

            # Step 3: Subcategory 분류
            subcategory_result = await self._classify_subcategory(
                user_input, category, context
            )
            subcategory = subcategory_result.get("subcategory")
            subcategory_confidence = subcategory_result.get("confidence", 0.0)

            if subcategory:
                self.log.debug(
                    f"Subcategory: {subcategory} (confidence: {subcategory_confidence})"
                )

            # Calculate overall confidence (weighted average)
            if subcategory:
                overall_confidence = (
                    domain_confidence * 0.3 +
                    category_confidence * 0.4 +
                    subcategory_confidence * 0.3
                )
            else:
                overall_confidence = (
                    domain_confidence * 0.4 +
                    category_confidence * 0.6
                )

            # Determine ML/Biz requirements
            requires_ml, requires_biz = self._determine_execution_requirements(
                domain, category, subcategory
            )

            # 명시적 데이터 수집 요청 감지
            requires_data_collection = self._detect_explicit_data_collection(
                user_input, domain, category, subcategory
            )

            # 명시적 전처리 요청 감지
            requires_preprocessing = self._detect_explicit_preprocessing(
                user_input, category, subcategory
            )

            intent = HierarchicalIntent(
                domain=domain,
                category=category,
                subcategory=subcategory,
                domain_confidence=domain_confidence,
                category_confidence=category_confidence,
                subcategory_confidence=subcategory_confidence,
                overall_confidence=overall_confidence,
                method="llm",
                requires_ml=requires_ml,
                requires_biz=requires_biz,
                requires_data_collection=requires_data_collection,
                requires_preprocessing=requires_preprocessing
            )

            self.log.info(
                f"Intent classified: {domain}.{category}.{subcategory} "
                f"(confidence: {overall_confidence:.2f})"
            )

            return intent

        except Exception as e:
            self.log.error(f"Intent classification error: {e}", exc_info=True)
            # Fallback to keyword-based classification
            return await self._fallback_classify(user_input)

    async def _classify_domain(
        self,
        user_input: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Level 1: Domain 분류"""

        system_prompt = """당신은 K-Beauty 글로벌 트렌드 분석 Agent의 Intent Domain 분류 전문가입니다.
이 시스템은 글로벌 고객의 K-Beauty 반응을 분석하여 트렌드 예측과 비즈니스 인사이트를 제공합니다.

사용자 입력을 다음 도메인 중 하나로 분류하세요:

- data_science: 데이터 수집, 분석, 시각화 관련
  * "리뷰 수집해줘", "데이터 모아줘", "크롤링", "분석해줘" 등 명시적 작업 요청
  * 올리브영/아마존/유튜브 등 플랫폼 데이터 수집 요청

- analytics: K-Beauty 트렌드 분석, 인사이트 도출, 기회 발굴 관련 ⭐핵심⭐
  * "트렌드 알려줘", "인사이트 뽑아줘", "기회 영역 찾아줘"
  * "성분 트렌드", "제형 트렌드", "글로벌 고객 니즈 변화"
  * "신규 기회", "시장 기회", "떠오르는 키워드"

- marketing: 마케팅, 콘텐츠 생성, 캠페인 관련
  * 광고 크리에이티브, 마케팅 자료 생성 요청

- sales: 영업, 고객 관리, 매출 관련

- operations: 운영, 자동화, 보고서 생성 관련

- general: 일반 대화, 도움말, **단순 정보성 질문**
  * "화장품 효과가 뭐야?", "가격 알려줘", "사용법" → general (단순 정보)
  * "안녕", "고마워", "도움말" → general (대화)

**핵심 분류 기준:**
- "트렌드", "인사이트", "기회", "니즈 변화", "성분 동향", "글로벌 반응" → analytics
- "수집", "크롤링", "모아줘", "분석해줘" → data_science
- 단순 정보 질문 (효과, 가격, 추천) → general

JSON 형식으로 응답하세요:
{
    "domain": "domain_name",
    "confidence": 0.95,
    "reasoning": "분류 근거"
}"""

        user_message = f"사용자 입력: {user_input}"
        if context:
            user_message += f"\n이전 컨텍스트: {json.dumps(context, ensure_ascii=False)}"

        try:
            response = await self.llm_client.chat_with_system(
                system_prompt=system_prompt,
                user_message=user_message,
                max_tokens=200
            )
            result = json.loads(response)
            return {
                "domain": IntentDomain(result["domain"]),
                "confidence": result["confidence"]
            }
        except Exception as e:
            self.log.warning(f"Domain classification failed: {e}")
            # Fallback
            return {
                "domain": IntentDomain.GENERAL,
                "confidence": 0.5
            }

    async def _classify_category(
        self,
        user_input: str,
        domain: IntentDomain,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Level 2: Category 분류"""

        # Get valid categories for domain
        valid_categories = DOMAIN_TO_CATEGORIES.get(domain, [])
        categories_str = ", ".join([cat.value for cat in valid_categories])

        system_prompt = f"""당신은 Intent Category 분류 전문가입니다.
도메인이 '{domain.value}'로 분류된 사용자 입력을 다음 카테고리 중 하나로 분류하세요:

{categories_str}

JSON 형식으로 응답하세요:
{{
    "category": "category_name",
    "confidence": 0.92,
    "reasoning": "분류 근거"
}}"""

        user_message = f"사용자 입력: {user_input}"

        try:
            response = await self.llm_client.chat_with_system(
                system_prompt=system_prompt,
                user_message=user_message,
                max_tokens=200
            )
            result = json.loads(response)
            return {
                "category": IntentCategory(result["category"]),
                "confidence": result["confidence"]
            }
        except Exception as e:
            self.log.warning(f"Category classification failed: {e}")
            # Fallback to first category
            fallback_category = valid_categories[0] if valid_categories else IntentCategory.CONVERSATION
            return {
                "category": fallback_category,
                "confidence": 0.5
            }

    async def _classify_subcategory(
        self,
        user_input: str,
        category: IntentCategory,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Level 3: Subcategory 분류"""

        # Get valid subcategories for category
        valid_subcategories = CATEGORY_TO_SUBCATEGORIES.get(category, [])

        if not valid_subcategories:
            return {"subcategory": None, "confidence": 0.0}

        subcategories_str = ", ".join([sub.value for sub in valid_subcategories])

        system_prompt = f"""당신은 Intent Subcategory 분류 전문가입니다.
카테고리가 '{category.value}'로 분류된 사용자 입력을 다음 서브카테고리 중 하나로 분류하세요:

{subcategories_str}

JSON 형식으로 응답하세요:
{{
    "subcategory": "subcategory_name",
    "confidence": 0.88,
    "reasoning": "분류 근거"
}}"""

        user_message = f"사용자 입력: {user_input}"

        try:
            response = await self.llm_client.chat_with_system(
                system_prompt=system_prompt,
                user_message=user_message,
                max_tokens=200
            )
            result = json.loads(response)
            return {
                "subcategory": IntentSubcategory(result["subcategory"]),
                "confidence": result["confidence"]
            }
        except Exception as e:
            self.log.warning(f"Subcategory classification failed: {e}")
            # Fallback to first subcategory
            fallback_subcategory = valid_subcategories[0] if valid_subcategories else None
            return {
                "subcategory": fallback_subcategory,
                "confidence": 0.5
            }

    def _determine_execution_requirements(
        self,
        domain: IntentDomain,
        category: IntentCategory,
        subcategory: Optional[IntentSubcategory]
    ) -> tuple[bool, bool]:
        """
        실행 레이어 요구사항 결정

        GENERAL domain의 경우 ML/Biz 실행 없이 바로 응답 생성.
        일반 대화, 도움말, 화장품 관련 일반 질문 등은 tool 호출 없이 처리.
        """

        requires_ml = False
        requires_biz = False

        # GENERAL domain: 일반 대화, 도움말 → ML/Biz 불필요
        # 바로 response 노드로 라우팅되어 LLM이 직접 응답 생성
        if domain == IntentDomain.GENERAL:
            self.log.info(f"GENERAL domain detected - no ML/Biz execution required")
            return False, False

        # DATA_SCIENCE domain always requires ML
        if domain == IntentDomain.DATA_SCIENCE:
            requires_ml = True

        # MARKETING domain usually requires Biz
        if domain == IntentDomain.MARKETING:
            requires_biz = True
            # Some categories may also need ML
            if category in [
                IntentCategory.MARKET_RESEARCH,
                IntentCategory.BRAND_ANALYSIS
            ]:
                requires_ml = True

        # SALES and ANALYTICS domains need both
        if domain in [IntentDomain.SALES, IntentDomain.ANALYTICS]:
            requires_ml = True
            requires_biz = True

        # OPERATIONS domain usually needs Biz
        if domain == IntentDomain.OPERATIONS:
            requires_biz = True

        return requires_ml, requires_biz

    def _detect_explicit_data_collection(
        self,
        user_input: str,
        domain: IntentDomain,
        category: IntentCategory,
        subcategory: Optional[IntentSubcategory]
    ) -> bool:
        """
        명시적 데이터 수집 요청 감지

        사용자가 명시적으로 데이터 수집을 요청했는지 판단합니다.
        "수집해줘", "collect", "크롤링", "데이터 모아줘" 등의 키워드가 있어야 True

        Returns:
            bool: 명시적 데이터 수집 요청 여부
        """
        input_lower = user_input.lower()

        # 명시적 데이터 수집 키워드 (한국어 + 영어)
        EXPLICIT_COLLECTION_KEYWORDS = [
            # 한국어 - 수집 관련
            "수집해", "수집해줘", "수집 해줘", "수집하", "데이터 수집",
            "모아줘", "모아 줘", "긁어", "긁어줘", "긁어와",
            "크롤링", "크롤", "스크래핑", "스크랩",
            "가져와", "가져와줘", "불러와", "불러와줘",
            "리뷰 수집", "댓글 수집", "데이터 모아",
            # 영어 - 수집 관련
            "collect", "scrape", "crawl", "fetch", "gather",
            "get reviews", "get data", "pull data", "extract",
            # 플랫폼 명시 + 수집
            "아마존에서", "올리브영에서", "유튜브에서", "틱톡에서",
            "amazon", "oliveyoung", "youtube", "tiktok",
        ]

        # 1. 명시적 수집 키워드 확인
        has_explicit_keyword = any(kw in input_lower for kw in EXPLICIT_COLLECTION_KEYWORDS)

        # 2. Category가 DATA_COLLECTION인 경우
        is_collection_category = category == IntentCategory.DATA_COLLECTION

        # 3. Subcategory가 WEB_SCRAPING 또는 API_FETCHING인 경우
        is_scraping_subcategory = subcategory in [
            IntentSubcategory.WEB_SCRAPING,
            IntentSubcategory.API_FETCHING,
        ]

        # 명시적 키워드가 있거나, Collection 카테고리면서 스크래핑 서브카테고리인 경우만 True
        if has_explicit_keyword:
            self.log.info(f"Explicit data collection detected: keyword match")
            return True

        if is_collection_category and is_scraping_subcategory:
            self.log.info(f"Explicit data collection detected: category={category}, subcategory={subcategory}")
            return True

        # 분석만 요청한 경우는 데이터 수집 없이 기존 데이터 사용
        self.log.debug(f"No explicit data collection request detected")
        return False

    def _detect_explicit_preprocessing(
        self,
        user_input: str,
        category: IntentCategory,
        subcategory: Optional[IntentSubcategory]
    ) -> bool:
        """
        명시적 전처리 요청 감지

        사용자가 명시적으로 데이터 전처리를 요청했는지 판단합니다.
        "전처리해줘", "정제해줘", "클리닝", "preprocess" 등의 키워드가 있어야 True

        Returns:
            bool: 명시적 전처리 요청 여부
        """
        input_lower = user_input.lower()

        # 명시적 전처리 키워드 (한국어 + 영어)
        EXPLICIT_PREPROCESSING_KEYWORDS = [
            # 한국어 - 전처리 관련
            "전처리", "전처리해", "전처리해줘", "데이터 전처리",
            "정제", "정제해", "정제해줘", "데이터 정제",
            "클리닝", "클린", "정리해", "정리해줘",
            "정규화", "정규화해", "노말라이즈",
            "변환해", "변환해줘", "데이터 변환",
            "필터링", "필터해", "필터해줘",
            # 영어 - 전처리 관련
            "preprocess", "preprocessing", "pre-process",
            "clean", "cleaning", "cleanse",
            "normalize", "normalization",
            "transform", "transformation",
            "filter", "filtering",
            "sanitize", "sanitizing",
        ]

        # 1. 명시적 전처리 키워드 확인
        has_explicit_keyword = any(kw in input_lower for kw in EXPLICIT_PREPROCESSING_KEYWORDS)

        # 2. Category가 DATA_PREPROCESSING인 경우
        is_preprocessing_category = category == IntentCategory.DATA_PREPROCESSING

        # 3. Subcategory가 DATA_CLEANING 또는 DATA_TRANSFORMATION인 경우
        is_preprocessing_subcategory = subcategory in [
            IntentSubcategory.DATA_CLEANING,
            IntentSubcategory.DATA_TRANSFORMATION,
            IntentSubcategory.DATA_VALIDATION,
        ]

        # 명시적 키워드가 있을 때만 True
        if has_explicit_keyword:
            self.log.info(f"Explicit preprocessing detected: keyword match")
            return True

        if is_preprocessing_category and is_preprocessing_subcategory:
            self.log.info(f"Explicit preprocessing detected: category={category}, subcategory={subcategory}")
            return True

        self.log.debug(f"No explicit preprocessing request detected")
        return False

    async def _fallback_classify(self, user_input: str) -> HierarchicalIntent:
        """Fallback keyword-based classification"""

        self.log.info("Using fallback keyword-based classification")

        # Simple keyword matching
        input_lower = user_input.lower()

        # Default to general conversation
        domain = IntentDomain.GENERAL
        category = IntentCategory.CONVERSATION
        subcategory = IntentSubcategory.SMALL_TALK

        # 1. 먼저 일반 정보성 질문 패턴 확인 (GENERAL로 유지)
        general_info_patterns = [
            # 질문 패턴
            "뭐야", "뭔가요", "알려줘", "알려주세요", "가르쳐", "설명해",
            "어떻게", "어떤", "무슨", "왜",
            # 화장품 일반 정보 질문
            "효과", "성분", "가격", "사용법", "추천", "좋은", "피부",
            "보습", "미백", "주름", "탄력", "진정",
            # 영어
            "what is", "how to", "recommend", "effect", "ingredient",
        ]

        # 명시적 작업 요청 키워드 (이게 있어야 data_science/marketing 등으로 분류)
        explicit_action_keywords = [
            "수집", "collect", "크롤링", "crawl", "스크래핑", "scrape",
            "분석해", "analyze", "분석해줘", "분석 해줘",
            "모아줘", "긁어", "가져와",
        ]

        # 일반 정보 질문이면서 명시적 작업 요청이 없으면 → GENERAL 유지
        has_info_pattern = any(kw in input_lower for kw in general_info_patterns)
        has_action_keyword = any(kw in input_lower for kw in explicit_action_keywords)

        if has_info_pattern and not has_action_keyword:
            # 일반 정보 질문으로 유지 (기본값 GENERAL)
            self.log.info(f"General info question detected - staying in GENERAL domain")
            pass  # domain, category, subcategory는 기본값 유지

        # 2. 명시적 데이터 수집 요청 확인
        elif any(kw in input_lower for kw in ["수집", "collect", "크롤링", "crawl", "스크래핑", "scrape", "모아줘", "긁어"]):
            domain = IntentDomain.DATA_SCIENCE
            category = IntentCategory.DATA_COLLECTION
            subcategory = IntentSubcategory.WEB_SCRAPING

        # 3. 명시적 데이터 분석 요청 확인 (단순히 "데이터" 단어만 있는 건 안 됨)
        elif any(kw in input_lower for kw in ["분석해", "분석해줘", "분석 해줘", "analyze"]):
            domain = IntentDomain.DATA_SCIENCE
            category = IntentCategory.DATA_ANALYSIS
            subcategory = IntentSubcategory.STATISTICAL_ANALYSIS

        # 4. 마케팅 콘텐츠 생성 요청
        elif any(kw in input_lower for kw in ["마케팅", "영상", "콘텐츠", "video", "content", "creative"]) and any(kw in input_lower for kw in ["만들어", "생성", "제작", "create"]):
            domain = IntentDomain.MARKETING
            category = IntentCategory.CONTENT_CREATION
            subcategory = IntentSubcategory.VIDEO_GENERATION

        # 5. 보고서 생성 요청
        elif any(kw in input_lower for kw in ["리포트", "보고서", "report", "dashboard"]) and any(kw in input_lower for kw in ["만들어", "생성", "작성", "create"]):
            domain = IntentDomain.OPERATIONS
            category = IntentCategory.REPORTING
            subcategory = IntentSubcategory.REPORT_GENERATION

        requires_ml, requires_biz = self._determine_execution_requirements(
            domain, category, subcategory
        )

        # Fallback에서도 명시적 데이터 수집 요청 감지
        requires_data_collection = self._detect_explicit_data_collection(
            user_input, domain, category, subcategory
        )

        # Fallback에서도 명시적 전처리 요청 감지
        requires_preprocessing = self._detect_explicit_preprocessing(
            user_input, category, subcategory
        )

        return HierarchicalIntent(
            domain=domain,
            category=category,
            subcategory=subcategory,
            domain_confidence=0.6,
            category_confidence=0.5,
            subcategory_confidence=0.5,
            overall_confidence=0.53,
            method="keyword",
            requires_ml=requires_ml,
            requires_biz=requires_biz,
            requires_data_collection=requires_data_collection,
            requires_preprocessing=requires_preprocessing
        )



# Helper functions re-exported from models for backward compatibility
from backend.app.dream_agent.models.intent import (  # noqa: F811, E402
    get_subcategories_for_category,
    get_categories_for_domain,
    validate_intent_hierarchy,
)
