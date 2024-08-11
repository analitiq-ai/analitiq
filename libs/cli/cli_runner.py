import argparse

def main():
    parser = argparse.ArgumentParser(description="Process some input.")
    parser.add_argument("text", type=str, help="User prompt")

    parser.parse_args()



