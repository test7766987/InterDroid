import json
from pathlib import Path
from typing import Dict, Any, List, Tuple
from llm_api import SiliconFlowAPI
from tqdm import tqdm
from PIL import Image, ImageDraw, ImageFont
import math
import os

class DataAugmentator:
    def __init__(self, api_key: str, model: str = "Qwen/Qwen2-VL-72B-Instruct"):
        self.api = SiliconFlowAPI(api_key=api_key, model=model)
        
    def get_action_description(self, step: Dict[str, Any]) -> str:
        """Generate action description based on step information"""
        action_type = step["action_type"]
        action_detail = step["action_detail"]
        
        if action_type == "click":
            return f"Click at coordinates ({action_detail['x']}, {action_detail['y']})", "A red circle on the screen indicates the click coordinates, with a red arrow pointing to it"
        elif action_type == "swipe":
            return f"Swipe from ({action_detail['start_x']}, {action_detail['start_y']}) to ({action_detail['end_x']}, {action_detail['end_y']})", "Red circles on the screen indicate the start and end coordinates of the swipe, with arrows showing the direction"
        elif action_type == "special_event":
            return f"Execute special action: {action_detail['event']}", "Red text in the top-left corner describes the special event"
        elif action_type == "input":
            return f"Input text: {action_detail['text']}", "Red text in the top-left corner shows the input text"
        else:
            return f"Execute action: {action_type} - {json.dumps(action_detail, ensure_ascii=False)}"
        
    def generate_prompt(self, target: str, step: Dict[str, Any], 
                       combined_img: str) -> List[Tuple[str, List]]:
        """Generate prompt for querying LLM"""
        
        # Get action description
        action_desc, label_info = self.get_action_description(step)

        app, activity = step['activity_info'].split('/')
            
        # Build prompt messages
        messages = [
            ("user", [
                combined_img,
                f"""The image shows two consecutive screenshots of the {app} application, from left to right.
These are screenshots before and after performing the action: {action_desc}.

{label_info}.

Overall goal: {target}, this operation is one of multiple steps to achieve the overall goal.

Reason why the user performed this action:

Please analyze and provide reasoning from the following aspects:
1. Interface state before the action (first image)
2. Specific action performed by the user
3. Interface changes after the action (second image)
4. How this action helps achieve the overall goal
5. Why this action needs to be performed at this time

Please first describe your reasoning process in a coherent paragraph, then organize the analysis results in the following JSON format:

{{
    "reasoning": "What was the interface state before the action, why this action was needed to achieve the overall goal, and why it needed to be performed at this time"
}}
"""
            ])
        ]

        print(messages)

        return messages

    def _parse_bounds(self, bounds_str: str) -> tuple:
        """Parse bounds string into coordinate tuple"""
        try:
            # Remove '[' and ']', split numbers
            nums = bounds_str.strip('[]').split(',')
            return tuple(map(int, nums))
        except:
            return None
            
    def _calculate_arrow_direction(self, x: int, y: int, img_width: int, img_height: int) -> Tuple[float, float]:
        """Calculate arrow direction
        
        Calculate the most appropriate arrow direction based on point position,
        ensuring the arrow stays within image bounds
        Returns x and y offsets of arrow start point relative to circle center
        """
        margin = 70  # arrow length plus some margin
        
        # calculate the distance to the four sides
        dist_to_left = x
        dist_to_right = img_width - x
        dist_to_top = y
        dist_to_bottom = img_height - y
        
        # find the farthest side
        distances = [
            (dist_to_right, (1, 0)),   # right
            (dist_to_left, (-1, 0)),   # left
            (dist_to_bottom, (0, 1)),  # bottom
            (dist_to_top, (0, -1))     # top
        ]
        
        # sort by distance, find the farthest side
        max_dist, direction = max(distances, key=lambda x: x[0])
        
        # arrow length
        arrow_length = 60
        dx, dy = direction
        
        # if it is the diagonal position, use 45 degree angle
        if max_dist > margin:
            if x < margin and y < margin:  # left top corner
                dx, dy = 1, 1
            elif x < margin and y > img_height - margin:  # left bottom corner
                dx, dy = 1, -1
            elif x > img_width - margin and y < margin:  # right top corner
                dx, dy = -1, 1
            elif x > img_width - margin and y > img_height - margin:  # right bottom corner
                dx, dy = -1, -1
            
        return dx * arrow_length, dy * arrow_length

    def process_screenshot(self, screenshot_path: str, step_data: Dict[str, Any]) -> Image.Image:
        """Process screenshot, add operation markers"""
        try:
            img = Image.open(screenshot_path)
            draw = ImageDraw.Draw(img)
            
            # set color and font
            red_color = (255, 0, 0)
            circle_radius = 10
            try:
                font = ImageFont.truetype("arial.ttf", 24)
            except:
                font = ImageFont.load_default()
            
            action_type = step_data["action_type"]
            
            if action_type == "click" or action_type == "press":
                x = step_data["action_detail"]["x"]
                y = step_data["action_detail"]["y"]
                
                # calculate arrow direction
                dx, dy = self._calculate_arrow_direction(x, y, img.width, img.height)
                
                # draw arrow pointing to the circle
                arrow_start_x = x + dx
                arrow_start_y = y + dy
                
                # draw main arrow line
                draw.line([arrow_start_x, arrow_start_y, x, y], 
                         fill=red_color, width=6)
                
                # draw arrow head
                arrow_head_length = 30
                angle = math.atan2(y - arrow_start_y, x - arrow_start_x)
                arrow_angle = math.pi / 6
                
                draw.line([x, y,
                          x - arrow_head_length * math.cos(angle + arrow_angle),
                          y - arrow_head_length * math.sin(angle + arrow_angle)],
                         fill=red_color, width=4)
                draw.line([x, y,
                          x - arrow_head_length * math.cos(angle - arrow_angle),
                          y - arrow_head_length * math.sin(angle - arrow_angle)],
                         fill=red_color, width=4)
                
                # draw solid circle
                draw.ellipse([x-circle_radius, y-circle_radius, 
                            x+circle_radius, y+circle_radius], 
                           fill=red_color)
                
            elif action_type == "swipe":
                start_x = step_data["action_detail"]["start_x"]
                start_y = step_data["action_detail"]["start_y"]
                end_x = step_data["action_detail"]["end_x"]
                end_y = step_data["action_detail"]["end_y"]
                
                # add arrow and circle for start and end points
                for x, y in [(start_x, start_y), (end_x, end_y)]:
                    dx, dy = self._calculate_arrow_direction(x, y, img.width, img.height)
                    
                    # draw arrow pointing to the circle
                    arrow_start_x = x + dx
                    arrow_start_y = y + dy
                    
                    # draw main arrow line
                    draw.line([arrow_start_x, arrow_start_y, x, y], 
                             fill=red_color, width=4)
                    
                    # draw arrow head
                    arrow_head_length = 15
                    angle = math.atan2(y - arrow_start_y, x - arrow_start_x)
                    arrow_angle = math.pi / 6
                    
                    draw.line([x, y,
                              x - arrow_head_length * math.cos(angle + arrow_angle),
                              y - arrow_head_length * math.sin(angle + arrow_angle)],
                             fill=red_color, width=4)
                    draw.line([x, y,
                              x - arrow_head_length * math.cos(angle - arrow_angle),
                              y - arrow_head_length * math.sin(angle - arrow_angle)],
                             fill=red_color, width=4)
                    
                    # draw solid circle
                    draw.ellipse([x-circle_radius, y-circle_radius, 
                                x+circle_radius, y+circle_radius], 
                               fill=red_color)
                
                # draw swipe trajectory and arrow
                draw.line([start_x, start_y, end_x, end_y], fill=red_color, width=4)
                arrow_length = 20
                angle = math.atan2(end_y - start_y, end_x - start_x)
                arrow_angle = math.pi / 6
                draw.line([end_x, end_y,
                          end_x - arrow_length * math.cos(angle + arrow_angle),
                          end_y - arrow_length * math.sin(angle + arrow_angle)], 
                         fill=red_color, width=4)
                draw.line([end_x, end_y,
                          end_x - arrow_length * math.cos(angle - arrow_angle),
                          end_y - arrow_length * math.sin(angle - arrow_angle)], 
                         fill=red_color, width=4)
            
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

    def process_record(self, record_dir: Path) -> List[Dict[str, Any]]:
        """Process single record directory, generate reasoning descriptions"""
        # read record.json
        with open(record_dir / "record.json", "r", encoding="utf-8") as f:
            record_data = json.load(f)
            
        target = record_data["target"]
        steps = record_data["steps"]
        
        # create combined_screenshots directory
        combined_screenshots_dir = record_dir / "combined_screenshots"
        combined_screenshots_dir.mkdir(exist_ok=True)
        
        # create new output data structure, keep the original record.json structure
        augmented_record = {
            "target": target,
            "screen_size": record_data["screen_size"],
            "steps": []
        }
        
        # add progress bar
        for i in tqdm(range(len(steps) - 1), desc=f"Processing steps in {record_dir.name}"):
            step_a = steps[i]
            step_b = steps[i + 1]

            print(step_a)

            step_a_img_path = str(record_dir / "screenshots" / f"step_{step_a['step_id'] - 1}.png")
            img_a = self.process_screenshot(step_a_img_path, step_a)
            
            step_b_img_path = str(record_dir / "screenshots" / f"step_{step_b['step_id'] - 1}.png")
            img_b = Image.open(step_b_img_path)
            
            # merge two images into one
            gap = 20
            total_width = img_a.width + img_b.width + gap
            max_height = max(img_a.height, img_b.height)
            combined_img = Image.new('RGB', (total_width, max_height), color='white')
            combined_img.paste(img_a, (0, 0))
            combined_img.paste(img_b, (img_a.width + gap, 0))
            
            # save combined_img
            combined_img_path = combined_screenshots_dir / f"combined_step_{step_a['step_id']}.png"
            combined_img.save(str(combined_img_path))
            
            # generate prompt and call llm api
            messages = self.generate_prompt(target, step_a, combined_img)
            response = self.api.chat_completion(messages)
            
            # extract JSON in response
            content = response["choices"][0]["message"]["content"]
            try:
                start_idx = content.find("{")
                end_idx = content.rfind("}") + 1
                if start_idx != -1 and end_idx != -1:
                    json_str = content[start_idx:end_idx]
                    reasoning_data = json.loads(json_str)
                else:
                    reasoning_data = {"reasoning": content}
            except json.JSONDecodeError:
                reasoning_data = {"reasoning": content}

            print(reasoning_data)
            
            # copy the origin step info and add reasoning info
            augmented_step = step_a.copy()
            augmented_step.update(reasoning_data)
            
            # add the augmented step info into steps list
            augmented_record["steps"].append(augmented_step)
            
        # add the last step（without reasoning）
        if steps:
            augmented_record["steps"].append(steps[-1].copy())
            
        return augmented_record

    def process_data_dir(self, data_dir: str) -> None:
        """Process entire data directory"""
        data_path = Path(data_dir)
        
        # Get all valid record directories
        record_dirs = [d for d in data_path.glob("record_*") if (d / "record.json").exists()]
        
        # Add overall progress bar
        for record_dir in tqdm(record_dirs, desc="Processing record directories"):
            print(f"\nProcessing {record_dir.name}...")
            augmented_record = self.process_record(record_dir)
            
            # Save augmented data
            output_file = record_dir / "augmented_reasoning.json"
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(augmented_record, f, ensure_ascii=False, indent=2)
            
            print(f"Saved augmented data to {output_file}")

            break

        print(f"\nProcessed {len(record_dirs)} record directories in total")

if __name__ == "__main__":
    # example
    augmentator = DataAugmentator(
        api_key="xxx",
        model="xxx"  # VLM model
    )
    
    # process data dir
    augmentator.process_data_dir("real_data")
