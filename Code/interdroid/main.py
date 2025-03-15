import configparser
import os
import json
import time
import shutil
from PIL import Image
import base64
import cv2

from llm_api import DashScopeAPI, OpenAIAPI
from record import Record
from logger import Log
# from build_rag_dataset_local import RAGDatasetBuilder
from build_rag_dataset_api import RAGDatasetBuilder
from prompts import *
from utils import *
from actions import *



def main(specified_record=None):
    action_history = []
    original_app = None  # Will be set when recording the first action
    reference_steps_count = 0
    
    # initialize config
    config = configparser.ConfigParser()
    config.read('config.ini')

    llm_client = OpenAIAPI(
        api_key=config['llm']['openai_api_key'],
        model=config['llm']['openai_model']
    )

    # initialize logger
    logger = Log().logger

    android_device = config['uiautomator2']['android_device']
    data_dir = config['data']['data_dir']
    # llm_api_key = config['llm']['llm_api_key']

    # Clear actions directory
    actions_dir = "actions"
    if os.path.exists(actions_dir):
        shutil.rmtree(actions_dir)

    record = Record(android_device)

    logger.info('Initializing ...')
    logger.debug(f"Current Page Info: {record.get_running_info()}")

    # get current step
    current_steps = record.get_current_steps()
    logger.info(f"Current Steps: {current_steps}")

    record.record()

    # get current step
    current_steps = record.get_current_steps()
    logger.info(f"Current Steps: {current_steps}")

    current_screenshot_path = record.get_cur_screenshot_path()
    logger.info(f"Screenshot Path: {current_screenshot_path}")

    current_activity = record.get_cur_activity()
    logger.info(f"Current Activity: {current_activity}")

    current_hierarchy_path = record.get_cur_hierarchy_path()
    logger.info(f"Current Hierarchy Path: {current_hierarchy_path}")

    current_component_path = record.get_cur_components_path()
    logger.info(f"Current Component Info: {current_component_path}")

    
    # If specified_record is provided, use it directly; otherwise use RAG retrieval
    similar_record = specified_record
    if not similar_record:
        # Initialize RAG dataset builder
        rag_builder = RAGDatasetBuilder(data_dir)
        
        # Create temporary directory to store current page information
        temp_dir = "temp_test_app"
        os.makedirs(temp_dir, exist_ok=True)
        
        # Copy current screenshot and hierarchy files to temporary directory
        shutil.copy(current_screenshot_path, os.path.join(temp_dir, "screenshot.png"))
        shutil.copy(current_hierarchy_path, os.path.join(temp_dir, "ui_tree.xml"))
        
        # Find similar application pages
        similar_record = rag_builder.find_similar_app(
            test_app_dir=temp_dir,
            activity_info=current_activity
        )
        
        # Clean up temporary directory
        shutil.rmtree(temp_dir)

    print(similar_record)

    # input("Press Enter to continue...")
    
    if similar_record:
        logger.info(f"Found most similar record: {similar_record}")
        # Can get corresponding operation steps based on similar_record
        similar_record_path = os.path.join(data_dir, similar_record)
        with open(os.path.join(similar_record_path, "record.json"), 'r', encoding='utf-8') as f:
            similar_record_data = json.load(f)
        logger.info(f"Operation steps of similar record: {similar_record_data.get('steps', [])}")
        reference_steps_count = len(similar_record_data.get('steps', []))
    else:
        logger.warning("No similar record found")
    
    # Display concatenated screenshots from retrieved similar record
    if similar_record:
        processed_screenshots_dir = os.path.join(data_dir, similar_record, "processed_screenshots")
        combined_image = combine_images_horizontally(
            processed_screenshots_dir, 
            output_path='combined_screenshots.png'
        )
        
        if combined_image:
            combined_image.show()
            logger.info("Generated and displayed concatenated screenshots")
        else:
            logger.warning(f"Cannot generate concatenated image, please check if directory {processed_screenshots_dir} contains image files")

    # input("Press Enter to continue...")

    # Besides concatenating all images in processed_screenshots, also get the first image separately
    screenshots_dir = os.path.join(data_dir, similar_record, "screenshots")
    first_screenshot_path = os.path.join(screenshots_dir, "step_0.png")

    # Add previous user question and assistant answer to chat_history
    chat_history = []

    # If similar record is found, add it to chat_history as in-context learning example
    if similar_record and os.path.exists('combined_screenshots.png'):

        chat_history.append(
            ("user", [
                first_screenshot_path,
                get_reference_question_prompt(similar_record_data.get('target'))
            ])
        )

        logger.info(("user", [
            first_screenshot_path,
            get_reference_question_prompt(similar_record_data.get('target'))
        ]))
            

        chat_history.append(
            ("assistant", [
                "./combined_screenshots.png",
                get_reference_answer_prompt(similar_record_data.get('target'), similar_record_data.get('steps'))
            ])
        )

        logger.info(("assistant", [
            "./combined_screenshots.png",
            get_reference_answer_prompt(similar_record_data.get('target'), similar_record_data.get('steps'))
        ]))

        chat_history.append(
            ("user", [
                get_thinking_prompt()
            ])
        )

        logger.info(("user", [
            get_thinking_prompt()
        ]))

        response = llm_client.chat_completion(chat_history, max_tokens=1024)

        logger.info(f"LLM response: {response}")

        try:
            inference = response["output"]["choices"][0]["message"]["content"][0]['text']
        except:
            inference = "LLM call failed"

        # print(inference)

        logger.info(inference)

        chat_history.append(
            ("assistant", [
                inference
            ])
        )

        # input("Press Enter to continue...")
    # This processing can shorten context and reduce token consumption
    processed_chat_history = chat_history
        

    # Initialize monitor_feedback
    monitor_feedback = None

    # Modify this part to loop until receiving end instruction
    while True:
        # Reset chat_history to processed_chat_history in each loop
        # This processing can shorten context and reduce token consumption
        chat_history = processed_chat_history
        # Record initial application
        if not original_app and record.get_running_info():
            original_app = record.get_running_info().get('app', '')
            
        with open(current_component_path, 'r', encoding='utf-8') as f:
            current_component_info = json.load(f)
        
        processed_screenshot = cv2.imread(current_screenshot_path)
        components_bounds = [item['bound'] for item in current_component_info]

        processed_screenshot = draw_all_bounds(processed_screenshot, components_bounds)
        
        processed_screenshot_path = 'processed_current_screenshot.png'
        cv2.imwrite(processed_screenshot_path, processed_screenshot)

        chat_history.append(
            ("user", [
                processed_screenshot_path,
                get_action_prompt(
                    similar_record_data.get('target'), 
                    str(current_component_info), 
                    str(action_history),
                    monitor_feedback
                )
            ])
        )

        logger.info(("user", [
            processed_screenshot_path,
            get_action_prompt(
                similar_record_data.get('target'), 
                str(current_component_info), 
                str(action_history),
                monitor_feedback
            )
        ]))

        # Reset monitor_feedback
        monitor_feedback = None
        
        # Call LLM to generate next action
        response = llm_client.chat_completion(chat_history, max_tokens=512)

        logger.info(f"LLM response: {response}")

        # input("Press Enter to continue...")

        try:
            next_steps = response["output"]["choices"][0]["message"]["content"][0]['text']
        except:
            next_steps = "LLM call failed"

        print(next_steps)
        
        json_next_steps = extract_json_from_str(next_steps)
        logger.info(f"LLM suggested next action: {str(json_next_steps)}")
        action_history.append(json_next_steps)

        # Monitoring checkpoint: when receiving end instruction or operation steps exceed reference steps
        if json_next_steps["action_type"] == "end" or len(action_history) > reference_steps_count:
            current_app = record.get_running_info().get('app', '')
            
            monitor_history = [
                ("user", [
                    get_monitor_prompt(
                        similar_record_data.get('target'),
                        str(action_history),
                        reference_steps_count,
                        current_app,
                        original_app
                    )
                ])
            ]

            print("monitor running...")
            
            monitor_response = llm_client.chat_completion(monitor_history, max_tokens=512)
            
            try:
                monitor_result = monitor_response["output"]["choices"][0]["message"]["content"][0]['text']
                monitor_result = extract_json_from_str(monitor_result)
                    
                logger.info(f"Monitor analysis: {monitor_result}")
                
                if monitor_result["recommendation"] == "truly_complete":
                    logger.info("Task fully completed and back in original app")
                    break
                elif monitor_result["recommendation"] == "return_to_original_app":
                    logger.info("Task completed but need to return to original app")
                    monitor_feedback = "Task is completed but we need to return to the original app. Please generate actions to navigate back."
                    continue
                elif monitor_result["recommendation"] == "continue":
                    logger.info("Task not completed, continuing execution")
                    if json_next_steps["action_type"] == "end":
                        continue
            except Exception as e:
                logger.error(f"Error parsing monitor response: {e}")
                print(monitor_response)
                
        if json_next_steps["action_type"] == "end" and not monitor_feedback:
            logger.info("Task completed, received end instruction")
            break

        action_type = json_next_steps["action_type"]
        action_detail = json_next_steps["action_detail"]

        if action_type == "click" or action_type == "press":
            click_item = {}
            with open(current_component_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                print(data)
                for each in data:
                    if each['id'] == int(action_detail):
                        click_item = each

            print(click_item)

            bound = click_item['bound']

            draw_bounds(record.current_steps, bound)

            if action_type == "click":
                click_node(bound, record.device_name)
            else:
                press_node(bound, record.device_name)
        else:
            if action_type == "swipe":
                begin_bound = None
                if 'begin_component_id' in action_detail:
                    with open(current_component_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        for each in data:
                            if each['id'] == int(action_detail['begin_component_id']):
                                begin_bound = each['bound']
                                break
                
                draw_swipe_action(record.current_steps, begin_bound, action_detail['direction'])
                
                swipe(record.device_name, 
                      action_detail['direction'], 
                      int(action_detail['distance']),
                      begin_bound)
            elif action_type == "keyboard_input":
                draw_text_action(record.current_steps, f"Input: {action_detail}")
                keyboard_input(action_detail, record.device_name)
            elif action_type == "special_action":
                draw_text_action(record.current_steps, f"Special Action: {action_detail['action_type']}")
                special_action(action_detail['action_type'], record.device_name)
            else:
                raise ValueError(f"action type {action_type} not supported")
        
        # After executing an action, need to get current page information again
        time.sleep(3)  # Wait for page loading
        record.record()
        current_screenshot_path = record.get_cur_screenshot_path()
        current_hierarchy_path = record.get_cur_hierarchy_path()
        current_component_path = record.get_cur_components_path()
        logger.info(f"Updated page information - Screenshot path: {current_screenshot_path}")



if __name__ == "__main__":
    # Can specify similar_record directly or not
    main()  # Not specified, use RAG retrieval
    # main("record_xxx")  # Directly specify record folder name, just for testing

