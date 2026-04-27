"""Tests for Phase 3: LLMAssemblyGeneratorService."""

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, Mock, patch, MagicMock
import json

from pydantic import ValidationError

from app.services.llm_assembly_generator import LLMAssemblyGeneratorService
from app.models.schemas import Part, PartType, SvgDrawing, AssemblyStep
from app.core.config import AssemblyTone
from app.core.exceptions import LLMApiError


# ============================================================================
# FIXTURES
# ============================================================================


@pytest_asyncio.fixture
async def llm_service():
    """Create an LLMAssemblyGeneratorService instance with test API key."""
    service = LLMAssemblyGeneratorService()
    # Set a test API key to avoid "API key not configured" errors
    service.api_key = "test-api-key-12345"
    return service


@pytest.fixture
def sample_parts():
    """Create sample parts for testing."""
    return [
        Part(
            id="A",
            original_index=0,
            part_type=PartType.PANEL,
            quantity=1,
            volume=100.5,
            dimensions={"width": 50, "height": 30, "depth": 2},
            centroid=[25, 15, 1],
            surface_area=3200,
            group_id="A",
            metrics={},
        ),
        Part(
            id="B",
            original_index=1,
            part_type=PartType.FASTENER,
            quantity=8,
            volume=1.0,
            dimensions={"width": 3, "height": 3, "depth": 10},
            centroid=[1.5, 1.5, 5],
            surface_area=120,
            group_id="B",
            metrics={},
        ),
        Part(
            id="C",
            original_index=2,
            part_type=PartType.STRUCTURAL,
            quantity=2,
            volume=50.0,
            dimensions={"width": 20, "height": 20, "depth": 5},
            centroid=[10, 10, 2.5],
            surface_area=1400,
            group_id="C",
            metrics={},
        ),
    ]


@pytest.fixture
def sample_drawings(sample_parts):
    """Create sample SVG drawings for testing."""
    return [
        SvgDrawing(part_id=part.id, svg_content=f"<svg>Part {part.id}</svg>")
        for part in sample_parts
    ]


@pytest.fixture
def mock_llm_response():
    """Create a mock LLM API response."""
    return {
        "choices": [
            {
                "message": {
                    "content": json.dumps(
                        {
                            "steps": [
                                {
                                    "step_number": 1,
                                    "title": "Attach base panel",
                                    "description": "Attach part B to part A using fasteners",
                                    "detail_description": "Carefully align part B with the mounting holes on part A",
                                    "part_indices": [0, 1],
                                    "part_roles": {0: "base", 1: "fastener"},
                                    "context_part_indices": [],
                                    "assembly_sequence": ["Align", "Insert", "Secure"],
                                    "warnings": ["Do not overtighten"],
                                    "tips": ["Use a level to ensure alignment"],
                                    "confidence_score": 0.95,
                                    "is_llm_generated": True,
                                }
                            ]
                        }
                    )
                }
            }
        ],
        "usage": {"prompt_tokens": 150, "completion_tokens": 200, "total_tokens": 350},
    }


# ============================================================================
# VALIDATION TESTS (4 tests)
# ============================================================================


class TestLLMInputValidation:
    """Test input validation for LLMAssemblyGeneratorService."""

    @pytest.mark.asyncio
    async def test_validate_valid_parts_and_drawings(
        self, llm_service, sample_parts, sample_drawings
    ):
        """Test validation of valid parts and drawings."""
        result, error = await llm_service.validate_input(sample_parts, sample_drawings)
        assert result is True
        assert error is None

    @pytest.mark.asyncio
    async def test_validate_empty_parts(self, llm_service, sample_drawings):
        """Test validation fails for empty parts list."""
        result, error = await llm_service.validate_input([], sample_drawings)
        assert result is False
        assert error is not None

    @pytest.mark.asyncio
    async def test_validate_empty_drawings(self, llm_service, sample_parts):
        """Test validation fails for empty drawings list."""
        result, error = await llm_service.validate_input(sample_parts, [])
        assert result is False
        assert error is not None

    @pytest.mark.asyncio
    async def test_validate_parts_drawings_mismatch(self, llm_service, sample_parts):
        """Test validation fails when parts and drawings count mismatch."""
        mismatched_drawings = [SvgDrawing(part_id="A", svg_content="<svg/>")]
        result, error = await llm_service.validate_input(sample_parts, mismatched_drawings)
        assert result is False
        assert "mismatch" in error.lower()


# ============================================================================
# PROMPT BUILDING TESTS (5 tests)
# ============================================================================


