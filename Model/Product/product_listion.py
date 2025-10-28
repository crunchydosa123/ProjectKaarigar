from google import genai
from pathlib import Path
import base64
import os
import sys
import json
from datetime import datetime
from typing import Dict, List, Optional


# ==================== CONFIGURATION ====================
PROJECT_ID = "useful-figure-475210-g7"
LOCATION = "us-central1"


# ==================== VALIDATION ====================
def validate_credentials():
    """Check if GOOGLE_APPLICATION_CREDENTIALS is set"""
    creds_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    if not creds_path or not os.path.isfile(creds_path):
        print("❌ ERROR: GOOGLE_APPLICATION_CREDENTIALS not set or file not found!")
        print(f"Current value: {creds_path}")
        print("\n📝 Set it with:")
        print(r'$env:GOOGLE_APPLICATION_CREDENTIALS = "D:\Barclays\ProjectKaarigar\Model\Product\useful-figure-475210-g7-e3197ba0e50d.json"')
        sys.exit(1)
    print(f"✅ Credentials found: {creds_path}")


# ==================== PRODUCT LISTING MODULE ====================
class ProductListingModule:
    """Module to handle product listing with image and description using Vertex AI"""
    
    def __init__(self, project_id: str = PROJECT_ID, location: str = LOCATION):
        """
        Initialize the Product Listing Module
        
        Args:
            project_id: Google Cloud Project ID
            location: Region for Vertex AI (default: us-central1)
        """
        self.project_id = project_id
        self.location = location
        try:
            self.client = genai.Client(
                vertexai=True,
                project=project_id,
                location=location
            )
            print(f"✅ GenAI Client initialized with project: {project_id}")
            print(f"✅ Location: {location}")
        except Exception as e:
            print(f"❌ Failed to initialize GenAI: {str(e)}")
            sys.exit(1)
    
    def get_mime_type(self, image_path: str) -> str:
        """
        Determine MIME type from file extension
        
        Args:
            image_path: Path to the image file
            
        Returns:
            MIME type string
        """
        extension = Path(image_path).suffix.lower()
        mime_types = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".gif": "image/gif",
            ".webp": "image/webp"
        }
        return mime_types.get(extension, "image/jpeg")
    
    def parse_listing_response(self, response_text: str) -> Dict:
        """
        Parse AI response into structured JSON format
        
        Args:
            response_text: Raw response from Gemini
            
        Returns:
            Structured dictionary with parsed components
        """
        listing_data = {
            "title": "",
            "description": "",
            "features": [],
            "category": "",
            "target_audience": "",
            "keywords": [],
            "quality_assessment": "",
            "price_range": ""
        }
        
        lines = response_text.split('\n')
        current_section = None
        
        for line in lines:
            line = line.strip()
            
            if not line:
                continue
            
            if "Enhanced Product Title" in line or "1." in line:
                current_section = "title"
                listing_data["title"] = line.replace("1.", "").replace("Enhanced Product Title", "").strip(":")
            elif "Improved Description" in line or "2." in line:
                current_section = "description"
                listing_data["description"] = line.replace("2.", "").replace("Improved Description", "").strip(":")
            elif "Key Features" in line or "3." in line:
                current_section = "features"
            elif "Suggested Category" in line or "4." in line:
                current_section = "category"
                listing_data["category"] = line.replace("4.", "").replace("Suggested Category", "").strip(":")
            elif "Target Audience" in line or "5." in line:
                current_section = "target_audience"
                listing_data["target_audience"] = line.replace("5.", "").replace("Target Audience", "").strip(":")
            elif "Suggested Keywords" in line or "6." in line:
                current_section = "keywords"
            elif "Quality Assessment" in line or "7." in line:
                current_section = "quality_assessment"
                listing_data["quality_assessment"] = line.replace("7.", "").replace("Quality Assessment", "").strip(":")
            elif "Price Range" in line or "8." in line:
                current_section = "price_range"
                listing_data["price_range"] = line.replace("8.", "").replace("Price Range Suggestion", "").strip(":")
            elif current_section == "features" and line.startswith(("-", "•", "*")):
                feature = line.lstrip("-•* ").strip()
                if feature:
                    listing_data["features"].append(feature)
            elif current_section == "keywords" and line.startswith(("-", "•", "*")):
                keyword = line.lstrip("-•* ").strip()
                if keyword:
                    listing_data["keywords"].append(keyword)
            elif current_section == "description" and listing_data["description"]:
                listing_data["description"] += " " + line
            elif current_section == "title" and listing_data["title"]:
                listing_data["title"] += " " + line
        
        return listing_data
    
    def generate_product_listing(
        self, 
        image_path: str, 
        description: str,
        product_name: str = None
    ) -> Dict:
        """
        Generate enhanced product listing using Vertex AI
        
        Args:
            image_path: Path to product image
            description: Product description
            product_name: Optional product name
            
        Returns:
            Dictionary containing product listing details in JSON format
        """
        try:
            # Validate image path exists
            if not Path(image_path).exists():
                return {
                    "status": "error",
                    "code": "FILE_NOT_FOUND",
                    "message": f"Image file not found: {image_path}",
                    "timestamp": datetime.now().isoformat(),
                    "data": None
                }
            
            print(f"📷 Processing image: {image_path}")
            
            # Read image file
            with open(image_path, "rb") as img_file:
                image_data = base64.standard_b64encode(img_file.read()).decode()
            
            # Get MIME type
            mime_type = self.get_mime_type(image_path)
            print(f"📋 MIME Type: {mime_type}")
            
            # Create prompt for product listing
            prompt = f"""Analyze this product image and description, then generate a comprehensive product listing:

Product Name: {product_name or 'Not specified'}
Product Description: {description}

Please provide in this exact format:
1. Enhanced Product Title (catchy and SEO-friendly)
2. Improved Description (professional and engaging, 2-3 sentences)
3. Key Features (5-7 bullet points, each on new line with -)
4. Suggested Category
5. Target Audience
6. Suggested Keywords (5-10 for search, each on new line with -)
7. Quality Assessment of the image
8. Price Range Suggestion (if applicable)"""
            
            print("🤖 Calling Vertex AI Gemini model...")
            
            # Call Vertex AI with image
            response = self.client.models.generate_content(
                model="gemini-2.0-flash",
                contents=[
                    genai.types.Content(
                        role="user",
                        parts=[
                            genai.types.Part(text=prompt),
                            genai.types.Part(
                                inline_data=genai.types.Blob(
                                    mime_type=mime_type,
                                    data=base64.standard_b64decode(image_data)
                                )
                            )
                        ]
                    )
                ]
            )
            
            # Parse response into structured format
            parsed_listing = self.parse_listing_response(response.text)
            
            return {
                "status": "success",
                "code": "LISTING_GENERATED",
                "message": "Product listing generated successfully",
                "timestamp": datetime.now().isoformat(),
                "data": {
                    "product": {
                        "name": product_name or "Unknown",
                        "original_description": description,
                        "image_path": image_path
                    },
                    "listing": parsed_listing,
                    "raw_response": response.text
                }
            }
            
        except FileNotFoundError:
            return {
                "status": "error",
                "code": "FILE_NOT_FOUND",
                "message": f"Image file not found: {image_path}",
                "timestamp": datetime.now().isoformat(),
                "data": None
            }
        except Exception as e:
            return {
                "status": "error",
                "code": "PROCESSING_ERROR",
                "message": f"Error generating listing: {str(e)}",
                "timestamp": datetime.now().isoformat(),
                "data": None
            }
    
    def batch_listing(self, products: list) -> Dict:
        """
        Generate listings for multiple products
        
        Args:
            products: List of dicts with 'image_path' and 'description' keys
            
        Returns:
            Dictionary with batch results in JSON format
        """
        results = []
        successful = 0
        failed = 0
        
        total = len(products)
        
        for idx, product in enumerate(products, 1):
            print(f"\n📦 Processing product {idx}/{total}...")
            listing = self.generate_product_listing(
                image_path=product['image_path'],
                description=product['description'],
                product_name=product.get('name')
            )
            results.append(listing)
            
            if listing["status"] == "success":
                successful += 1
            else:
                failed += 1
        
        return {
            "status": "success",
            "code": "BATCH_PROCESSING_COMPLETE",
            "message": f"Batch processing completed: {successful} successful, {failed} failed",
            "timestamp": datetime.now().isoformat(),
            "data": {
                "summary": {
                    "total": total,
                    "successful": successful,
                    "failed": failed
                },
                "results": results
            }
        }
    
    def save_to_file(self, result: Dict, output_file: str = None) -> Dict:
        """
        Save result to JSON file
        
        Args:
            result: Result dictionary
            output_file: Output file path (auto-generated if None)
            
        Returns:
            Dictionary confirming save status
        """
        try:
            if not output_file:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_file = f"product_listing_{timestamp}.json"
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            
            return {
                "status": "success",
                "code": "FILE_SAVED",
                "message": f"Result saved to {output_file}",
                "timestamp": datetime.now().isoformat(),
                "data": {
                    "file_path": output_file,
                    "file_size": os.path.getsize(output_file),
                    "saved_at": datetime.now().isoformat()
                }
            }
        except Exception as e:
            return {
                "status": "error",
                "code": "SAVE_ERROR",
                "message": f"Error saving file: {str(e)}",
                "timestamp": datetime.now().isoformat(),
                "data": None
            }
    
    def refine_listing(self, listing_data: Dict, refinement_prompt: str) -> Dict:
        """
        Refine an existing listing with additional instructions
        
        Args:
            listing_data: The existing listing dictionary
            refinement_prompt: Instructions for refinement
            
        Returns:
            Dictionary with refined listing
        """
        try:
            listing_str = json.dumps(listing_data, indent=2)
            
            prompt = f"""You are a product listing expert. Please refine the following product listing based on the refinement instructions:

ORIGINAL LISTING:
{listing_str}

REFINEMENT INSTRUCTIONS:
{refinement_prompt}

Please provide the refined listing in the same JSON format structure."""
            
            print("🤖 Refining listing with Gemini model...")
            
            response = self.client.models.generate_content(
                model="gemini-2.0-flash",
                contents=[
                    genai.types.Content(
                        role="user",
                        parts=[
                            genai.types.Part(text=prompt)
                        ]
                    )
                ]
            )
            
            refined_listing = self.parse_listing_response(response.text)
            
            return {
                "status": "success",
                "code": "LISTING_REFINED",
                "message": "Listing refined successfully",
                "timestamp": datetime.now().isoformat(),
                "data": {
                    "original_listing": listing_data,
                    "refined_listing": refined_listing,
                    "refinement_prompt": refinement_prompt
                }
            }
        except Exception as e:
            return {
                "status": "error",
                "code": "REFINEMENT_ERROR",
                "message": f"Error refining listing: {str(e)}",
                "timestamp": datetime.now().isoformat(),
                "data": None
            }


