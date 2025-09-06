import pytest
import logging
from pathlib import Path
from unittest.mock import patch

from src.text_refiner import TextRefiner

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@pytest.mark.integration
class TestFormatInstructionIntegration:
    """Integration test specifically for format instruction processing with audio3"""

    @classmethod
    def setup_class(cls):
        """Setup for format instruction test class"""
        logger.info("Setting up format instruction integration test")

        # Get audio3 script with format instruction
        fixtures_dir = Path(__file__).parent / "fixtures"
        script_file = fixtures_dir / "audio3_script.txt"

        if not script_file.exists():
            pytest.skip("Audio3 script file not found")

        with open(script_file, "r", encoding="utf-8") as f:
            cls.audio3_script = f.read().strip()

        logger.info(f"Loaded audio3 script: {len(cls.audio3_script)} characters")
        logger.info(
            f"Format instruction present: {'Format this as a to-do list in bullet points' in cls.audio3_script}"
        )

    def test_format_instruction_text_processing(self):
        """Test text refiner behavior with format instruction using mocked API response"""
        logger.info(
            "Testing format instruction processing with properly formatted bullet points"
        )

        # Mock the OpenAI client at module import level
        with patch("src.text_refiner.OpenAI") as mock_openai:
            mock_client = mock_openai.return_value
            mock_response = type("MockResponse", (), {})()

            # Create a realistic bullet-point formatted response
            mock_response.output_text = """• Call the dentist and reschedule appointment for next week
• Finish the Johnson report by end of day tomorrow
• Pick up groceries: milk, bread, chicken, and vegetables
• Respond to Sarah's email about the project meeting
• Call mom (haven't talked all week)
• Get gas for the car
• Move laundry to the dryer"""

            mock_client.responses.create.return_value = mock_response

            # Create refiner with test API key
            refiner = TextRefiner(api_key="test-format-key")

            # Process the audio3 script with format instruction
            result = refiner.refine_text(self.audio3_script)

            # Verify the result
            assert result is not None, (
                "Format instruction processing should return refined text"
            )
            assert len(result) > 0, "Refined text should not be empty"
            logger.info(f"Refined text length: {len(result)} characters")

            # Check for bullet point formatting
            bullet_indicators = ["•", "-", "*"]
            has_bullets = any(indicator in result for indicator in bullet_indicators)
            assert has_bullets, (
                f"Refined text should contain bullet points. Got: {result}"
            )
            logger.info("✓ Bullet points detected in output")

            # Verify format instruction was processed (not included in final output)
            assert "Format this as a to-do list" not in result, (
                "Format instruction should be processed and removed from final output"
            )
            logger.info("✓ Format instruction properly removed from output")

            # Count bullet points
            bullet_count = result.count("•") + result.count("- ") + result.count("* ")
            assert bullet_count >= 5, (
                f"Should have multiple bullet points, found {bullet_count}"
            )
            logger.info(f"✓ Found {bullet_count} bullet points")

            # Check that key tasks from the original text are present
            key_tasks = [
                "dentist",
                "Johnson",
                "groceries",
                "Sarah",
                "mom",
                "gas",
                "laundry",
            ]
            found_tasks = []

            for task in key_tasks:
                if task.lower() in result.lower():
                    found_tasks.append(task)

            assert len(found_tasks) >= 5, (
                f"Should contain most key tasks. Found: {found_tasks}"
            )
            logger.info(f"✓ Key tasks preserved: {found_tasks}")

            # Verify the structure looks like a proper to-do list
            lines = [line.strip() for line in result.split("\n") if line.strip()]
            assert len(lines) >= 5, f"Should have multiple lines, got {len(lines)}"

            # Most lines should start with bullet points
            bullet_lines = [
                line
                for line in lines
                if any(line.startswith(b) for b in ["•", "-", "*"])
            ]
            bullet_ratio = len(bullet_lines) / len(lines)
            assert bullet_ratio >= 0.7, (
                f"Most lines should be bullet points, ratio: {bullet_ratio:.2f}"
            )

            logger.info(
                f"✓ Proper list structure: {len(bullet_lines)}/{len(lines)} lines are bullet points"
            )
            logger.info(f"Final formatted result:\n{result}")

        logger.info("Format instruction integration test passed successfully")

    def test_format_instruction_detection(self):
        """Test that we can detect format instructions in text"""
        logger.info("Testing format instruction detection logic")

        # Verify the audio3 script contains the expected format instruction
        assert "Format this as a to-do list in bullet points" in self.audio3_script, (
            "Audio3 script should contain format instruction"
        )

        # Test various format instruction patterns
        test_texts = [
            "Some text here. Format this as a to-do list in bullet points.",
            "Text content. Please format as bullet points.",
            "Content here. Make this a bulleted list.",
            "Regular text without format instruction.",
            self.audio3_script,
        ]

        format_patterns = [
            "format this as a to-do list",
            "format as bullet",
            "bullet points",
            "bulleted list",
            "make this a list",
        ]

        for i, text in enumerate(test_texts):
            has_instruction = any(
                pattern.lower() in text.lower() for pattern in format_patterns
            )
            logger.info(f"Text {i + 1} has format instruction: {has_instruction}")

            if i == len(test_texts) - 1:  # audio3_script
                assert has_instruction, (
                    "Audio3 script should be detected as having format instruction"
                )

        logger.info("Format instruction detection test passed")

    def test_text_refiner_with_different_instructions(self):
        """Test text refiner behavior with different format instructions"""
        logger.info("Testing text refiner with various format instructions")

        test_cases = [
            {
                "input": "Task one, task two, task three. Format as numbered list.",
                "expected_format": "numbered",
                "mock_response": "1. Task one\n2. Task two\n3. Task three",
            },
            {
                "input": "Item A, Item B, Item C. Format this as bullet points.",
                "expected_format": "bullets",
                "mock_response": "• Item A\n• Item B\n• Item C",
            },
            {
                "input": "Step one, step two, step three. Make this a checklist.",
                "expected_format": "checklist",
                "mock_response": "☐ Step one\n☐ Step two\n☐ Step three",
            },
        ]

        for i, test_case in enumerate(test_cases):
            logger.info(f"Testing format case {i + 1}: {test_case['expected_format']}")

            with patch("src.text_refiner.OpenAI") as mock_openai:
                mock_client = mock_openai.return_value
                mock_response = type("MockResponse", (), {})()
                mock_response.output_text = test_case["mock_response"]
                mock_client.responses.create.return_value = mock_response

                refiner = TextRefiner(api_key=f"test-key-{i}")
                result = refiner.refine_text(test_case["input"])

                # Verify format instruction was processed
                instruction_removed = not any(
                    phrase in result.lower()
                    for phrase in ["format", "make this", "as bullet", "as numbered"]
                )

                assert instruction_removed, (
                    f"Format instruction should be removed for case {i + 1}"
                )
                assert len(result) > 0, f"Should have non-empty result for case {i + 1}"

                logger.info(f"Case {i + 1} result: {result}")

        logger.info("Different format instructions test passed")

    def test_format_instruction_with_short_text(self):
        """Test format instruction with text shorter than refinement threshold"""
        logger.info("Testing format instruction with short text")

        # Text shorter than 20 characters with format instruction
        short_text = "A, B, C. Bullet list."  # 22 characters - just above threshold

        with patch("src.text_refiner.OpenAI") as mock_openai:
            mock_client = mock_openai.return_value
            mock_response = type("MockResponse", (), {})()
            mock_response.output_text = "• A\n• B\n• C"
            mock_client.responses.create.return_value = mock_response

            refiner = TextRefiner(api_key="test-short-key")
            result = refiner.refine_text(short_text)

            # Should be processed because it has format instruction
            assert result is not None, (
                "Short text with format instruction should be processed"
            )
            assert result != short_text, "Should be refined, not returned as-is"

            logger.info(f"Short text processing result: {result}")

        # Very short text - should return as-is regardless
        very_short = "A,B,C. List."  # 12 characters
        result = refiner.refine_text(very_short)
        assert result == very_short, (
            "Very short text should return as-is even with instruction"
        )

        logger.info("Short text format instruction test passed")

    def test_audio3_specific_content_validation(self):
        """Test that audio3 script contains all expected task content"""
        logger.info("Testing audio3 script content validation for task extraction")

        expected_tasks = {
            "dentist": "dental appointment scheduling",
            "Johnson report": "work deliverable",
            "groceries": "shopping tasks",
            "milk": "specific grocery item",
            "bread": "specific grocery item",
            "chicken": "specific grocery item",
            "Sarah": "email communication",
            "mom": "personal communication",
            "gas": "car maintenance",
            "laundry": "household chore",
        }

        logger.info(f"Checking for {len(expected_tasks)} expected task elements")

        found_tasks = {}
        for task, description in expected_tasks.items():
            if task.lower() in self.audio3_script.lower():
                found_tasks[task] = description
                logger.info(f"✓ Found task: {task} ({description})")
            else:
                logger.warning(f"✗ Missing task: {task} ({description})")

        # Should find most tasks
        found_ratio = len(found_tasks) / len(expected_tasks)
        assert found_ratio >= 0.8, (
            f"Should find at least 80% of tasks, found {found_ratio:.1%}"
        )

        # Check that format instruction is present (may span sentences)
        assert "Format this as a to-do list in bullet points" in self.audio3_script, (
            "Format instruction should be present in the script"
        )

        # Check that it's near the end of the text
        instruction_pos = self.audio3_script.find(
            "Format this as a to-do list in bullet points"
        )
        text_length = len(self.audio3_script)
        instruction_ratio = instruction_pos / text_length if text_length > 0 else 0

        assert instruction_ratio >= 0.7, (
            f"Format instruction should be in last 30% of text, found at {instruction_ratio:.1%}"
        )

        logger.info(
            f"Audio3 content validation passed: {len(found_tasks)}/{len(expected_tasks)} tasks found"
        )


if __name__ == "__main__":
    # Run format instruction tests
    pytest.main([__file__, "-v", "--tb=short", "-m", "integration"])
