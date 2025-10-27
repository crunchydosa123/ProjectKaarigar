"""
Test Suite for Reel Ideas Generator Module
Tests all API methods of ReelIdeasGenerator class
"""

import os
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict

# Import the ReelIdeasGenerator class
from reel_ideas_generator import ReelIdeasGenerator


class Colors:
    """ANSI color codes for terminal output"""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def print_header(title: str):
    """Print formatted test header"""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*80}")
    print(f"  {title}")
    print(f"{'='*80}{Colors.ENDC}\n")


def print_success(message: str, details: Dict = None):
    """Print success message"""
    print(f"{Colors.OKGREEN}✅ {message}{Colors.ENDC}")
    if details:
        for key, value in details.items():
            if isinstance(value, list):
                print(f"   {key}:")
                for item in value:
                    print(f"     • {item}")
            else:
                print(f"   {key}: {value}")


def print_error(message: str, details: Dict = None):
    """Print error message"""
    print(f"{Colors.FAIL}❌ {message}{Colors.ENDC}")
    if details:
        for key, value in details.items():
            print(f"   {key}: {value}")


def print_warning(message: str):
    """Print warning message"""
    print(f"{Colors.WARNING}⚠️  {message}{Colors.ENDC}")


def print_info(message: str):
    """Print info message"""
    print(f"{Colors.OKCYAN}ℹ️  {message}{Colors.ENDC}")


# ==================== TEST CASES ====================

def test_1_generate_ideas_basic():
    """TEST 1: Generate ideas from basic text prompt"""
    print_header("TEST 1: Generate Ideas from Text Prompt")
    
    generator = ReelIdeasGenerator()
    
    test_prompt = "A product launch event with excitement and celebration"
    
    print_info(f"Testing with prompt: '{test_prompt}'")
    print_info("Requesting 5 unique ideas...")
    
    result = generator.generate_ideas(
        initial_prompt=test_prompt,
        num_ideas=5
    )
    
    print(f"\nResponse:")
    if result.get("success"):
        print_success("Ideas generated successfully", {
            "Total Ideas": result.get("count"),
            "Source Prompt": result.get("prompt")
        })
        
        ideas = result.get("ideas", [])
        print("\n📋 Generated Ideas:")
        for idx, idea in enumerate(ideas, 1):
            word_count = len(idea.split())
            status = "✓" if word_count <= 30 else "⚠"
            print(f"   {idx}. [{status} {word_count} words] {idea}")
        
        return True
    else:
        print_error("Failed to generate ideas", {
            "Error": result.get("error")
        })
        return False


def test_2_generate_ideas_with_image():
    """TEST 2: Generate ideas from text prompt + image context"""
    print_header("TEST 2: Generate Ideas with Image Context")
    
    generator = ReelIdeasGenerator()
    
    # Check for test image
    image_path = r"D:\Barclays\ProjectKaarigar\Model\images (1).jpeg"
    
    if not os.path.exists(image_path):
        print_warning(f"Test image not found: {image_path}")
        print_info("Skipping image context test (image-based tests require actual images)")
        return None
    
    test_prompt = "Create a video showcasing this product"
    
    print_info(f"Image: {Path(image_path).name}")
    print_info(f"Prompt: '{test_prompt}'")
    
    result = generator.generate_ideas(
        initial_prompt=test_prompt,
        image_path=image_path,
        num_ideas=3
    )
    
    if result.get("success"):
        print_success("Ideas with image context generated", {
            "Total Ideas": result.get("count")
        })
        
        ideas = result.get("ideas", [])
        print("\n📋 Generated Ideas:")
        for idx, idea in enumerate(ideas, 1):
            print(f"   {idx}. {idea}")
        
        return True
    else:
        print_error("Failed to generate ideas with image", {
            "Error": result.get("error")
        })
        return False


