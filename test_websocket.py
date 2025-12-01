#!/usr/bin/env python3
"""
Simple WebSocket test script to verify the speech endpoint is working.
This tests the WebSocket connection without requiring audio input.
"""
import asyncio
import websockets
import json

async def test_websocket():
    """Test the WebSocket speech endpoint."""
    uri = "ws://localhost:8000/ws/speech"
    
    try:
        print(f"Connecting to {uri}...")
        async with websockets.connect(uri) as websocket:
            print("✅ WebSocket connected successfully!")
            
            # Send a reset message
            reset_msg = {"type": "reset"}
            await websocket.send(json.dumps(reset_msg))
            print("✅ Sent reset message")
            
            # Wait for any response
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                print(f"✅ Received response: {response}")
            except asyncio.TimeoutError:
                print("ℹ️  No immediate response (this is normal)")
            
            # Send an end message (simulating end of recording)
            end_msg = {"type": "end"}
            await websocket.send(json.dumps(end_msg))
            print("✅ Sent end message")
            
            # Wait a bit for any final response
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=3.0)
                message = json.loads(response)
                print(f"✅ Received message: {message.get('type', 'unknown')}")
                if message.get('type') == 'error':
                    print(f"   Error: {message.get('message')}")
                elif message.get('type') == 'final_transcript':
                    print(f"   Transcript: {message.get('text')}")
            except asyncio.TimeoutError:
                print("ℹ️  No response to end message (this is normal if no audio was sent)")
            
            print("\n✅ WebSocket test completed successfully!")
            print("   The endpoint is working. You can now test voice input in the browser.")
            
    except ConnectionRefusedError:
        print("❌ Error: Could not connect to WebSocket.")
        print("   Make sure the backend server is running on port 8000")
        print("   Run: cd backend && uvicorn main:app --reload")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_websocket())