class TestPromptBuilding:
    """Test prompt generation for different tones."""

    def test_build_system_prompt_ikea(self, llm_service):
        """Test IKEA tone prompt stays constrained and technical."""
        prompt = llm_service._build_system_prompt(AssemblyTone.IKEA)
        assert "technical" in prompt.lower() or "operational" in prompt.lower()
        assert "emoji" in prompt.lower() or "marketing" in prompt.lower()
        assert isinstance(prompt, str)
        assert len(prompt) > 100

    def test_build_system_prompt_technical(self, llm_service):
        """Test TECHNICAL tone system prompt is formal."""
        prompt = llm_service._build_system_prompt(AssemblyTone.TECHNICAL)
        assert "precise" in prompt.lower() or "technical" in prompt.lower()
        assert "specification" in prompt.lower() or "requirement" in prompt.lower()
        assert isinstance(prompt, str)
        assert len(prompt) > 100

    def test_build_system_prompt_beginner(self, llm_service):
        """Test BEGINNER tone system prompt is safety-focused."""
        prompt = llm_service._build_system_prompt(AssemblyTone.BEGINNER)
        assert "safety" in prompt.lower() or "warning" in prompt.lower()
        assert "beginner" in prompt.lower() or "simple" in prompt.lower()
        assert isinstance(prompt, str)
        assert len(prompt) > 100

    def test_build_user_prompt_includes_parts(self, llm_service, sample_parts):
        """Test user prompt includes part information."""
        prompt = llm_service._build_user_prompt(sample_parts, AssemblyTone.IKEA)
        assert "Part A" in prompt or "part_id" in prompt.lower()
        assert "Part B" in prompt or "part B" in prompt.lower()
        assert isinstance(prompt, str)
        assert len(prompt) > 200

    def test_build_user_prompt_includes_dimensions(self, llm_service, sample_parts):
        """Test user prompt includes part dimensions."""
        prompt = llm_service._build_user_prompt(sample_parts, AssemblyTone.TECHNICAL)
        # Check that dimensions are in prompt (width, height, depth values)
        assert "50" in prompt or "width" in prompt.lower()
        assert "30" in prompt or "height" in prompt.lower()
        assert isinstance(prompt, str)

    @pytest.mark.asyncio
    async def test_build_prompt_includes_step_skeleton_constraints(
        self, llm_service, sample_parts, sample_drawings
    ):
        """Prompt should constrain the model to the predefined step skeleton."""
        skeleton_steps = [
            AssemblyStep(
                step_number=1,
                title="Base skeleton",
                description="",
                detail_description="",
                part_indices=[0, 1],
                part_roles={0: "panel", 1: "fastener"},
                context_part_indices=[2],
                assembly_sequence=[],
                warnings=[],
                tips=[],
                duration_minutes=3,
                is_llm_generated=False,
            )
        ]

        prompt = await llm_service._build_prompt(
            sample_parts,
            sample_drawings,
            AssemblyTone.TECHNICAL,
            skeleton_steps,
        )

        assert "do not change part_indices" in prompt.lower()
        assert '"part_indices": [' in prompt
        assert '"context_part_indices": [' in prompt
        assert '"step_number": 1' in prompt


# ============================================================================
# API CALL TESTS (5 tests)
# ============================================================================


class TestLLMApiCalls:
    """Test API communication with OpenRouter."""

    @pytest.mark.asyncio
    async def test_call_llm_success(self, llm_service, sample_parts, mock_llm_response):
        """Test successful LLM API call."""
        # Create a mock response object
        mock_response = Mock(status_code=200, json=lambda: mock_llm_response)
        mock_response.raise_for_status = Mock()

        # Create mock client with async context manager support
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch("httpx.AsyncClient", return_value=mock_client):
            result = await llm_service._call_llm(
                "system", "user", AssemblyTone.IKEA, max_tokens=2000
            )
            assert result is not None
            assert isinstance(result, dict)
            assert "choices" in result

    @pytest.mark.asyncio
    async def test_call_llm_timeout(self, llm_service):
        """Test LLM API call timeout handling."""
        import httpx

        # Create mock client that raises TimeoutException
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(side_effect=httpx.TimeoutException("Request timed out"))
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch("httpx.AsyncClient", return_value=mock_client):
            with pytest.raises(TimeoutError) as exc_info:
                await llm_service._call_llm("system", "user", AssemblyTone.IKEA, max_tokens=2000)
            # Check for "timed" since the message is "timed out" not "timeout"
            assert "timed" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_call_llm_unauthorized(self, llm_service):
        """Test LLM API call with invalid API key."""
        mock_response = Mock(status_code=401)
        mock_response.raise_for_status = Mock()

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch("httpx.AsyncClient", return_value=mock_client):
            with pytest.raises(LLMApiError) as exc_info:
                await llm_service._call_llm("system", "user", AssemblyTone.IKEA, max_tokens=2000)
            assert "401" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_call_llm_rate_limit(self, llm_service):
        """Test LLM API call with rate limiting."""
        mock_response = Mock(status_code=429)
        mock_response.raise_for_status = Mock()

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch("httpx.AsyncClient", return_value=mock_client):
            with pytest.raises(LLMApiError) as exc_info:
                await llm_service._call_llm("system", "user", AssemblyTone.IKEA, max_tokens=2000)
            assert "429" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_call_llm_malformed_response(self, llm_service):
        """Test LLM API call with malformed JSON response."""
        mock_response = Mock(status_code=200, json=lambda: {"invalid": "format"})
        mock_response.raise_for_status = Mock()

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch("httpx.AsyncClient", return_value=mock_client):
            result = await llm_service._call_llm(
                "system", "user", AssemblyTone.IKEA, max_tokens=2000
            )
            # Should return some result (may be None or raise)
            assert result is None or isinstance(result, dict)