def test_3_refine_idea():
    """TEST 3: Refine a chosen idea"""
    print_header("TEST 3: Refine Idea with User Feedback")
    
    generator = ReelIdeasGenerator()
    
    # First generate an idea to refine
    print_info("Step 1: Generating initial idea...")
    initial_result = generator.generate_ideas("Sunset landscape", num_ideas=1)
    
    if not initial_result.get("success"):
        print_error("Failed to generate initial idea")
        return False
    
    chosen_idea = initial_result.get("ideas", [])[0]
    print_success("Initial idea generated", {"Idea": chosen_idea})
    
    # Now refine it
    print_info("\nStep 2: Refining the idea...")
    refinement_request = "Make it more dramatic and cinematic with dramatic lighting"
    
    refine_result = generator.refine_idea(
        chosen_idea=chosen_idea,
        refinement_prompt=refinement_request
    )
    
    if refine_result.get("success"):
        print_success("Idea refined successfully", {
            "Original": refine_result.get("original_idea"),
            "Refined": refine_result.get("refined_idea"),
            "Word Count": refine_result.get("word_count"),
            "Refinement Applied": refine_result.get("refinement_applied")
        })
        return True
    else:
        print_error("Failed to refine idea", {
            "Error": refine_result.get("error")
        })
        return False


def test_4_regenerate_ideas():
    """TEST 4: Regenerate ideas with new feedback"""
    print_header("TEST 4: Regenerate Ideas with New Direction")
    
    generator = ReelIdeasGenerator()
    
    feedback = "Generate tech-focused content ideas with innovation and futuristic elements"
    
    print_info(f"Regeneration feedback: '{feedback}'")
    print_info("Requesting 4 completely new ideas...")
    
    result = generator.regenerate_ideas(
        regeneration_prompt=feedback,
        num_ideas=4
    )
    
    if result.get("success"):
        print_success("Ideas regenerated successfully", {
            "Total Ideas": result.get("count"),
            "Context": result.get("regeneration_context")
        })
        
        ideas = result.get("ideas", [])
        print("\n📋 Regenerated Ideas:")
        for idx, idea in enumerate(ideas, 1):
            word_count = len(idea.split())
            print(f"   {idx}. [{word_count} words] {idea}")
        
        return True
    else:
        print_error("Failed to regenerate ideas", {
            "Error": result.get("error")
        })
        return False


def test_5_generate_video_script():
    """TEST 5: Generate optimized video script from idea"""
    print_header("TEST 5: Generate Video Script from Idea")
    
    generator = ReelIdeasGenerator()
    
    # First generate an idea
    print_info("Step 1: Generating initial idea...")
    idea_result = generator.generate_ideas("Urban street photography", num_ideas=1)
    
    if not idea_result.get("success"):
        print_error("Failed to generate initial idea")
        return False
    
    chosen_idea = idea_result.get("ideas", [])[0]
    print_success("Idea generated", {"Idea": chosen_idea})
    
    # Generate video script
    print_info("\nStep 2: Generating optimized video script...")
    script_result = generator.generate_video_script(reel_idea=chosen_idea)
    
    if script_result.get("success"):
        print_success("Video script generated", {
            "Original Idea": script_result.get("reel_idea"),
            "Word Count": script_result.get("word_count"),
            "Model": script_result.get("model")
        })
        
        print("\n📝 Generated Script:")
        script = script_result.get("script", "")
        print(f"{Colors.OKBLUE}{script}{Colors.ENDC}")
        
        return True
    else:
        print_error("Failed to generate video script", {
            "Error": script_result.get("error")
        })
        return False


