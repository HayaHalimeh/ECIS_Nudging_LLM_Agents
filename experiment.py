from browser_use import ChatOpenAI, Agent 
from dotenv import load_dotenv
import asyncio
import argparse
import os

load_dotenv()

# Set API keys as environment variables
os.environ['OPENAI_API_KEY'] = os.getenv('OPENAI_API_KEY')


async def main():
    parser = argparse.ArgumentParser(description='Run browser automation agent')
    parser.add_argument('--case', type=str, choices=['defaults', 'social_influence', 'no_nudge'], default='no_nudge',
                       help='Choose the experiment case: defaults or social_influence or no_nudge')
    parser.add_argument('--provider', type=str, choices=['openai'], default='openai',
                       help='Choose the model provider: openai')
    parser.add_argument('--model', type=str, choices=['gpt-5-mini', "gpt-5"], default='gpt-5-mini',
                       help='Specify the model name to use ')
    parser.add_argument('--reasoning', type=str, choices=['minimal', 'low', 'medium', 'high'], default='medium',
                        help='Specify the reasoning level for the agent')
    parser.add_argument('--set', type=str, choices=['set_a', 'set_b'], default='set_a',
                        help='Specify the target product set for the experiment (the nudged product set in case of presence of a nudge)')
    parser.add_argument('--seed', type=int, default=42,
                        help='Specify the seed number for the experiment')
    
    
    
    args = parser.parse_args()

    # Define output directory based on the case
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(script_dir, args.case)

    if args.reasoning:
        model_mode = f"model-{args.model}-reasoning-{args.reasoning}"
        if args.reasoning == 'medium':
            use_thinking = True
        else:
            use_thinking = False


    save_conversation_path = os.path.join(os.path.join(output_dir,  args.set, "conversations"), f"{model_mode}-seed-{args.seed}")
    print(f"Saving conversation to: {save_conversation_path}")
    
    # Ensure the folder exists and is writable by the current process.
    os.makedirs(save_conversation_path, exist_ok=True)

    # Read the task 
    prompt_file = "prompt.txt"
    with open(prompt_file, "r", encoding="utf-8") as f:
        task = f.read()

    # Define the model based on the provider
    if args.provider == 'openai':
        # Use OpenAI API
        llm = ChatOpenAI(model=args.model, reasoning_effort=args.reasoning, seed=args.seed)


    # Initialize and run the agent
    agent = Agent(task=task,
                  llm=llm,
                  save_conversation_path=save_conversation_path,
                  generate_gif=False,
                  use_thinking=use_thinking)
    

    await agent.run()

if __name__ == "__main__":
    asyncio.run(main())