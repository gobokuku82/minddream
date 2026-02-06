"""Response Formatter

출력 포맷별 응답 생성
"""

from typing import Any, Literal

from app.core.logging import get_logger
from app.dream_agent.models import Attachment, Intent, ResponsePayload

logger = get_logger(__name__)


class ResponseFormatter:
    """응답 포맷터"""

    def format(
        self,
        format_type: Literal["text", "mixed", "pdf", "image", "video"],
        content: dict[str, Any],
        intent: Intent,
        language: str = "ko",
    ) -> ResponsePayload:
        """응답 포맷팅

        Args:
            format_type: 출력 포맷
            content: 포맷팅할 컨텐츠
            intent: 원본 의도
            language: 언어

        Returns:
            포맷된 ResponsePayload
        """
        if format_type == "text":
            return self._format_text(content, intent, language)
        elif format_type == "mixed":
            return self._format_mixed(content, intent, language)
        elif format_type == "pdf":
            return self._format_pdf(content, intent, language)
        else:
            return self._format_text(content, intent, language)

    def _format_text(
        self,
        content: dict[str, Any],
        intent: Intent,
        language: str,
    ) -> ResponsePayload:
        """텍스트 포맷"""
        text = content.get("text", "")
        summary = content.get("summary", "")

        return ResponsePayload(
            format="text",
            text=text,
            summary=summary,
            attachments=[],
            next_actions=content.get("next_actions", []),
            metadata={"language": language},
        )

    def _format_mixed(
        self,
        content: dict[str, Any],
        intent: Intent,
        language: str,
    ) -> ResponsePayload:
        """혼합 포맷 (텍스트 + 첨부파일)"""
        text = content.get("text", "")
        summary = content.get("summary", "")

        # 첨부파일 생성
        attachments = []
        for att_data in content.get("attachments", []):
            attachments.append(
                Attachment(
                    type=att_data.get("type", "file"),
                    title=att_data.get("title", "Attachment"),
                    url=att_data.get("url", ""),
                    description=att_data.get("description"),
                )
            )

        return ResponsePayload(
            format="mixed",
            text=text,
            summary=summary,
            attachments=attachments,
            next_actions=content.get("next_actions", []),
            metadata={"language": language},
        )

    def _format_pdf(
        self,
        content: dict[str, Any],
        intent: Intent,
        language: str,
    ) -> ResponsePayload:
        """PDF 포맷"""
        # PDF 생성 (실제 구현에서는 PDF 생성 로직)
        pdf_path = content.get("pdf_path", "/reports/report.pdf")

        text = content.get("text", "보고서가 생성되었습니다.")
        summary = content.get("summary", "")

        return ResponsePayload(
            format="pdf",
            text=text,
            summary=summary,
            attachments=[
                Attachment(
                    type="pdf",
                    title="분석 보고서",
                    url=pdf_path,
                    description="상세 분석 보고서",
                )
            ],
            next_actions=content.get("next_actions", []),
            metadata={"language": language, "pdf_path": pdf_path},
        )


class FormatDecider:
    """출력 포맷 결정기"""

    def decide(
        self,
        intent: Intent,
        execution_results: dict[str, Any],
    ) -> Literal["text", "mixed", "pdf", "image", "video"]:
        """출력 포맷 결정

        Args:
            intent: 원본 의도
            execution_results: 실행 결과

        Returns:
            출력 포맷
        """
        domain = intent.domain.value if hasattr(intent.domain, "value") else intent.domain

        # 도메인별 기본 포맷
        domain_formats = {
            "analysis": "mixed",  # 분석 → 차트 포함
            "content": "pdf",     # 콘텐츠 → 보고서
            "operation": "text",  # 운영 → 텍스트
            "inquiry": "text",    # 질의 → 텍스트
        }

        format_type = domain_formats.get(domain, "text")

        # 결과에 차트/이미지가 있으면 mixed
        for result in execution_results.values():
            if isinstance(result, dict):
                data = result.get("data", {})
                if "chart" in data or "image" in data:
                    return "mixed"

        return format_type