# ==================== SERVERLESS FUNCTIONS ====================
def generate_listing_handler(payload: Dict) -> Dict:
    """
    Serverless function handler for single product listing
    
    Expected payload:
    {
        "image_path": "path/to/image.jpg",
        "description": "product description",
        "product_name": "optional product name"
    }
    
    Returns:
        JSON response with listing
    """
    try:
        validate_credentials()
        
        module = ProductListingModule(project_id=PROJECT_ID, location=LOCATION)
        
        result = module.generate_product_listing(
            image_path=payload.get('image_path'),
            description=payload.get('description'),
            product_name=payload.get('product_name')
        )
        
        return result
    
    except Exception as e:
        return {
            "status": "error",
            "code": "HANDLER_ERROR",
            "message": str(e),
            "timestamp": datetime.now().isoformat(),
            "data": None
        }


def batch_listing_handler(payload: Dict) -> Dict:
    """
    Serverless function handler for batch processing
    
    Expected payload:
    {
        "products": [
            {
                "image_path": "path/to/image1.jpg",
                "description": "description 1",
                "name": "product 1"
            },
            ...
        ]
    }
    
    Returns:
        JSON response with batch results
    """
    try:
        validate_credentials()
        
        module = ProductListingModule(project_id=PROJECT_ID, location=LOCATION)
        
        result = module.batch_listing(payload.get('products', []))
        
        return result
    
    except Exception as e:
        return {
            "status": "error",
            "code": "HANDLER_ERROR",
            "message": str(e),
            "timestamp": datetime.now().isoformat(),
            "data": None
        }


