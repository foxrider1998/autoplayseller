"""
Generate Config Helper
Script untuk generate config.json dengan 1-100 produk
"""
import json

def generate_config(num_products: int = 100):
    """Generate config untuk N produk"""
    
    config = {
        "obs_settings": {
            "host": "localhost",
            "port": 4455,
            "password": "",
            "video_source_name": "VideoPlayer",
            "scene_name": "Main Scene"
        },
        "comment_keywords": {},
        "comment_source": {
            "type": "file",
            "file_path": "comments.txt",
            "check_interval": 1.0
        },
        "video_settings": {
            "auto_hide_after_play": True,
            "transition_duration": 0.5
        }
    }
    
    # Generate keywords untuk N produk
    for i in range(1, num_products + 1):
        config["comment_keywords"][f"keranjang {i}"] = {
            "video_path": f"videos/product_{i}.mp4",
            "response_text": f"Terima kasih! Produk {i} akan kami proses segera 🎉"
        }
    
    # Save to file
    with open("config.json", "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    
    print(f"✓ Config generated for {num_products} products!")
    print(f"✓ File saved: config.json")
    print(f"\nJangan lupa:")
    print(f"1. Siapkan {num_products} video files di folder videos/")
    print(f"2. Nama file: product_1.mp4, product_2.mp4, ..., product_{num_products}.mp4")
    print(f"3. Setup OBS dengan Media Source bernama 'VideoPlayer'")


if __name__ == "__main__":
    import sys
    
    # Check argument
    num = 100
    if len(sys.argv) > 1:
        try:
            num = int(sys.argv[1])
        except:
            print("Usage: python generate_config.py [number_of_products]")
            print("Example: python generate_config.py 50")
            sys.exit(1)
    
    print(f"Generating config for {num} products...\n")
    generate_config(num)
