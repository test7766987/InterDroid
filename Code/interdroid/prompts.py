def get_action_prompt(task: str, component_info: str, action_history: str, monitor_feedback: str = None):
    prompt = f"""
## Role
You are an Android app tester. 
Please refer to the examples in the previous conversations to complete the cross-app task testing for the current app.
The current screenshot is a screen capture, with red boxes highlighting the clickable components. The numbers in the top-left corner of the red boxes represent the component IDs.

## Task
You are given a screenshot of an Android app and a task description.
You need to perform a series of coherent operations on this app to ultimately achieve the goal of the task.
The task: {task}

## Action History
{action_history}

## Component Information
{component_info}
"""

    if monitor_feedback:
        prompt += f"""
## Monitor Feedback
{monitor_feedback}
"""

    prompt += f"""
## Rules
You can choose one of the following actions: "click", "press", "swipe", "keyboard_input", "special_action"
"keyboard_input" refers to keyboard input (please note that often you need to click on an input-supporting component first in order to start typing).
"special_action" includes four actions: 'KEY_BACK', 'KEY_HOME', and 'KEY_ENTER'.KEY_BACK corresponds to returning to the previous page, KEY_HOME indicates returning to the system's HOME desktop, and KEY_ENTER represents the Enter key. After finishing input, pressing Enter may directly trigger the signal indicating that input is complete.
Please output the next operation in JSON format.

"""
    prompt +=  """
## Expected Output
```json
{
    "action_type": "click",
    "action_detail": "1(just the id of the component to click)",
    "action_description": "the description of the action"
}
```
or
```json
{
    "action_type": "press",
    "action_detail": "1(just the id of the component to press)",
    "action_description": "the description of the action"
}
```
or
```json
{
    "action_type": "swipe",
    "action_detail": {
        "direction": "up/down/left/right",
        "begin_component_id": "1(just the id of the component to begin swipe)",
        "distance": "200(the distance of the swipe)"
    },
    "action_description": "the description of the action"
}
```
or
```json
{
    "action_type": "keyboard_input",
    "action_detail": "the keyboard input content",
    "action_description": "the description of the action"
}
```
(Please note that you often need to click on the input box first before you can start typing.)
or
```json
{
    "action_type": "special_action",
    "action_detail": "KEY_BACK/KEY_HOME/KEY_ENTER",
    "action_description": "the description of the action"
}
```
or
```json
{
    "action_type": "end",
    "action_detail": "end",
    "action_description": "the action is to end the current task"
}
```
"""
    return prompt

SYSTEM_PROMPT = """Here is an example of an operation with a similar path, demonstrating how to conduct a cross-application test (navigating from Application A to Application B and then back to Application A).
Please refer to this example to operate the current application interface.
"""

def get_reference_question_prompt(task: str):
    return f"""
You are an Android app tester.
Please start testing from this page, and the final goal is to complete the "{task}" functionality.
"""


def get_reference_answer_prompt(task: str, steps: list):
    steps_str = ""
    for step in steps:
        steps_str += f"Step {step['step_id']}: {step['action_type']} {str(step['action_detail'])}\n"

    return f"""
To complete the "{task}" functionality, you need to perform the following steps:
{steps_str}
"""

def get_thinking_prompt():
    return """
Please think step by step. 
In the previous chat history, what task was being performed with the given example? 
What operations were carried out at each step, and why were these steps taken to accomplish the task?
"""


def get_monitor_prompt(task: str, action_history: str, reference_steps_count: int, current_app: str, original_app: str):
    prompt = f"""
## Task Progress Monitor
You are monitoring the progress of an Android app testing task.

Original task: {task}
Total actions taken: {len(action_history)}
Reference steps count: {reference_steps_count}
Current app: {current_app}
Original app being tested: {original_app}

## Action History
{action_history}

## Analysis Required
1. Has the main task been completed successfully? Please explain why.
2. Are we currently in the original app that was being tested ({original_app})?
3. What should be the next step?

Please provide your analysis in the following JSON format:
"""
    prompt += """
```json
{
    "task_completed": true/false,
    "in_original_app": true/false,
    "analysis": "Your detailed analysis here",
    "recommendation": "continue/return_to_original_app/truly_complete",
    "reason": "Explain your recommendation"
}
```
"""
    return prompt
