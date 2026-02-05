"""Intent Models - 의도 분류 관련 모델 (SSOT)

3-Depth 계층적 Intent 체계의 Single Source of Truth.
모든 Enum, Pydantic 모델, 계층 매핑이 이 파일에 정의됩니다.

Domain → Category → Subcategory 3단계 분류
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from enum import Enum


# ============================================================
# 3-Depth Intent Hierarchy Enums
# ============================================================

class IntentDomain(str, Enum):
    """Level 1: 도메인 분류"""
    DATA_SCIENCE = "data_science"       # 데이터 수집, 분석, 시각화
    MARKETING = "marketing"              # 마케팅, 콘텐츠 생성, 캠페인
    SALES = "sales"                      # 영업, 고객 관리
    OPERATIONS = "operations"            # 운영, 자동화
    ANALYTICS = "analytics"              # 분석, 인사이트
    GENERAL = "general"                  # 일반 대화


class IntentCategory(str, Enum):
    """Level 2: 카테고리 분류"""

    # DATA_SCIENCE domain
    DATA_COLLECTION = "data_collection"
    DATA_PREPROCESSING = "data_preprocessing"
    DATA_ANALYSIS = "data_analysis"
    DATA_VISUALIZATION = "data_visualization"

    # MARKETING domain
    CONTENT_CREATION = "content_creation"
    CAMPAIGN_MANAGEMENT = "campaign_management"
    BRAND_ANALYSIS = "brand_analysis"
    MARKET_RESEARCH = "market_research"

    # SALES domain
    SALES_ANALYSIS = "sales_analysis"
    CUSTOMER_INSIGHTS = "customer_insights"
    FORECASTING = "forecasting"

    # OPERATIONS domain
    PROCESS_AUTOMATION = "process_automation"
    REPORTING = "reporting"
    WORKFLOW_MANAGEMENT = "workflow_management"

    # ANALYTICS domain
    PERFORMANCE_ANALYSIS = "performance_analysis"
    COMPETITIVE_ANALYSIS = "competitive_analysis"
    TREND_ANALYSIS = "trend_analysis"

    # GENERAL domain
    CONVERSATION = "conversation"
    HELP = "help"


class IntentSubcategory(str, Enum):
    """Level 3: 서브카테고리 분류"""

    # DATA_COLLECTION subcategories
    WEB_SCRAPING = "web_scraping"
    API_FETCHING = "api_fetching"
    DATABASE_QUERY = "database_query"
    FILE_IMPORT = "file_import"

    # DATA_PREPROCESSING subcategories
    DATA_CLEANING = "data_cleaning"
    DATA_TRANSFORMATION = "data_transformation"
    DATA_VALIDATION = "data_validation"

    # DATA_ANALYSIS subcategories
    STATISTICAL_ANALYSIS = "statistical_analysis"
    ML_MODELING = "ml_modeling"
    NLP_ANALYSIS = "nlp_analysis"
    SENTIMENT_ANALYSIS = "sentiment_analysis"

    # DATA_VISUALIZATION subcategories
    CHART_GENERATION = "chart_generation"
    DASHBOARD_CREATION = "dashboard_creation"
    REPORT_VISUALIZATION = "report_visualization"

    # CONTENT_CREATION subcategories
    VIDEO_GENERATION = "video_generation"
    COPYWRITING = "copywriting"
    IMAGE_DESIGN = "image_design"
    AD_CREATIVE = "ad_creative"
    SOCIAL_MEDIA_POST = "social_media_post"

    # CAMPAIGN_MANAGEMENT subcategories
    CAMPAIGN_PLANNING = "campaign_planning"
    CAMPAIGN_EXECUTION = "campaign_execution"
    CAMPAIGN_OPTIMIZATION = "campaign_optimization"

    # BRAND_ANALYSIS subcategories
    BRAND_MONITORING = "brand_monitoring"
    BRAND_COMPARISON = "brand_comparison"
    BRAND_SENTIMENT = "brand_sentiment"

    # MARKET_RESEARCH subcategories
    MARKET_SIZING = "market_sizing"
    CHANNEL_ANALYSIS = "channel_analysis"
    CONSUMER_BEHAVIOR = "consumer_behavior"

    # SALES_ANALYSIS subcategories
    REVENUE_ANALYSIS = "revenue_analysis"
    PRODUCT_PERFORMANCE = "product_performance"
    SALES_ATTRIBUTION = "sales_attribution"

    # CUSTOMER_INSIGHTS subcategories
    CUSTOMER_SEGMENTATION = "customer_segmentation"
    CUSTOMER_LIFETIME_VALUE = "customer_lifetime_value"
    CHURN_ANALYSIS = "churn_analysis"

    # PERFORMANCE_ANALYSIS subcategories
    KPI_TRACKING = "kpi_tracking"
    ROI_ANALYSIS = "roi_analysis"
    PERFORMANCE_REPORT = "performance_report"

    # COMPETITIVE_ANALYSIS subcategories
    COMPETITOR_TRACKING = "competitor_tracking"
    MARKET_POSITIONING = "market_positioning"
    COMPETITIVE_BENCHMARKING = "competitive_benchmarking"

    # TREND_ANALYSIS subcategories
    TREND_DETECTION = "trend_detection"
    FORECAST_MODELING = "forecast_modeling"
    PATTERN_RECOGNITION = "pattern_recognition"

    # K-BEAUTY GLOBAL TREND subcategories
    KBEAUTY_GLOBAL_TREND = "kbeauty_global_trend"
    INGREDIENT_TREND = "ingredient_trend"
    FORMULATION_TREND = "formulation_trend"
    GLOBAL_CUSTOMER_NEEDS = "global_customer_needs"
    NEW_OPPORTUNITY_DISCOVERY = "new_opportunity_discovery"

    # REPORTING subcategories
    REPORT_GENERATION = "report_generation"
    AUTOMATED_REPORTING = "automated_reporting"
    PRESENTATION_CREATION = "presentation_creation"

    # CONVERSATION subcategories
    GREETING = "greeting"
    SMALL_TALK = "small_talk"
    FEEDBACK = "feedback"

    # HELP subcategories
    FEATURE_INQUIRY = "feature_inquiry"
    TROUBLESHOOTING = "troubleshooting"
    DOCUMENTATION = "documentation"


# ============================================================
# Intent Hierarchy Mapping
# ============================================================

DOMAIN_TO_CATEGORIES: Dict[IntentDomain, List[IntentCategory]] = {
    IntentDomain.DATA_SCIENCE: [
        IntentCategory.DATA_COLLECTION,
        IntentCategory.DATA_PREPROCESSING,
        IntentCategory.DATA_ANALYSIS,
        IntentCategory.DATA_VISUALIZATION,
    ],
    IntentDomain.MARKETING: [
        IntentCategory.CONTENT_CREATION,
        IntentCategory.CAMPAIGN_MANAGEMENT,
        IntentCategory.BRAND_ANALYSIS,
        IntentCategory.MARKET_RESEARCH,
    ],
    IntentDomain.SALES: [
        IntentCategory.SALES_ANALYSIS,
        IntentCategory.CUSTOMER_INSIGHTS,
        IntentCategory.FORECASTING,
    ],
    IntentDomain.OPERATIONS: [
        IntentCategory.PROCESS_AUTOMATION,
        IntentCategory.REPORTING,
        IntentCategory.WORKFLOW_MANAGEMENT,
    ],
    IntentDomain.ANALYTICS: [
        IntentCategory.PERFORMANCE_ANALYSIS,
        IntentCategory.COMPETITIVE_ANALYSIS,
        IntentCategory.TREND_ANALYSIS,
    ],
    IntentDomain.GENERAL: [
        IntentCategory.CONVERSATION,
        IntentCategory.HELP,
    ],
}

CATEGORY_TO_SUBCATEGORIES: Dict[IntentCategory, List[IntentSubcategory]] = {
    IntentCategory.DATA_COLLECTION: [
        IntentSubcategory.WEB_SCRAPING,
        IntentSubcategory.API_FETCHING,
        IntentSubcategory.DATABASE_QUERY,
        IntentSubcategory.FILE_IMPORT,
    ],
    IntentCategory.DATA_PREPROCESSING: [
        IntentSubcategory.DATA_CLEANING,
        IntentSubcategory.DATA_TRANSFORMATION,
        IntentSubcategory.DATA_VALIDATION,
    ],
    IntentCategory.DATA_ANALYSIS: [
        IntentSubcategory.STATISTICAL_ANALYSIS,
        IntentSubcategory.ML_MODELING,
        IntentSubcategory.NLP_ANALYSIS,
        IntentSubcategory.SENTIMENT_ANALYSIS,
    ],
    IntentCategory.DATA_VISUALIZATION: [
        IntentSubcategory.CHART_GENERATION,
        IntentSubcategory.DASHBOARD_CREATION,
        IntentSubcategory.REPORT_VISUALIZATION,
    ],
    IntentCategory.CONTENT_CREATION: [
        IntentSubcategory.VIDEO_GENERATION,
        IntentSubcategory.COPYWRITING,
        IntentSubcategory.IMAGE_DESIGN,
        IntentSubcategory.AD_CREATIVE,
        IntentSubcategory.SOCIAL_MEDIA_POST,
    ],
    IntentCategory.CAMPAIGN_MANAGEMENT: [
        IntentSubcategory.CAMPAIGN_PLANNING,
        IntentSubcategory.CAMPAIGN_EXECUTION,
        IntentSubcategory.CAMPAIGN_OPTIMIZATION,
    ],
    IntentCategory.BRAND_ANALYSIS: [
        IntentSubcategory.BRAND_MONITORING,
        IntentSubcategory.BRAND_COMPARISON,
        IntentSubcategory.BRAND_SENTIMENT,
    ],
    IntentCategory.MARKET_RESEARCH: [
        IntentSubcategory.MARKET_SIZING,
        IntentSubcategory.CHANNEL_ANALYSIS,
        IntentSubcategory.CONSUMER_BEHAVIOR,
    ],
    IntentCategory.SALES_ANALYSIS: [
        IntentSubcategory.REVENUE_ANALYSIS,
        IntentSubcategory.PRODUCT_PERFORMANCE,
        IntentSubcategory.SALES_ATTRIBUTION,
    ],
    IntentCategory.CUSTOMER_INSIGHTS: [
        IntentSubcategory.CUSTOMER_SEGMENTATION,
        IntentSubcategory.CUSTOMER_LIFETIME_VALUE,
        IntentSubcategory.CHURN_ANALYSIS,
    ],
    IntentCategory.PERFORMANCE_ANALYSIS: [
        IntentSubcategory.KPI_TRACKING,
        IntentSubcategory.ROI_ANALYSIS,
        IntentSubcategory.PERFORMANCE_REPORT,
    ],
    IntentCategory.COMPETITIVE_ANALYSIS: [
        IntentSubcategory.COMPETITOR_TRACKING,
        IntentSubcategory.MARKET_POSITIONING,
        IntentSubcategory.COMPETITIVE_BENCHMARKING,
    ],
    IntentCategory.TREND_ANALYSIS: [
        IntentSubcategory.TREND_DETECTION,
        IntentSubcategory.FORECAST_MODELING,
        IntentSubcategory.PATTERN_RECOGNITION,
        # K-Beauty 글로벌 트렌드 분석 특화
        IntentSubcategory.KBEAUTY_GLOBAL_TREND,
        IntentSubcategory.INGREDIENT_TREND,
        IntentSubcategory.FORMULATION_TREND,
        IntentSubcategory.GLOBAL_CUSTOMER_NEEDS,
        IntentSubcategory.NEW_OPPORTUNITY_DISCOVERY,
    ],
    IntentCategory.REPORTING: [
        IntentSubcategory.REPORT_GENERATION,
        IntentSubcategory.AUTOMATED_REPORTING,
        IntentSubcategory.PRESENTATION_CREATION,
    ],
    IntentCategory.CONVERSATION: [
        IntentSubcategory.GREETING,
        IntentSubcategory.SMALL_TALK,
        IntentSubcategory.FEEDBACK,
    ],
    IntentCategory.HELP: [
        IntentSubcategory.FEATURE_INQUIRY,
        IntentSubcategory.TROUBLESHOOTING,
        IntentSubcategory.DOCUMENTATION,
    ],
}


# ============================================================
# Pydantic Models
# ============================================================

class Entity(BaseModel):
    """추출된 엔티티"""
    type: str
    value: str
    confidence: float = Field(ge=0.0, le=1.0)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator('confidence')
    @classmethod
    def validate_confidence(cls, v):
        if v < 0 or v > 1:
            raise ValueError("Confidence must be between 0 and 1")
        return v


class HierarchicalIntent(BaseModel):
    """3-depth 계층적 Intent"""
    domain: IntentDomain
    category: IntentCategory
    subcategory: Optional[IntentSubcategory] = None

    # Confidence scores for each level
    domain_confidence: float = Field(ge=0.0, le=1.0)
    category_confidence: float = Field(ge=0.0, le=1.0)
    subcategory_confidence: float = Field(default=0.0, ge=0.0, le=1.0)

    # Overall confidence (weighted average)
    overall_confidence: float = Field(ge=0.0, le=1.0)

    # Classification method
    method: str = "unknown"  # llm, keyword, hybrid

    # Requires ML/Biz execution
    requires_ml: bool = False
    requires_biz: bool = False

    # 명시적 데이터 수집 요청 여부
    requires_data_collection: bool = False

    # 명시적 전처리 요청 여부
    requires_preprocessing: bool = False

    class Config:
        json_schema_extra = {
            "example": {
                "domain": "marketing",
                "category": "content_creation",
                "subcategory": "video_generation",
                "domain_confidence": 0.95,
                "category_confidence": 0.92,
                "subcategory_confidence": 0.88,
                "overall_confidence": 0.92,
                "method": "llm",
                "requires_ml": False,
                "requires_biz": True,
                "requires_data_collection": False,
                "requires_preprocessing": False,
            }
        }


# Backward-compatible alias
Intent = HierarchicalIntent


# ============================================================
# Helper Functions
# ============================================================

def get_categories_for_domain(domain: IntentDomain) -> List[IntentCategory]:
    """도메인에 해당하는 카테고리 목록 반환"""
    return DOMAIN_TO_CATEGORIES.get(domain, [])


def get_subcategories_for_category(category: IntentCategory) -> List[IntentSubcategory]:
    """카테고리에 해당하는 서브카테고리 목록 반환"""
    return CATEGORY_TO_SUBCATEGORIES.get(category, [])


def validate_intent_hierarchy(
    domain: IntentDomain,
    category: IntentCategory,
    subcategory: Optional[IntentSubcategory] = None,
) -> bool:
    """Intent 계층 구조 유효성 검증"""

    # Check domain -> category mapping
    valid_categories = DOMAIN_TO_CATEGORIES.get(domain, [])
    if category not in valid_categories:
        return False

    # Check category -> subcategory mapping
    if subcategory:
        valid_subcategories = CATEGORY_TO_SUBCATEGORIES.get(category, [])
        if subcategory not in valid_subcategories:
            return False

    return True
