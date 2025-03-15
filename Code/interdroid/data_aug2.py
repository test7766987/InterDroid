import json
from pathlib import Path
from typing import Dict, Any, List, Tuple
from tqdm import tqdm
from PIL import Image, ImageDraw, ImageFont
import math
import shutil

class DataAugmentator2:
    def __init__(self):
        pass
        
    def get_action_description(self, step: Dict[str, Any]) -> str:
        """Generate action description"""
        action_type = step["action_type"]
        action_detail = step["action_detail"]
        
        if action_type in ["click", "press"]:
            return f"Click at coordinates ({action_detail['x']}, {action_detail['y']})", "A red cross on the screen indicates the click position"
        elif action_type == "swipe":
            return f"Swipe from ({action_detail['start_x']}, {action_detail['start_y']}) to ({action_detail['end_x']}, {action_detail['end_y']})", "Red circles indicate the start and end points of the swipe"
        elif action_type == "special_event":
            return f"Execute special action: {action_detail['event']}", "Red text in the top-left corner describes the special event"
        elif action_type == "input":
            return f"Input text: {action_detail['text']}", "Red text in the top-left corner shows the input text"
        else:
            return f"Execute action: {action_type} - {json.dumps(action_detail, ensure_ascii=False)}"

    def draw_cross(self, draw: ImageDraw, x: int, y: int, size: int = 30, color: tuple = (255, 0, 0), width: int = 5):
        """Draw cross marker
        Args:
            size: Length of cross arms, default 30 pixels
            width: Line thickness, default 5 pixels
        """
        # Draw horizontal line
        draw.line([(x - size, y), (x + size, y)], fill=color, width=width)
        # Draw vertical line
        draw.line([(x, y - size), (x, y + size)], fill=color, width=width)

    def process_screenshot(self, screenshot_path: str, step_data: Dict[str, Any]) -> Image.Image:
        """Process screenshot, add action markers"""
        try:
            img = Image.open(screenshot_path)
            draw = ImageDraw.Draw(img)
            
            # Set color and font
            red_color = (255, 0, 0)
            circle_radius = 10
            try:
                font = ImageFont.truetype("arial.ttf", 24)
            except:
                font = ImageFont.load_default()
            
            action_type = step_data["action_type"]
            
            if action_type in ["click", "press"]:
                x = step_data["action_detail"]["x"]
                y = step_data["action_detail"]["y"]
                # Draw cross marker
                self.draw_cross(draw, x, y)
                
            elif action_type == "swipe":
                start_x = step_data["action_detail"]["start_x"]
                start_y = step_data["action_detail"]["start_y"]
                end_x = step_data["action_detail"]["end_x"]
                end_y = step_data["action_detail"]["end_y"]
                
                # Draw circles for start and end points
                for x, y in [(start_x, start_y), (end_x, end_y)]:
                    draw.ellipse([x-circle_radius, y-circle_radius, 
                                x+circle_radius, y+circle_radius], 
                               outline=red_color, width=3)
                
                # Draw swipe trajectory and arrow
                draw.line([start_x, start_y, end_x, end_y], fill=red_color, width=3)
                arrow_length = 20
                angle = math.atan2(end_y - start_y, end_x - start_x)
                arrow_angle = math.pi / 6
                draw.line([end_x, end_y,
                          end_x - arrow_length * math.cos(angle + arrow_angle),
                          end_y - arrow_length * math.sin(angle + arrow_angle)], 
                         fill=red_color, width=3)
                draw.line([end_x, end_y,
                          end_x - arrow_length * math.cos(angle - arrow_angle),
                          end_y - arrow_length * math.sin(angle - arrow_angle)], 
                         fill=red_color, width=3)
            
            elif action_type == "input":
                text = f"Input: {step_data['action_detail']['text']}"
                draw.text((10, 10), text, fill=red_color, font=font)
            
            elif action_type == "special_event":
                text = f"Special Event: {step_data['action_detail']['event']}"
                draw.text((10, 10), text, fill=red_color, font=font)
            
            return img
            
        except Exception as e:
            print(f"Error processing screenshot: {e}")
            return Image.open(screenshot_path)

    def process_record(self, record_dir: Path) -> None:
        """Process single record directory"""
        # Read record.json
        with open(record_dir / "record.json", "r", encoding="utf-8") as f:
            record_data = json.load(f)
            
        steps = record_data["steps"]
        
        # If processed_screenshots directory exists, delete it first
        processed_dir = record_dir / "processed_screenshots"
        if processed_dir.exists():
            shutil.rmtree(processed_dir)
        
        # Create new processed_screenshots directory
        processed_dir.mkdir(exist_ok=True)
        
        # Process screenshots for each step
        for step in tqdm(steps, desc=f"Processing steps in {record_dir.name}"):
            screenshot_path = record_dir / "screenshots" / f"step_{step['step_id'] - 1}.png"
            if screenshot_path.exists():
                processed_img = self.process_screenshot(str(screenshot_path), step)
                output_path = processed_dir / f"step_{step['step_id'] - 1}_processed.png"
                processed_img.save(str(output_path))

    def process_data_dir(self, data_dir: str) -> None:
        """Process entire data directory"""
        data_path = Path(data_dir)
        
        # Get all valid record directories
        record_dirs = [d for d in data_path.glob("record_*") if (d / "record.json").exists()]
        
        # Add overall progress bar
        for record_dir in tqdm(record_dirs, desc="Processing record directories"):
            print(f"\nProcessing {record_dir.name}...")
            self.process_record(record_dir)

        print(f"\nProcessed {len(record_dirs)} record directories in total")

if __name__ == "__main__":
    # Example
    augmentator = DataAugmentator2()
    
    # Process data directory
    augmentator.process_data_dir("real_data") 