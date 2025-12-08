from ddgs import DDGS

def test_ddg():
    print("Testing DDGS...")
    try:
        with DDGS() as ddgs:
            results = ddgs.text("Deep Breathing benefits", max_results=5)
            print("Results type:", type(results))
            for r in results:
                print(r)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_ddg()
