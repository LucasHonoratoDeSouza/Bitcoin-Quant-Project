import requests

def get_fear_and_greed():
    """
    Fetches the Crypto Fear & Greed Index from Alternative.me.
    This is the industry standard index (0-100).
    0 = Extreme Fear
    100 = Extreme Greed
    """
    url = "https://api.alternative.me/fng/"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        if "data" in data and len(data["data"]) > 0:
            item = data["data"][0]
            return {
                "value": int(item["value"]),
                "classification": item["value_classification"],
                "timestamp": int(item["timestamp"])
            }
        else:
            return None
            
    except Exception as e:
        print(f"Error fetching Fear & Greed Index: {e}")
        return None

if __name__ == "__main__":
    import json
    print(json.dumps(get_fear_and_greed(), indent=4))
