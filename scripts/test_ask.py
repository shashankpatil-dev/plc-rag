#!/usr/bin/env python3
"""
Test the Ask Assistant endpoint
"""
import requests
import json

def test_ask(query, n_examples=2, include_code=True):
    """Test ask endpoint"""
    print(f"\n{'='*60}")
    print(f"Query: {query}")
    print(f"{'='*60}")

    url = "http://localhost:8000/api/v1/ask"
    payload = {
        "query": query,
        "n_examples": n_examples,
        "include_code": include_code
    }

    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()

        data = response.json()

        print(f"\n📝 Answer:")
        print(data['answer'])

        print(f"\n📚 Code Examples ({data['examples_used']} found):")
        for i, ex in enumerate(data['code_examples'], 1):
            print(f"\n  {i}. {ex['machine_name']}")
            print(f"     Similarity: {ex['similarity_score']:.1%}")
            print(f"     States: {ex['state_count']}, Interlocks: {ex['interlock_count']}")
            print(f"     Source: {ex['source_csv']}")

            if ex.get('l5x_preview'):
                preview = ex['l5x_preview'][:300]
                print(f"     L5X Preview: {preview}...")

        return True

    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("Testing Ask Assistant Endpoint\n")

    # Test 1: Specific question about UDT structure
    test_ask("How many timers in UDT_Sequencer?", n_examples=2, include_code=True)

    # Test 2: Pattern question
    test_ask("Show me interlock logic examples", n_examples=2, include_code=False)

    # Test 3: Structure question
    test_ask("How do you structure UDT_Sequencer?", n_examples=1, include_code=True)

    print("\n" + "="*60)
    print("✅ Test Complete!")
    print("="*60)