def test_6_batch_generate_ideas():
    """TEST 6: Batch generate ideas for multiple prompts"""
    print_header("TEST 6: Batch Generate Ideas for Multiple Prompts")
    
    generator = ReelIdeasGenerator()
    
    prompts = [
        "Luxury fashion collection launch",
        "Tech startup innovation showcase",
        "Sustainable lifestyle product"
    ]
    
    print_info(f"Processing {len(prompts)} prompts in batch mode...")
    print_info("Generating 3 ideas per prompt...\n")
    
    result = generator.batch_generate_ideas(
        prompts=prompts,
        num_ideas=3
    )
    
    if result.get("success"):
        print_success("Batch generation completed", {
            "Total Prompts": result.get("total_prompts")
        })
        
        results = result.get("results", [])
        for prompt_idx, prompt_result in enumerate(results, 1):
            print(f"\n📌 Prompt {prompt_idx}: {prompt_result.get('prompt')}")
            
            if prompt_result.get("success"):
                ideas = prompt_result.get("ideas", [])
                for idea_idx, idea in enumerate(ideas, 1):
                    print(f"   {idea_idx}. {idea}")
            else:
                print_warning("Failed to generate ideas for this prompt")
        
        return True
    else:
        print_error("Failed batch generation", {
            "Error": result.get("error")
        })
        return False


def test_7_edge_cases():
    """TEST 7: Edge cases and error handling"""
    print_header("TEST 7: Edge Cases & Error Handling")
    
    generator = ReelIdeasGenerator()
    test_passed = True
    
    # Test 7a: Empty prompt
    print_info("Test 7a: Empty prompt handling...")
    result = generator.generate_ideas(initial_prompt="", num_ideas=3)
    
    if not result.get("success") and "empty" in result.get("error", "").lower():
        print_success("Empty prompt correctly rejected")
    else:
        print_error("Empty prompt should be rejected")
        test_passed = False
    
    # Test 7b: Whitespace-only prompt
    print_info("\nTest 7b: Whitespace-only prompt handling...")
    result = generator.generate_ideas(initial_prompt="   ", num_ideas=3)
    
    if not result.get("success"):
        print_success("Whitespace-only prompt correctly rejected")
    else:
        print_error("Whitespace-only prompt should be rejected")
        test_passed = False
    
    # Test 7c: Very long prompt (should still work)
    print_info("\nTest 7c: Very long prompt handling...")
    long_prompt = "Create a video about " + "innovative products " * 20
    result = generator.generate_ideas(initial_prompt=long_prompt, num_ideas=2)
    
    if result.get("success"):
        print_success("Long prompt handled successfully", {
            "Character Count": len(long_prompt),
            "Ideas Generated": result.get("count")
        })
    else:
        print_warning("Long prompt resulted in error (may be API limit)")
    
    # Test 7d: Zero ideas requested
    print_info("\nTest 7d: Zero ideas requested...")
    result = generator.generate_ideas(initial_prompt="Test prompt", num_ideas=0)
    
    if result.get("success") and result.get("count") == 0:
        print_success("Zero ideas request handled correctly")
    else:
        print_warning("Zero ideas behavior may need adjustment")
    
    # Test 7e: Very high number of ideas
    print_info("\nTest 7e: High idea count request (10 ideas)...")
    result = generator.generate_ideas(initial_prompt="Test prompt", num_ideas=10)
    
    if result.get("success"):
        print_success("High count request handled", {
            "Requested": 10,
            "Generated": result.get("count")
        })
    else:
        print_warning("High count may have triggered rate limit or API error")
    
    return test_passed


def test_8_validation_methods():
    """TEST 8: Validation helper methods"""
    print_header("TEST 8: Validation Helper Methods")
    
    generator = ReelIdeasGenerator()
    
    # Test _validate_prompt
    print_info("Testing _validate_prompt method...")
    
    test_cases = [
        ("Valid prompt", True),
        ("", False),
        ("   ", False),
        ("Hi", False),  # Too short
        ("This is a valid prompt", True),
    ]
    
    all_passed = True
    for prompt, expected in test_cases:
        result = generator._validate_prompt(prompt)
        status = "✓" if result == expected else "✗"
        print(f"   {status} '{prompt}' -> {result} (expected {expected})")
        if result != expected:
            all_passed = False
    
    if all_passed:
        print_success("All validation tests passed")
    else:
        print_error("Some validation tests failed")
    
    return all_passed