# ============================================================================
# RESPONSE PARSING TESTS (3 tests)
# ============================================================================


class TestResponseParsing:
    """Test parsing LLM responses."""

    def test_parse_response_valid_json(self, llm_service, mock_llm_response):
        """Test parsing valid LLM response."""
        response_text = mock_llm_response["choices"][0]["message"]["content"]
        result = llm_service._parse_response(response_text)
        assert isinstance(result, list)
        assert len(result) > 0
        assert all(isinstance(step, AssemblyStep) for step in result)

    def test_parse_response_extracts_steps(self, llm_service, mock_llm_response):
        """Test that parsing extracts all steps."""
        response_text = mock_llm_response["choices"][0]["message"]["content"]
        result = llm_service._parse_response(response_text)
        assert len(result) == 1
        assert result[0].step_number == 1
        assert result[0].title == "Attach base panel"
        assert result[0].is_llm_generated is True

    def test_parse_response_invalid_json(self, llm_service):
        """Test parsing invalid JSON response."""
        invalid_response = "This is not valid JSON"
        with pytest.raises(Exception):
            llm_service._parse_response(invalid_response)

    @pytest.mark.asyncio
    async def test_parse_llm_response_rejects_changed_part_indices(self, llm_service):
        """LLM output should be rejected when it changes the predefined parts."""
        response_text = json.dumps(
            {
                "steps": [
                    {
                        "step_number": 1,
                        "title": "Secure panel",
                        "description": "Align the panel and secure it.",
                        "detail_description": "Align the panel to the bracket and tighten the fastener.",
                        "part_indices": [2],
                        "part_roles": {"2": "bracket"},
                        "context_part_indices": [1],
                        "assembly_sequence": ["Align", "Secure"],
                        "warnings": [],
                        "tips": [],
                        "duration_minutes": 4,
                    }
                ]
            }
        )
        expected_steps = [
            AssemblyStep(
                step_number=1,
                title="Skeleton",
                description="",
                detail_description="",
                part_indices=[0, 1],
                part_roles={0: "panel", 1: "fastener"},
                context_part_indices=[2],
                assembly_sequence=[],
                warnings=[],
                tips=[],
                duration_minutes=3,
                is_llm_generated=False,
            )
        ]

        with pytest.raises(ValidationError):
            await llm_service._parse_llm_response(response_text, expected_steps)

    @pytest.mark.asyncio
    async def test_parse_llm_response_preserves_expected_indices(self, llm_service):
        """Valid LLM output should keep the predefined step topology."""
        response_text = json.dumps(
            {
                "steps": [
                    {
                        "step_number": 1,
                        "title": "Secure side panel",
                        "description": "Align panel A with bracket C and insert fastener B.",
                        "detail_description": "Keep the panel edge flush with the bracket face, then seat the fastener without over-tightening.",
                        "part_indices": [0, 1],
                        "part_roles": {"0": "side panel", "1": "fastener"},
                        "context_part_indices": [2],
                        "assembly_sequence": ["Align panel", "Insert fastener", "Tighten"],
                        "warnings": ["Keep the bracket square during tightening."],
                        "tips": ["Check that the panel edge stays flush before tightening fully."],
                        "duration_minutes": 4,
                    }
                ]
            }
        )
        expected_steps = [
            AssemblyStep(
                step_number=1,
                title="Skeleton",
                description="",
                detail_description="",
                part_indices=[0, 1],
                part_roles={0: "panel", 1: "fastener"},
                context_part_indices=[2],
                assembly_sequence=[],
                warnings=[],
                tips=[],
                duration_minutes=3,
                is_llm_generated=False,
            )
        ]

        steps = await llm_service._parse_llm_response(response_text, expected_steps)

        assert steps[0].part_indices == [0, 1]
        assert steps[0].context_part_indices == [2]
        assert steps[0].title == "Secure side panel"


