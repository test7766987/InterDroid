import os
import json
import logging
import glob

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('benchmark_loader')

class BenchmarkCase:
    """Benchmark test case class"""
    
    def __init__(self, case_id, name, apk_path=None):
        """Initialize benchmark test case"""
        self.case_id = case_id
        self.name = name
        self.apk_path = apk_path
        self.screenshots = []
        self.actions = []
        self.description = ""
    
    def add_screenshot(self, screenshot_path):
        """Add screenshot"""
        self.screenshots.append(screenshot_path)
    
    def add_action(self, action):
        """Add action"""
        self.actions.append(action)
    
    def set_description(self, description):
        """Set description"""
        self.description = description
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            "case_id": self.case_id,
            "name": self.name,
            "apk_path": self.apk_path,
            "screenshots": self.screenshots,
            "actions": self.actions,
            "description": self.description
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create instance from dictionary"""
        case = cls(data["case_id"], data["name"], data.get("apk_path"))
        case.screenshots = data.get("screenshots", [])
        case.actions = data.get("actions", [])
        case.description = data.get("description", "")
        return case
    
    def get_action_sequence(self):
        """Convert actions to ActionSequence object"""
        from action_coverage import ActionSequence
        
        sequence = ActionSequence()
        for action in self.actions:
            action_type = action.get("type")
            next_page = action.get("next_page")
            params = action.get("params", {})
            sequence.add_action(action_type, next_page, params)
        
        return sequence
    
    def get_screenshot_by_index(self, index):
        """Get screenshot by index"""
        if 0 <= index < len(self.screenshots):
            return self.screenshots[index]
        return None
    
    def get_screenshot_by_page(self, page_name):
        """Get screenshot by page name"""
        # Try to find a screenshot with the page name in its filename
        for screenshot in self.screenshots:
            if page_name.lower() in os.path.basename(screenshot).lower():
                return screenshot
        return None

class BenchmarkLoader:
    """Benchmark loader"""
    
    def __init__(self, benchmark_dir):
        """Initialize loader"""
        self.benchmark_dir = benchmark_dir
        self.cases = []
    
    def load_cases(self):
        """Load all test cases"""
        # Find all test case directories
        case_dirs = glob.glob(os.path.join(self.benchmark_dir, "case_*"))
        
        for case_dir in sorted(case_dirs):
            case_id = int(os.path.basename(case_dir).split("_")[1])
            
            # Load test case configuration
            config_path = os.path.join(case_dir, "config.json")
            if os.path.exists(config_path):
                try:
                    with open(config_path, 'r') as f:
                        config = json.load(f)
                    
                    case = BenchmarkCase(case_id, config.get("name", f"Case {case_id}"))
                    case.set_description(config.get("description", ""))
                    
                    # Set APK path
                    apk_path = config.get("apk_path")
                    if apk_path:
                        if os.path.isabs(apk_path):
                            case.apk_path = apk_path
                        else:
                            case.apk_path = os.path.join(self.benchmark_dir, apk_path)
                    
                    # Load screenshots
                    screenshots_dir = os.path.join(case_dir, "screenshots")
                    if os.path.exists(screenshots_dir):
                        for screenshot in sorted(glob.glob(os.path.join(screenshots_dir, "*.png"))):
                            case.add_screenshot(screenshot)
                    
                    # Load action sequence
                    actions_path = os.path.join(case_dir, "actions.json")
                    if os.path.exists(actions_path):
                        try:
                            with open(actions_path, 'r') as f:
                                actions = json.load(f)
                            case.actions = actions
                        except Exception as e:
                            logger.error(f"Error loading action sequence {actions_path}: {e}")
                    
                    self.cases.append(case)
                    
                except Exception as e:
                    logger.error(f"Error loading test case {case_dir}: {e}")
        
        logger.info(f"Loaded {len(self.cases)} test cases")
        return self.cases
    
    def get_case_by_id(self, case_id):
        """Get test case by ID"""
        for case in self.cases:
            if case.case_id == case_id:
                return case
        return None
    
    def get_case_by_name(self, name):
        """Get test case by name"""
        for case in self.cases:
            if case.name.lower() == name.lower():
                return case
        return None
    
    def save_cases(self, output_dir):
        """Save test cases to output directory"""
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        for case in self.cases:
            case_dir = os.path.join(output_dir, f"case_{case.case_id}")
            os.makedirs(case_dir, exist_ok=True)
            
            # Save configuration
            config = {
                "name": case.name,
                "description": case.description,
                "apk_path": case.apk_path
            }
            
            with open(os.path.join(case_dir, "config.json"), 'w') as f:
                json.dump(config, f, indent=2)
            
            # Save action sequence
            with open(os.path.join(case_dir, "actions.json"), 'w') as f:
                json.dump(case.actions, f, indent=2)
    
    def create_case(self, name, description="", apk_path=None):
        """Create a new test case"""
        # Generate a new case ID
        case_id = 1
        if self.cases:
            case_id = max(case.case_id for case in self.cases) + 1
        
        case = BenchmarkCase(case_id, name, apk_path)
        case.set_description(description)
        self.cases.append(case)
        
        return case
    
    def import_from_action_sequence(self, sequence_path, name=None, description=None, screenshots_dir=None):
        """Import a test case from an action sequence file"""
        from action_coverage import ActionSequence
        
        try:
            sequence = ActionSequence()
            sequence.load_from_file(sequence_path)
            
            if not sequence.actions:
                logger.error(f"Action sequence file {sequence_path} is empty")
                return None
            
            # Create a new case
            if name is None:
                name = os.path.basename(sequence_path).split('.')[0]
            
            case = self.create_case(name, description or "")
            
            # Import actions
            case.actions = sequence.actions
            
            # Import screenshots if available
            if screenshots_dir and os.path.exists(screenshots_dir):
                screenshots = sorted(glob.glob(os.path.join(screenshots_dir, "*.png")))
                for screenshot in screenshots:
                    case.add_screenshot(screenshot)
            
            return case
            
        except Exception as e:
            logger.error(f"Error importing action sequence {sequence_path}: {e}")
            return None
    
    def export_to_action_sequence(self, case_id, output_path):
        """Export a test case to an action sequence file"""
        case = self.get_case_by_id(case_id)
        if not case:
            logger.error(f"Test case with ID {case_id} not found")
            return False
        
        sequence = case.get_action_sequence()
        sequence.save_to_file(output_path)
        
        return True

if __name__ == "__main__":
    # Test code
    import sys
    if len(sys.argv) < 2:
        print("Usage: python benchmark_loader.py <benchmark_dir> [command] [args...]")
        print("Commands:")
        print("  list                     - List all test cases")
        print("  export <case_id> <path>  - Export test case to action sequence")
        print("  import <seq_path> <name> - Import action sequence as test case")
        sys.exit(1)
    
    benchmark_dir = sys.argv[1]
    loader = BenchmarkLoader(benchmark_dir)
    cases = loader.load_cases()
    
    if len(sys.argv) > 2:
        command = sys.argv[2]
        
        if command == "list":
            print(f"Loaded {len(cases)} test cases:")
            for case in cases:
                print(f"  Case {case.case_id}: {case.name}")
                print(f"    APK: {case.apk_path}")
                print(f"    Screenshots: {len(case.screenshots)}")
                print(f"    Actions: {len(case.actions)}")
        
        elif command == "export" and len(sys.argv) > 4:
            case_id = int(sys.argv[3])
            output_path = sys.argv[4]
            
            if loader.export_to_action_sequence(case_id, output_path):
                print(f"Exported test case {case_id} to {output_path}")
            else:
                print(f"Failed to export test case {case_id}")
        
        elif command == "import" and len(sys.argv) > 4:
            sequence_path = sys.argv[3]
            name = sys.argv[4]
            screenshots_dir = sys.argv[5] if len(sys.argv) > 5 else None
            
            case = loader.import_from_action_sequence(sequence_path, name, None, screenshots_dir)
            if case:
                print(f"Imported test case {case.case_id}: {case.name}")
                loader.save_cases(benchmark_dir)
            else:
                print("Failed to import test case")
    else:
        print(f"Loaded {len(cases)} test cases:")
        for case in cases:
            print(f"  Case {case.case_id}: {case.name}")
            print(f"    APK: {case.apk_path}")
            print(f"    Screenshots: {len(case.screenshots)}")
            print(f"    Actions: {len(case.actions)}") 