def test_9_json_parsing():
    """TEST 9: JSON parsing with various formats"""
    print_header("TEST 9: JSON Parsing Robustness")
    
    generator = ReelIdeasGenerator()
    
    test_cases = [
        # Valid JSON
        ('{"ideas": ["idea1", "idea2", "idea3"]}', 3, True),
        # JSON with extra whitespace
        ('  {"ideas": ["idea1", "idea2"]}  ', 2, True),
        # JSON with newlines
        ('{\n  "ideas": [\n    "idea1",\n    "idea2"\n  ]\n}', 2, True),
        # Invalid JSON (should fallback)
        ('Not valid JSON at all', 0, False),
        # Empty ideas array
        ('{"ideas": []}', 0, True),
    ]
    
    print_info("Testing JSON parsing with various formats...\n")
    
    for idx, (test_json, expected_count, should_succeed) in enumerate(test_cases, 1):
        preview = test_json[:40] + "..." if len(test_json) > 40 else test_json
        print_info(f"Test case {idx}: {preview}")
        
        result = generator._parse_json_ideas(test_json)
        actual_count = len(result)
        
        if (actual_count == expected_count) == should_succeed:
            print_success(f"Parsed correctly: {actual_count} ideas extracted")
        else:
            print_error(f"Parse failed: got {actual_count}, expected {expected_count}")
        print()


# ==================== TEST SUITE RUNNER ====================

def run_all_tests():
    """Run complete test suite"""
    print(f"{Colors.BOLD}{Colors.HEADER}")
    print("=" * 80)
    print("  🎬 REEL IDEAS GENERATOR - COMPREHENSIVE TEST SUITE")
    print("=" * 80)
    print(f"{Colors.ENDC}")
    
    start_time = datetime.now()
    test_results = {}
    
    # Run all tests
    tests = [
        ("Generate Ideas - Basic", test_1_generate_ideas_basic),
        ("Generate Ideas - With Image", test_2_generate_ideas_with_image),
        ("Refine Idea", test_3_refine_idea),
        ("Regenerate Ideas", test_4_regenerate_ideas),
        ("Generate Video Script", test_5_generate_video_script),
        ("Batch Generate Ideas", test_6_batch_generate_ideas),
        ("Edge Cases", test_7_edge_cases),
        ("Validation Methods", test_8_validation_methods),
        ("JSON Parsing", test_9_json_parsing),
    ]
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            test_results[test_name] = result
        except Exception as e:
            print_error(f"Test crashed: {str(e)}")
            test_results[test_name] = False
    
    # Print summary
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    print_header("TEST SUMMARY")
    
    passed = sum(1 for v in test_results.values() if v is True)
    failed = sum(1 for v in test_results.values() if v is False)
    skipped = sum(1 for v in test_results.values() if v is None)
    
    print(f"{Colors.BOLD}Results:{Colors.ENDC}")
    for test_name, result in test_results.items():
        if result is True:
            status = f"{Colors.OKGREEN}PASSED{Colors.ENDC}"
        elif result is False:
            status = f"{Colors.FAIL}FAILED{Colors.ENDC}"
        else:
            status = f"{Colors.WARNING}SKIPPED{Colors.ENDC}"
        
        print(f"  {status} - {test_name}")
    
    print(f"\n{Colors.BOLD}Summary:{Colors.ENDC}")
    print(f"  Total Tests: {len(tests)}")
    print(f"  {Colors.OKGREEN}Passed: {passed}{Colors.ENDC}")
    print(f"  {Colors.FAIL}Failed: {failed}{Colors.ENDC}")
    print(f"  {Colors.WARNING}Skipped: {skipped}{Colors.ENDC}")
    print(f"  Duration: {duration:.2f}s")
    
    print(f"\n{Colors.BOLD}{Colors.HEADER}{'='*80}{Colors.ENDC}\n")
    
    return passed, failed, skipped


if __name__ == "__main__":
    print("\n🚀 Starting Test Suite...\n")
    passed, failed, skipped = run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if failed == 0 else 1)