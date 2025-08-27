#!/usr/bin/env python3
"""
Test script for brand image optimization functionality
"""

import os
import sys
from PIL import Image, ImageDraw, ImageFont
import tempfile

# Add the project root to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

def create_test_image(width, height, text, filename):
    """Create a test image with specified dimensions and text"""
    # Create a new image with a gradient background
    img = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(img)
    
    # Add some text
    try:
        font = ImageFont.truetype("arial.ttf", 20)
    except:
        font = ImageFont.load_default()
    
    # Calculate text position to center it
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    x = (width - text_width) // 2
    y = (height - text_height) // 2
    
    # Draw text
    draw.text((x, y), text, fill='black', font=font)
    
    # Save the test image
    img.save(filename)
    return filename

def test_brand_image_optimization():
    """Test the brand image optimization functionality"""
    print("🧪 Testing Brand Image Optimization...")
    
    # Import the function we want to test
    from routes.routes_helper import save_brand_asset_file
    
    # Test cases with different image sizes
    test_cases = [
        {
            'field': 'logo_header',
            'original_size': (800, 200),
            'expected_max_size': (300, 80),
            'description': 'Logo Header - should be resized to 300x80 max'
        },
        {
            'field': 'logo_footer', 
            'original_size': (600, 150),
            'expected_max_size': (200, 60),
            'description': 'Logo Footer - should be resized to 200x60 max'
        },
        {
            'field': 'favicon',
            'original_size': (128, 128),
            'expected_max_size': (32, 32),
            'description': 'Favicon - should be resized to 32x32'
        },
        {
            'field': 'placeholder_image',
            'original_size': (1920, 1080),
            'expected_max_size': (800, 600),
            'description': 'Placeholder - should be resized to 800x600 max'
        }
    ]
    
    # Create static/pic directory if it doesn't exist
    os.makedirs('static/pic', exist_ok=True)
    
    for i, test_case in enumerate(test_cases):
        print(f"\n📸 Test {i+1}: {test_case['description']}")
        
        # Create a test image
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
            test_image_path = tmp_file.name
            create_test_image(
                test_case['original_size'][0],
                test_case['original_size'][1], 
                f"Test {test_case['field']}",
                test_image_path
            )
        
        try:
            # Create a proper mock file object that mimics Flask's uploaded file
            class MockFile:
                def __init__(self, path):
                    self.path = path
                    self.filename = os.path.basename(path)
                    self.stream = open(path, 'rb')
                
                def read(self, size=None):
                    if size is None:
                        return self.stream.read()
                    return self.stream.read(size)
                
                def seek(self, position):
                    self.stream.seek(position)
                
                def tell(self):
                    return self.stream.tell()
                
                def close(self):
                    self.stream.close()
                
                def __enter__(self):
                    return self
                
                def __exit__(self, exc_type, exc_val, exc_tb):
                    self.close()
            
            mock_file = MockFile(test_image_path)
            
            # Test the optimization function
            filename, file_path = save_brand_asset_file(mock_file, test_case['field'])
            
            # Check if the optimized file exists
            if os.path.exists(file_path):
                # Get the optimized image dimensions
                optimized_img = Image.open(file_path)
                optimized_size = optimized_img.size
                
                print(f"✅ Success: {test_case['field']}")
                print(f"   Original: {test_case['original_size']}")
                print(f"   Optimized: {optimized_size}")
                print(f"   File: {file_path}")
                
                # Verify the size constraints
                max_width, max_height = test_case['expected_max_size']
                if optimized_size[0] <= max_width and optimized_size[1] <= max_height:
                    print(f"   ✅ Size constraints met: {optimized_size[0]}x{optimized_size[1]} <= {max_width}x{max_height}")
                else:
                    print(f"   ❌ Size constraints violated: {optimized_size[0]}x{optimized_size[1]} > {max_width}x{max_height}")
                
                # Check file format
                if file_path.endswith('.png'):
                    print(f"   ✅ Format: PNG")
                else:
                    print(f"   ❌ Unexpected format: {file_path}")
                    
            else:
                print(f"❌ Failed: Optimized file not created at {file_path}")
                    
        except Exception as e:
            print(f"❌ Error testing {test_case['field']}: {str(e)}")
        finally:
            # Clean up test image
            if os.path.exists(test_image_path):
                os.unlink(test_image_path)
    
    print("\n🎉 Brand image optimization test completed!")

if __name__ == "__main__":
    test_brand_image_optimization() 