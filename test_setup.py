import sys
import os
from datetime import datetime

def test_imports():
    """Test if all required packages are installed"""
    required_packages = ['requests', 'pandas']
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"✓ {package} is installed")
        except ImportError:
            missing_packages.append(package)
            print(f"✗ {package} is missing")
    
    return len(missing_packages) == 0

def test_project_structure():
    """Test if all required files and directories exist"""
    required_structure = [
        'src',
        'src/api',
        'src/models',
        'src/utils',
        'src/gui',
        'src/api/warframe_market.py',
        'src/models/item.py',
        'src/utils/config.py',
        'src/gui/main_window.py',
        'main.py'
    ]
    
    missing_paths = []
    
    for path in required_structure:
        full_path = os.path.join(os.getcwd(), path)
        if os.path.exists(full_path):
            print(f"✓ {path} exists")
        else:
            missing_paths.append(path)
            print(f"✗ {path} is missing")
    
    return len(missing_paths) == 0

def test_api_connection():
    """Test if we can connect to the Warframe Market API"""
    from src.api.warframe_market import WarframeMarketAPI
    
    try:
        api = WarframeMarketAPI()
        items = api.get_items_list()
        if items:
            print(f"✓ API connection successful - retrieved {len(items)} items")
            return True
        else:
            print("✗ API connection failed - no items retrieved")
            return False
    except Exception as e:
        print(f"✗ API connection failed with error: {str(e)}")
        return False

def test_item_model():
    """Test if the Item model works correctly"""
    from src.models.item import Item
    from src.api.warframe_market import WarframeMarketAPI
    
    try:
        api = WarframeMarketAPI()
        # Test with a known item (Rhino Prime Set)
        item = Item(url_name="rhino_prime_set", name="Rhino Prime Set")
        item.update_data(api)
        analysis = item.analyze()
        
        if analysis:
            print("✓ Item model working correctly")
            print(f"  - Current lowest sell price: {analysis.lowest_sell}")
            print(f"  - Current highest buy price: {analysis.highest_buy}")
            print(f"  - Potential profit: {analysis.potential_profit}")
            return True
        else:
            print("✗ Item model failed to analyze data")
            return False
    except Exception as e:
        print(f"✗ Item model test failed with error: {str(e)}")
        return False

def run_all_tests():
    """Run all setup tests"""
    print("\n=== Running Setup Tests ===")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("Python version:", sys.version)
    print("\n1. Testing Required Packages:")
    packages_ok = test_imports()
    
    print("\n2. Testing Project Structure:")
    structure_ok = test_project_structure()
    
    print("\n3. Testing API Connection:")
    api_ok = test_api_connection()
    
    print("\n4. Testing Item Model:")
    model_ok = test_item_model()
    
    print("\n=== Test Summary ===")
    print(f"Required Packages: {'✓' if packages_ok else '✗'}")
    print(f"Project Structure: {'✓' if structure_ok else '✗'}")
    print(f"API Connection: {'✓' if api_ok else '✗'}")
    print(f"Item Model: {'✓' if model_ok else '✗'}")
    
    all_passed = all([packages_ok, structure_ok, api_ok, model_ok])
    print(f"\nOverall Status: {'✓ All tests passed' if all_passed else '✗ Some tests failed'}")
    
    return all_passed

if __name__ == "__main__":
    run_all_tests()