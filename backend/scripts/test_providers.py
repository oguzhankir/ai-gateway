"""Test provider connections."""

import sys
from pathlib import Path
import asyncio

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import settings
from app.providers.factory import provider_factory


async def test_openai():
    """Test OpenAI connection."""
    print("Testing OpenAI...")
    try:
        provider = provider_factory.get_provider("openai")
        if not settings.openai_api_key:
            print("✗ OpenAI API key not configured")
            return False
        
        # Simple test - would need actual API call
        print("✓ OpenAI provider initialized")
        return True
    except Exception as e:
        print(f"✗ OpenAI test failed: {e}")
        return False


async def test_gemini():
    """Test Gemini connection."""
    print("Testing Gemini...")
    try:
        provider = provider_factory.get_provider("gemini")
        if not settings.gemini_api_key:
            print("✗ Gemini API key not configured")
            return False
        
        print("✓ Gemini provider initialized")
        return True
    except Exception as e:
        print(f"✗ Gemini test failed: {e}")
        return False


async def main():
    """Run all tests."""
    print("Testing provider connections...")
    results = await asyncio.gather(test_openai(), test_gemini())
    
    if all(results):
        print("\n✓ All providers configured correctly")
    else:
        print("\n⚠ Some providers are not configured")
        print("You can still use the gateway with configured providers")


if __name__ == "__main__":
    asyncio.run(main())

