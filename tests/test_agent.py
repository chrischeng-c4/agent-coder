import asyncio
from src.agent.core import create_agent, get_agent_response

async def test_agent():
    print("Testing agent connection...")
    try:
        # Default to gpt-oss:20b
        from src.config import Settings
        settings = Settings(model="gpt-oss:20b")
        agent = create_agent(settings=settings)
        # We can't easily mock the Ollama server here without external libs, 
        # so we will just check if the agent object is created correctly 
        # and try a simple prompt if Ollama is running.
        print("Agent created successfully.")
        
        # Check if we can get a response (timeout if Ollama not running)
        # using a very short timeout
        try:
            response = await asyncio.wait_for(get_agent_response(agent, "Say hello"), timeout=30.0)
            print(f"Agent response: {response}")
        except asyncio.TimeoutError:
            print("Timeout waiting for Ollama. Is it running?")
        except Exception as e:
            print(f"Error during inference: {e}")

    except Exception as e:
        print(f"Failed to create agent: {e}")

if __name__ == "__main__":
    asyncio.run(test_agent())