def refine_listing_handler(payload: Dict) -> Dict:
    """
    Serverless function handler for refining listings
    
    Expected payload:
    {
        "listing": { listing_data },
        "refinement_prompt": "refinement instructions"
    }
    
    Returns:
        JSON response with refined listing
    """
    try:
        validate_credentials()
        
        module = ProductListingModule(project_id=PROJECT_ID, location=LOCATION)
        
        result = module.refine_listing(
            listing_data=payload.get('listing'),
            refinement_prompt=payload.get('refinement_prompt')
        )
        
        return result
    
    except Exception as e:
        return {
            "status": "error",
            "code": "HANDLER_ERROR",
            "message": str(e),
            "timestamp": datetime.now().isoformat(),
            "data": None
        }


# ==================== USER INPUT FUNCTIONS ====================
def get_user_input() -> Dict:
    """
    Get product details from user input
    
    Returns:
        Dictionary with image_path and description
    """
    print("\n" + "="*70)
    print("       PRODUCT LISTING MODULE - VERTEX AI GEMINI 2.0")
    print("="*70)
    
    # Get image path
    while True:
        image_path = input("\n📁 Enter the image path (e.g., D:\\images\\product.jpg): ").strip()
        if Path(image_path).exists():
            print(f"✅ Image found: {Path(image_path).name}")
            break
        else:
            print(f"❌ Image file not found. Please enter a valid path.")
    
    # Get product name
    product_name = input("📦 Enter product name (optional, press Enter to skip): ").strip()
    if not product_name:
        product_name = None
    
    # Get description
    description = input("📝 Enter product description: ").strip()
    if not description:
        print("⚠️  Warning: Using empty description")
        description = ""
    
    return {
        "image_path": image_path,
        "description": description,
        "product_name": product_name
    }


