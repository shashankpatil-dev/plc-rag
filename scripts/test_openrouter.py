#!/usr/bin/env python3
"""
Test OpenRouter Connection
Verify both code generation and embeddings work correctly
"""
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_generation():
    """Test Claude Sonnet code generation via OpenRouter"""
    print("=" * 60)
    print("TEST 1: Code Generation (Claude Sonnet 3.5)")
    print("=" * 60)

    api_key = os.getenv("OPENROUTER_API_KEY")
    model = os.getenv("OPENROUTER_MODEL", "anthropic/claude-3.5-sonnet")

    if not api_key:
        print("❌ OPENROUTER_API_KEY not found in .env")
        return False

    try:
        client = OpenAI(
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1"
        )

        print(f"Model: {model}")
        print("Sending test prompt...")

        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": "You are a PLC programming expert."
                },
                {
                    "role": "user",
                    "content": "Generate a simple ladder logic rung for an emergency stop check in L5X format."
                }
            ],
            max_tokens=200,
            temperature=0.1
        )

        result = response.choices[0].message.content
        print("\n✅ Generation successful!")
        print(f"\nResponse ({len(result)} chars):")
        print("-" * 60)
        print(result[:500])  # First 500 chars
        print("-" * 60)

        # Check token usage
        if hasattr(response, 'usage'):
            usage = response.usage
            print(f"\nToken Usage:")
            print(f"  Input:  {usage.prompt_tokens}")
            print(f"  Output: {usage.completion_tokens}")
            print(f"  Total:  {usage.total_tokens}")

        return True

    except Exception as e:
        print(f"\n❌ Generation failed: {e}")
        return False


def test_embeddings():
    """Test OpenAI embeddings via OpenRouter"""
    print("\n" + "=" * 60)
    print("TEST 2: Embeddings (text-embedding-3-small)")
    print("=" * 60)

    api_key = os.getenv("OPENROUTER_API_KEY")
    embedding_model = os.getenv("OPENROUTER_EMBEDDING_MODEL", "openai/text-embedding-3-small")

    if not api_key:
        print("❌ OPENROUTER_API_KEY not found in .env")
        return False

    try:
        client = OpenAI(
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1"
        )

        print(f"Model: {embedding_model}")
        print("Creating test embedding...")

        test_text = "Safety interlock logic: IF NOT EStop AND Door_Closed THEN Safety_OK"

        response = client.embeddings.create(
            model=embedding_model,
            input=test_text
        )

        embedding = response.data[0].embedding
        dimensions = len(embedding)

        print(f"\n✅ Embedding successful!")
        print(f"\nDimensions: {dimensions}")
        print(f"Expected:   1536")

        if dimensions == 1536:
            print("✅ Dimension check passed")
        else:
            print(f"⚠️  Warning: Expected 1536 dimensions, got {dimensions}")

        print(f"\nFirst 10 values:")
        print(embedding[:10])

        return True

    except Exception as e:
        print(f"\n❌ Embedding failed: {e}")
        return False


def test_cost_estimation():
    """Estimate costs for typical usage"""
    print("\n" + "=" * 60)
    print("TEST 3: Cost Estimation")
    print("=" * 60)

    # Pricing (as of Feb 2026)
    SONNET_INPUT_COST = 3.00 / 1_000_000    # $3 per 1M tokens
    SONNET_OUTPUT_COST = 15.00 / 1_000_000  # $15 per 1M tokens
    EMBEDDING_COST = 0.02 / 1_000_000       # $0.02 per 1M tokens

    print("\n📊 Pricing:")
    print(f"  Claude Sonnet Input:  ${SONNET_INPUT_COST * 1_000_000:.2f}/1M tokens")
    print(f"  Claude Sonnet Output: ${SONNET_OUTPUT_COST * 1_000_000:.2f}/1M tokens")
    print(f"  Embeddings:           ${EMBEDDING_COST * 1_000_000:.4f}/1M tokens")

    print("\n📈 Estimated Costs:")

    # 2,500-line L5X file
    routines_2500 = 14
    input_per_routine = 5000
    output_per_routine = 2000

    total_input = routines_2500 * input_per_routine
    total_output = routines_2500 * output_per_routine

    cost_2500 = (total_input * SONNET_INPUT_COST) + (total_output * SONNET_OUTPUT_COST)

    print(f"\n  2,500-line file:")
    print(f"    Routines:     {routines_2500}")
    print(f"    Input tokens: {total_input:,}")
    print(f"    Output tokens: {total_output:,}")
    print(f"    Cost:         ${cost_2500:.2f}")

    # 10,000-line L5X file
    routines_10k = 60
    total_input_10k = routines_10k * input_per_routine
    total_output_10k = routines_10k * output_per_routine

    cost_10k = (total_input_10k * SONNET_INPUT_COST) + (total_output_10k * SONNET_OUTPUT_COST)

    print(f"\n  10,000-line file:")
    print(f"    Routines:     {routines_10k}")
    print(f"    Input tokens: {total_input_10k:,}")
    print(f"    Output tokens: {total_output_10k:,}")
    print(f"    Cost:         ${cost_10k:.2f}")

    # Monthly costs
    files_per_month = 100
    monthly_cost_avg = files_per_month * ((cost_2500 + cost_10k) / 2)

    print(f"\n  Monthly (100 files, avg size):")
    print(f"    Cost:         ${monthly_cost_avg:.2f}")

    # Initial embedding setup
    routines_to_embed = 200
    tokens_per_routine = 500
    embedding_setup_cost = (routines_to_embed * tokens_per_routine) * EMBEDDING_COST

    print(f"\n  One-time embedding setup:")
    print(f"    Routines:     {routines_to_embed}")
    print(f"    Tokens:       {routines_to_embed * tokens_per_routine:,}")
    print(f"    Cost:         ${embedding_setup_cost:.4f}")

    print("\n✅ Cost analysis complete")
    return True


def main():
    """Run all tests"""
    print("\n🧪 OpenRouter Connection Test Suite\n")

    results = []

    # Test 1: Generation
    results.append(("Code Generation", test_generation()))

    # Test 2: Embeddings
    results.append(("Embeddings", test_embeddings()))

    # Test 3: Cost estimation
    results.append(("Cost Estimation", test_cost_estimation()))

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}  {test_name}")

    all_passed = all(result[1] for result in results)

    if all_passed:
        print("\n🎉 All tests passed! OpenRouter is ready to use.")
        print("\nNext steps:")
        print("  1. Parse L5X files: python scripts/parse_l5x_files.py")
        print("  2. Build IR layer: See IMPLEMENTATION_PLAN.md Phase 1")
        return 0
    else:
        print("\n⚠️  Some tests failed. Check your .env configuration.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
