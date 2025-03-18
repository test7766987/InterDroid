import argparse
import os
import sys
import logging
from datetime import datetime
import configparser

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('benchmark')

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Automated Testing Tool')
    
    # Required arguments
    parser.add_argument('-o', '--output', required=True, help='Output directory')
    
    # Test related parameters
    parser.add_argument('--case', type=int, help='Specify which test case to run from the Benchmark')
    parser.add_argument('--time', default='6h', help='Test duration, format: hours(6h), minutes(6m) or seconds(6s), default: 6h')
    parser.add_argument('--repeat', type=int, default=1, help='Number of times to repeat the test, default: 1')
    parser.add_argument('--wait', type=int, default=0, help='Idle time to wait before testing (seconds)')
    parser.add_argument('--record', help='Specific record to use as reference (for LLM testing), default: None')
    
    # Test method selection
    test_methods = parser.add_argument_group('Test methods')
    test_methods.add_argument('--page-coverage', action='store_true', help='Calculate page coverage')
    test_methods.add_argument('--action-coverage', action='store_true', help='Calculate action coverage')
    test_methods.add_argument('--exact-match', action='store_true', help='Calculate exact match rate')
    
    return parser.parse_args()

def parse_time(time_str):
    """Parse time string to seconds"""
    if time_str.endswith('h'):
        return int(time_str[:-1]) * 3600
    elif time_str.endswith('m'):
        return int(time_str[:-1]) * 60
    elif time_str.endswith('s'):
        return int(time_str[:-1])
    else:
        try:
            return int(time_str)
        except ValueError:
            logger.error(f"Cannot parse time format: {time_str}")
            sys.exit(1)

def setup_output_dir(output_dir):
    """Set up output directory"""
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = os.path.join(output_dir, f"run_{timestamp}")
    os.makedirs(run_dir)
    
    return run_dir

def main():
    """Main function"""
    args = parse_arguments()
    
    # Create output directory with timestamp
    run_dir = setup_output_dir(args.output)
    
    # Save run parameters
    import json
    with open(os.path.join(run_dir, "args.json"), "w") as f:
        json.dump(vars(args), f, indent=2)
    
    # Check if config.ini exists
    if not os.path.exists('config.ini'):
        logger.error("config.ini not found. Please create a config.ini file with LLM and device settings.")
        sys.exit(1)
    
    # Read config.ini
    config = configparser.ConfigParser()
    config.read('config.ini')
    
    # Verify required sections and keys
    required_sections = ['llm', 'uiautomator2', 'data']
    for section in required_sections:
        if section not in config:
            logger.error(f"Missing section '{section}' in config.ini")
            sys.exit(1)
    
    if 'openai_api_key' not in config['llm']:
        logger.error("Missing 'openai_api_key' in [llm] section of config.ini")
        sys.exit(1)
    
    if 'android_device' not in config['uiautomator2']:
        logger.error("Missing 'android_device' in [uiautomator2] section of config.ini")
        sys.exit(1)
    
    if 'data_dir' not in config['data']:
        logger.error("Missing 'data_dir' in [data] section of config.ini")
        sys.exit(1)
    
    # Set environment variables if needed
    os.environ['OPENAI_API_KEY'] = config['llm']['openai_api_key']
    
    # Run the test using the abstract testing tool
    logger.info("Starting intelligent testing")
    
    # Import and use testing_tool instead of directly calling llm_main
    from benchmark_script.testing_tool import run_test
    run_test(
        run_dir=run_dir,
        record=args.record,
        test_case=args.case,
        duration=parse_time(args.time),
        repeat=args.repeat,
        wait_time=args.wait,
        config=config
    )
    
    # Calculate metrics if requested
    results = {}
    
    if args.page_coverage:
        from benchmark_script.page_coverage import calculate_page_coverage
        benchmark_screenshots_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                                               "Benchmark", f"case_{args.case}", "screenshots") if args.case else None
        
        if benchmark_screenshots_dir and os.path.exists(benchmark_screenshots_dir):
            logger.info("Calculating page coverage...")
            screenshots_dir = os.path.join(run_dir, "screenshots")
            results["page_coverage"] = calculate_page_coverage(screenshots_dir, benchmark_screenshots_dir)
            logger.info(f"Page coverage: {results['page_coverage']['coverage_percentage']:.2f}%")
        else:
            logger.warning("Benchmark screenshots directory not found, cannot calculate page coverage")
    
    if args.action_coverage:
        from benchmark_script.action_coverage import calculate_action_coverage
        benchmark_actions_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                                            "Benchmark", f"case_{args.case}", "actions.json") if args.case else None
        
        if benchmark_actions_path and os.path.exists(benchmark_actions_path):
            logger.info("Calculating action coverage...")
            actions_json_path = os.path.join(run_dir, "actions.json")
            results["action_coverage"] = calculate_action_coverage(actions_json_path, benchmark_actions_path)
            logger.info(f"Action coverage: {results['action_coverage']['coverage_percentage']:.2f}%")
        else:
            logger.warning("Benchmark actions file not found, cannot calculate action coverage")
    
    if args.exact_match:
        from benchmark_script.exact_match import calculate_exact_match
        benchmark_actions_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                                            "Benchmark", f"case_{args.case}", "actions.json") if args.case else None
        
        if benchmark_actions_path and os.path.exists(benchmark_actions_path):
            logger.info("Calculating exact match rate...")
            actions_json_path = os.path.join(run_dir, "actions.json")
            results["exact_match"] = calculate_exact_match(actions_json_path, benchmark_actions_path)
            logger.info(f"Exact match rate: {results['exact_match']['match_percentage']:.2f}%")
        else:
            logger.warning("Benchmark actions file not found, cannot calculate exact match rate")
    
    # Save results
    with open(os.path.join(run_dir, "results.json"), "w") as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Test run completed. Results saved to {run_dir}")

if __name__ == "__main__":
    main() 