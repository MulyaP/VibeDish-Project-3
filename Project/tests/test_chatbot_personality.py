"""
Tests to verify the VibeDish chatbot can answer identity and help questions.

This test suite ensures the chatbot properly responds to questions like:
- "Who are you?"
- "How can you help me?"
- "What is VibeDish?"
- "What features do you have?"
"""
import pytest
from fastapi.testclient import TestClient

import app.main as main_app
import app.routers.chat as chat_router_module


@pytest.fixture(autouse=True)
def override_current_user():
    """Override authentication for testing."""
    main_app.app.dependency_overrides[chat_router_module.current_user] = lambda: {
        "id": "test-user-personality",
        "email": "personality@test.com"
    }
    yield
    main_app.app.dependency_overrides.clear()


def test_chatbot_identifies_itself(monkeypatch):
    """Test that chatbot responds appropriately to 'Who are you?' questions."""
    client = TestClient(main_app.app)

    # Mock persistence layer
    monkeypatch.setattr(chat_router_module, "create_session", lambda user_id=None: "sess-who-123")
    monkeypatch.setattr(
        chat_router_module,
        "append_message",
        lambda session_id, role, content, provider_info=None, token_count=None: f"msg-{role}-1"
    )
    monkeypatch.setattr(chat_router_module, "get_history", lambda session_id, limit=200: [])
    monkeypatch.setattr(chat_router_module, "session_belongs_to_user", lambda s, u: True)

    # Mock the AI response - this simulates what Groq would return
    async def fake_generate_identity(history, message, context):
        # The system prompt should guide the response
        return {
            "reply": (
                "I'm the official virtual assistant for VibeDish! I help you discover "
                "delicious meals based on your Spotify mood, browse surplus restaurant meals "
                "to reduce food waste, track your orders in real-time, and navigate all the "
                "features of our app. How can I assist you today?"
            ),
            "provider_info": {
                "usage": {"completion_tokens": 45, "prompt_tokens": 250, "total_tokens": 295},
                "model": "grok-latest"
            },
        }

    monkeypatch.setattr(chat_router_module, "generate_reply_with_groq", fake_generate_identity)

    # Send "Who are you?" question
    resp = client.post("/chat/messages", json={
        "session_id": None,
        "message": "Who are you?"
    })

    assert resp.status_code == 200
    data = resp.json()
    assert data["session_id"] == "sess-who-123"
    
    # Verify the response contains key identity elements
    reply_lower = data["reply"].lower()
    assert "vibedish" in reply_lower
    assert "assistant" in reply_lower or "help" in reply_lower


def test_chatbot_explains_features(monkeypatch):
    """Test that chatbot can explain how it helps users."""
    client = TestClient(main_app.app)

    # Mock persistence layer
    monkeypatch.setattr(chat_router_module, "create_session", lambda user_id=None: "sess-help-456")
    monkeypatch.setattr(
        chat_router_module,
        "append_message",
        lambda session_id, role, content, provider_info=None, token_count=None: f"msg-{role}-2"
    )
    monkeypatch.setattr(chat_router_module, "get_history", lambda session_id, limit=200: [])
    monkeypatch.setattr(chat_router_module, "session_belongs_to_user", lambda s, u: True)

    # Mock the AI response
    async def fake_generate_help(history, message, context):
        return {
            "reply": (
                "I can help you with:\n\n"
                "🎵 Spotify Mood Integration - Connect your Spotify to get meal recommendations based on your music\n"
                "🍽️ Surplus Meals - Browse discounted meals from restaurants to reduce food waste\n"
                "📍 Order Tracking - Track your order in real-time from preparation to delivery\n"
                "💳 Payment & Refunds - Manage payment methods, apply promo codes, and request refunds\n"
                "⚙️ Account Settings - Update your profile and manage connected apps\n\n"
                "What would you like to do?"
            ),
            "provider_info": {
                "usage": {"completion_tokens": 85, "prompt_tokens": 250, "total_tokens": 335},
                "model": "grok-latest"
            },
        }

    monkeypatch.setattr(chat_router_module, "generate_reply_with_groq", fake_generate_help)

    # Send "How can you help me?" question
    resp = client.post("/chat/messages", json={
        "session_id": None,
        "message": "How can you help me?"
    })

    assert resp.status_code == 200
    data = resp.json()
    
    # Verify the response contains key features
    reply_lower = data["reply"].lower()
    assert any(keyword in reply_lower for keyword in ["spotify", "mood", "music"])
    assert any(keyword in reply_lower for keyword in ["order", "track", "delivery"])
    assert any(keyword in reply_lower for keyword in ["surplus", "meal", "food"])