def display_json_result(result: Dict) -> None:
    """
    Display result in formatted JSON
    
    Args:
        result: Result dictionary
    """
    print("\n" + "="*70)
    print("           JSON OUTPUT")
    print("="*70)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print("="*70 + "\n")


# ==================== MAIN EXECUTION ====================
def main():
    """Main execution function"""
    # Validate credentials first
    validate_credentials()
    
    print(f"\n🚀 Initializing Product Listing Module...")
    product_module = ProductListingModule(project_id=PROJECT_ID, location=LOCATION)
    
    # Main menu
    while True:
        print("\n" + "="*70)
        print("           MAIN MENU")
        print("="*70)
        print("1. Single Product Listing (JSON Output)")
        print("2. Batch Processing (JSON Output)")
        print("3. Refine Listing (JSON Output)")
        print("4. Exit")
        
        choice = input("\nSelect option (1-4): ").strip()
        
        if choice == "1":
            # Single product
            user_input = get_user_input()
            print("\n⏳ Processing product listing...")
            result = product_module.generate_product_listing(
                image_path=user_input['image_path'],
                description=user_input['description'],
                product_name=user_input['product_name']
            )
            display_json_result(result)
            
            # Save option
            save_choice = input("Save to file? (yes/no): ").strip().lower()
            if save_choice in ['yes', 'y']:
                save_result = product_module.save_to_file(result)
                display_json_result(save_result)
        
        elif choice == "2":
            # Batch processing
            try:
                batch_count = int(input("\nHow many products? ").strip())
                products = []
                
                for idx in range(1, batch_count + 1):
                    print(f"\n--- Product {idx} ---")
                    while True:
                        image_path = input(f"📁 Image path: ").strip()
                        if Path(image_path).exists():
                            print(f"✅ Image found")
                            break
                        else:
                            print(f"❌ Image not found")
                    
                    product_name = input(f"📦 Product name: ").strip() or None
                    description = input(f"📝 Description: ").strip() or ""
                    
                    products.append({
                        "image_path": image_path,
                        "description": description,
                        "name": product_name
                    })
                
                if products:
                    print("\n⏳ Processing batch...")
                    result = product_module.batch_listing(products)
                    display_json_result(result)
                    
                    save_choice = input("Save to file? (yes/no): ").strip().lower()
                    if save_choice in ['yes', 'y']:
                        save_result = product_module.save_to_file(result)
                        display_json_result(save_result)
            
            except ValueError:
                print("❌ Invalid number")
        
        elif choice == "3":
            # Refine listing
            print("\n" + "="*70)
            print("       REFINE LISTING")
            print("="*70)
            
            listing_json = input("\nPaste listing JSON:\n> ").strip()
            refinement_prompt = input("\nEnter refinement instructions:\n> ").strip()
            
            try:
                listing_data = json.loads(listing_json)
                print("\n⏳ Refining listing...")
                result = product_module.refine_listing(listing_data, refinement_prompt)
                display_json_result(result)
            except json.JSONDecodeError:
                print("❌ Invalid JSON format")
        
        elif choice == "4":
            print("\n👋 Thank you for using Product Listing Module!")
            break
        
        else:
            print("❌ Invalid option")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Module terminated by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        sys.exit(1)