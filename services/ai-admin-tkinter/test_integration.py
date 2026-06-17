"""
Integration test - Verify all modules work together
Quick smoke test for the modular architecture
"""

import sys
import traceback

def test_imports():
    """Test all modules can be imported"""
    print("Testing imports...")
    
    try:
        import config
        print("  ✓ config.py")
    except Exception as e:
        print(f"  ✗ config.py: {e}")
        return False
    
    try:
        from api_client import AIEngineClient
        print("  ✓ api_client.py")
    except Exception as e:
        print(f"  ✗ api_client.py: {e}")
        return False
    
    try:
        from styles import AppStyle
        print("  ✓ styles.py")
    except Exception as e:
        print(f"  ✗ styles.py: {e}")
        return False
    
    try:
        from widgets import ModernScrollableFrame, Card, MetricDisplay, StatusBadge, ModernSlider
        print("  ✓ widgets.py")
    except Exception as e:
        print(f"  ✗ widgets.py: {e}")
        return False
    
    try:
        from components import ModelStatusSection, QuickActionsSection, TrainingConfigSection, DatasetUploadSection
        print("  ✓ components.py")
    except Exception as e:
        print(f"  ✗ components.py: {e}")
        return False
    
    try:
        from main import AIAdminDashboard
        print("  ✓ main.py")
    except Exception as e:
        print(f"  ✗ main.py: {e}")
        return False
    
    return True

def test_config():
    """Test configuration values"""
    print("\nTesting configuration...")
    
    try:
        from config import COLORS, FONTS, API_BASE_URL
        
        assert isinstance(COLORS, dict), "COLORS should be dict"
        assert 'bg_dark' in COLORS, "COLORS should have bg_dark"
        assert 'accent' in COLORS, "COLORS should have accent"
        print("  ✓ Colors configured")
        
        assert isinstance(FONTS, dict), "FONTS should be dict"
        assert 'title' in FONTS, "FONTS should have title"
        print("  ✓ Fonts configured")
        
        assert isinstance(API_BASE_URL, str), "API_BASE_URL should be string"
        assert 'http' in API_BASE_URL, "API_BASE_URL should be URL"
        print("  ✓ API URL configured")
        
        return True
    except Exception as e:
        print(f"  ✗ Configuration error: {e}")
        return False

def test_widget_creation():
    """Test widget instantiation"""
    print("\nTesting widget creation...")
    
    try:
        import tkinter as tk
        from widgets import Card, MetricDisplay, StatusBadge, ModernSlider
        
        root = tk.Tk()
        root.withdraw()  # Hide window
        
        # Test Card
        card = Card(root, "Test Card")
        print("  ✓ Card created")
        
        # Test MetricDisplay
        metric = MetricDisplay(root, "Test Metric", "0")
        print("  ✓ MetricDisplay created")
        
        # Test StatusBadge
        badge = StatusBadge(root)
        badge.set_status(True)
        print("  ✓ StatusBadge created")
        
        # Test ModernSlider
        slider = ModernSlider(root, "Test Slider", 0, 100, 50, is_int=True)
        assert slider.get_value() == 50, "Slider should have default value"
        print("  ✓ ModernSlider created")
        
        root.destroy()
        return True
    except Exception as e:
        print(f"  ✗ Widget creation failed: {e}")
        traceback.print_exc()
        return False

def test_api_client():
    """Test API client structure"""
    print("\nTesting API client...")
    
    try:
        from api_client import AIEngineClient
        
        client = AIEngineClient()
        
        # Check methods exist
        assert hasattr(client, 'get_model_info'), "Should have get_model_info"
        assert hasattr(client, 'train_model'), "Should have train_model"
        assert hasattr(client, 'reset_model'), "Should have reset_model"
        assert hasattr(client, 'upload_dataset'), "Should have upload_dataset"
        print("  ✓ All API methods exist")
        
        return True
    except Exception as e:
        print(f"  ✗ API client error: {e}")
        return False

def test_components():
    """Test component creation"""
    print("\nTesting components...")
    
    try:
        import tkinter as tk
        from components import ModelStatusSection, TrainingConfigSection
        
        root = tk.Tk()
        root.withdraw()
        
        # Test ModelStatusSection
        status = ModelStatusSection(root)
        status.update_status({'is_trained': True, 'training_samples': 1000})
        print("  ✓ ModelStatusSection created")
        
        # Test TrainingConfigSection
        training = TrainingConfigSection(root, lambda: None)
        params = training.get_params()
        assert 'n_estimators' in params, "Should return parameters"
        print("  ✓ TrainingConfigSection created")
        
        root.destroy()
        return True
    except Exception as e:
        print(f"  ✗ Component error: {e}")
        traceback.print_exc()
        return False

def run_all_tests():
    """Run all integration tests"""
    print("=" * 60)
    print("AI Admin Dashboard - Integration Test")
    print("=" * 60)
    
    results = []
    
    results.append(("Imports", test_imports()))
    results.append(("Configuration", test_config()))
    results.append(("Widgets", test_widget_creation()))
    results.append(("API Client", test_api_client()))
    results.append(("Components", test_components()))
    
    print("\n" + "=" * 60)
    print("Test Results")
    print("=" * 60)
    
    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{name:20s} {status}")
    
    total = len(results)
    passed = sum(1 for _, p in results if p)
    
    print("=" * 60)
    print(f"Total: {passed}/{total} tests passed")
    print("=" * 60)
    
    return all(p for _, p in results)

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