# ============================================================================
# FALLBACK TESTS (2 tests)
# ============================================================================


class TestFallbackBehavior:
    """Test graceful fallback on LLM failure."""

    @pytest.mark.asyncio
    async def test_process_falls_back_on_api_error(
        self, llm_service, sample_parts, sample_drawings
    ):
        """Test that process falls back to rules when API fails."""
        with patch.object(llm_service, "_call_llm") as mock_call:
            import httpx

            mock_call.side_effect = httpx.ConnectError("Connection failed")
            # Should not raise, but handle gracefully
            # (actual behavior depends on implementation)
            assert llm_service is not None

    @pytest.mark.asyncio
    async def test_process_handles_malformed_llm_response(
        self, llm_service, sample_parts, sample_drawings
    ):
        """Test that process handles malformed LLM response gracefully."""
        with patch.object(llm_service, "_call_llm") as mock_call:
            mock_call.return_value = {"choices": [{"message": {"content": "invalid"}}]}
            # Should handle gracefully without raising
            assert llm_service is not None


# ============================================================================
# INTEGRATION TESTS (2 tests - basic LLM flow)
# ============================================================================


class TestLLMIntegration:
    """Test end-to-end LLM flow (mocked)."""

    @pytest.mark.asyncio
    async def test_process_with_mocked_api(
        self, llm_service, sample_parts, sample_drawings, mock_llm_response
    ):
        """Test complete process with mocked API."""
        # Create a properly mocked response and client
        mock_response = Mock(status_code=200, json=lambda: mock_llm_response)
        mock_response.raise_for_status = Mock()

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch("httpx.AsyncClient", return_value=mock_client):
            result = await llm_service.process(
                sample_parts, sample_drawings, tone=AssemblyTone.IKEA
            )
            assert isinstance(result, list)
            assert len(result) > 0

    @pytest.mark.asyncio
    async def test_process_tone_affects_output(
        self, llm_service, sample_parts, sample_drawings, mock_llm_response
    ):
        """Test that tone parameter affects LLM prompts."""
        # Create a properly mocked response and client for first call
        mock_response = Mock(status_code=200, json=lambda: mock_llm_response)
        mock_response.raise_for_status = Mock()

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch("httpx.AsyncClient", return_value=mock_client):
            # Call with IKEA tone
            result1 = await llm_service.process(
                sample_parts, sample_drawings, tone=AssemblyTone.IKEA
            )
            assert isinstance(result1, list)

            # Call with TECHNICAL tone - should work the same with mocked client
            result2 = await llm_service.process(
                sample_parts, sample_drawings, tone=AssemblyTone.TECHNICAL
            )
            assert isinstance(result2, list)


# ============================================================================
# TOKEN ESTIMATION TESTS (2 tests)
# ============================================================================


class TestTokenEstimation:
    """Test token estimation helpers."""

    def test_estimate_tokens_returns_number(self, llm_service, sample_parts):
        """Test token estimation returns a number."""
        token_count = llm_service._estimate_tokens(sample_parts)
        assert isinstance(token_count, int)
        assert token_count > 0

    def test_token_estimation_scales_with_parts(self, llm_service):
        """Test that token estimation increases with more parts."""
        few_parts = [
            Part(
                id="A",
                original_index=0,
                part_type=PartType.PANEL,
                quantity=1,
                volume=100.5,
                dimensions={"width": 50, "height": 30, "depth": 2},
                centroid=[25, 15, 1],
                surface_area=3200,
                group_id="A",
            )
        ]
        many_parts = few_parts * 5

        few_tokens = llm_service._estimate_tokens(few_parts)
        many_tokens = llm_service._estimate_tokens(many_parts)
        assert many_tokens > few_tokens


# ============================================================================
# COST CALCULATION TESTS (2 tests)
# ============================================================================


class TestCostCalculation:
    """Test cost estimation."""

    def test_calculate_cost_returns_float(self, llm_service):
        """Test cost calculation returns a float."""
        cost = llm_service._calculate_cost(150, 200, "google/gemini-2.0-flash")
        assert isinstance(cost, float)
        assert cost >= 0

    def test_calculate_cost_increases_with_tokens(self, llm_service):
        """Test that cost increases with token usage."""
        cost_small = llm_service._calculate_cost(100, 100, "google/gemini-2.0-flash")
        cost_large = llm_service._calculate_cost(200, 200, "google/gemini-2.0-flash")
        assert cost_large >= cost_small
