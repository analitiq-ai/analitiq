import argparse

def main():
    parser = argparse.ArgumentParser(description="Process some input.")
    parser.add_argument("text", type=str, help="User prompt")

    args = parser.parse_args()

    print(f"Running Analitiq with prompt: {args.text}")