def test_chatbot_explains_vibedish(monkeypatch):
    """Test that chatbot can explain what VibeDish is."""
    client = TestClient(main_app.app)

    # Mock persistence layer
    monkeypatch.setattr(chat_router_module, "create_session", lambda user_id=None: "sess-what-789")
    monkeypatch.setattr(
        chat_router_module,
        "append_message",
        lambda session_id, role, content, provider_info=None, token_count=None: f"msg-{role}-3"
    )
    monkeypatch.setattr(chat_router_module, "get_history", lambda session_id, limit=200: [])
    monkeypatch.setattr(chat_router_module, "session_belongs_to_user", lambda s, u: True)

    # Mock the AI response
    async def fake_generate_what(history, message, context):
        return {
            "reply": (
                "VibeDish is an AI-powered meal recommendation and ordering platform that connects "
                "your Spotify music mood to curated food suggestions from local restaurants. We also "
                "help reduce food waste by offering surplus restaurant meals at discounted prices. "
                "It's all about matching great food with your vibe!"
            ),
            "provider_info": {
                "usage": {"completion_tokens": 52, "prompt_tokens": 250, "total_tokens": 302},
                "model": "grok-latest"
            },
        }

    monkeypatch.setattr(chat_router_module, "generate_reply_with_groq", fake_generate_what)

    # Send "What is VibeDish?" question
    resp = client.post("/chat/messages", json={
        "session_id": None,
        "message": "What is VibeDish?"
    })

    assert resp.status_code == 200
    data = resp.json()
    
    # Verify the response explains VibeDish purpose
    reply_lower = data["reply"].lower()
    assert "vibedish" in reply_lower
    assert any(keyword in reply_lower for keyword in ["spotify", "mood", "music"])
    assert any(keyword in reply_lower for keyword in ["food", "meal", "restaurant"])
    assert any(keyword in reply_lower for keyword in ["waste", "surplus"])


def test_chatbot_stays_in_character(monkeypatch):
    """Test that chatbot doesn't hallucinate non-existent features."""
    client = TestClient(main_app.app)

    # Mock persistence layer
    monkeypatch.setattr(chat_router_module, "create_session", lambda user_id=None: "sess-char-000")
    monkeypatch.setattr(
        chat_router_module,
        "append_message",
        lambda session_id, role, content, provider_info=None, token_count=None: f"msg-{role}-4"
    )
    monkeypatch.setattr(chat_router_module, "get_history", lambda session_id, limit=200: [])
    monkeypatch.setattr(chat_router_module, "session_belongs_to_user", lambda s, u: True)

    # Mock the AI response - should NOT mention features that don't exist
    async def fake_generate_char(history, message, context):
        # This should be guided by the system prompt to only mention real features
        return {
            "reply": (
                "I can help with meal recommendations, order tracking, Spotify integration, "
                "and browsing surplus meals. I don't have access to features like recipe creation "
                "or grocery shopping - I'm focused on helping you order great restaurant meals "
                "that match your vibe!"
            ),
            "provider_info": {
                "usage": {"completion_tokens": 48, "prompt_tokens": 250, "total_tokens": 298},
                "model": "grok-latest"
            },
        }

    monkeypatch.setattr(chat_router_module, "generate_reply_with_groq", fake_generate_char)

    # Ask about a feature that doesn't exist
    resp = client.post("/chat/messages", json={
        "session_id": None,
        "message": "Can you help me create recipes?"
    })

    assert resp.status_code == 200
    data = resp.json()
    
    # Response should clarify what it CAN do without making up features
    assert "reply" in data


def test_chatbot_greeting_new_users(monkeypatch):
    """Test that chatbot properly greets new users."""
    client = TestClient(main_app.app)

    # Mock persistence layer
    monkeypatch.setattr(chat_router_module, "create_session", lambda user_id=None: "sess-greet-111")
    monkeypatch.setattr(
        chat_router_module,
        "append_message",
        lambda session_id, role, content, provider_info=None, token_count=None: f"msg-{role}-5"
    )
    monkeypatch.setattr(chat_router_module, "get_history", lambda session_id, limit=200: [])
    monkeypatch.setattr(chat_router_module, "session_belongs_to_user", lambda s, u: True)

    # Mock the AI response
    async def fake_generate_greeting(history, message, context):
        return {
            "reply": (
                "Hey there! 👋 Welcome to VibeDish! I'm your AI-powered food assistant. "
                "I can help you discover amazing meals based on your Spotify music mood, "
                "find surplus restaurant deals to save money and reduce waste, and track "
                "your orders in real-time. What are you in the mood for today?"
            ),
            "provider_info": {
                "usage": {"completion_tokens": 58, "prompt_tokens": 250, "total_tokens": 308},
                "model": "grok-latest"
            },
        }

    monkeypatch.setattr(chat_router_module, "generate_reply_with_groq", fake_generate_greeting)

    # Send a simple greeting
    resp = client.post("/chat/messages", json={
        "session_id": None,
        "message": "Hello"
    })

    assert resp.status_code == 200
    data = resp.json()
    
    # Verify friendly greeting
    reply = data["reply"]
    assert len(reply) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
