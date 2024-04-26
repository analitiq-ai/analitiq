import logging
import pprint


class TaskManager:

    def create_task_list(self, llm, prompts: dict, avail_services_str: str):
        """
        :param llm: An instance of the LLM class that provides the methods to create a task list.
        :param prompts: A dictionary containing the prompts required to create the task list. The dictionary should have the following keys:
            - 'refined': A list of refined prompts (optional).
            - 'hints': A list of hints for the prompts (optional).
            - 'original': A list of original prompts.
        :param avail_services_str: A string representing available services.

        :return: The generated task list.
        """

        if len(prompts['refined']) > 10 and len(prompts['hints']) > 10:
            tasks_list = llm.llm_create_task_list_w_hints(prompts['refined'], prompts['hints'], avail_services_str)
        elif len(prompts['refined']) > 10:
            tasks_list = llm.llm_create_task_list(prompts['refined'], avail_services_str)
        else:
            tasks_list = llm.llm_create_task_list(prompts['original'], avail_services_str)

        # Ensure the list is not empty to avoid IndexError
        if not tasks_list:
            return False

        logging.info(f"Task list: {tasks_list}")
        # Convert list of objects into a dictionary where name is the key and description is the value

        return tasks_list

    def refine_tasks_until_stable(self, llm, user_prompt: str, tasks_list, iter_limit: int = 5):
        """
        This task list refiner works by asking LLM to refine a list of tasks until it can do no further refinement.
        :param llm: llm object
        :param user_prompt:
        :param tasks_list:
        :param iter_limit: Limit to how many interactions or checking we want to do.
        :return:
        """
        num_tasks = len(tasks_list)
        i = 0
        refined_tasks_list = "\n".join(f"{task.Name}: {task.Description} using {task.Using}." for task in tasks_list)
        response = llm.llm_refine_task_list(user_prompt, refined_tasks_list)

        while num_tasks != len(response.TaskList):
            num_tasks = len(response.TaskList)
            logging.info(f"\nModel input list of tasks [Iteration {i}][Tasks: {len(response.TaskList)}]: \n {refined_tasks_list}")
            response = llm.llm_refine_task_list(user_prompt, refined_tasks_list)

            # make task list from list of objects into a string
            refined_tasks_list = "\n".join(f"{task.Name}: {task.Description} using {task.Using}." for task in response.TaskList)
            logging.info(f"\n[Tasks][Combine][Iteration: {i}][Tasks: {len(response.TaskList)}]: \n {refined_tasks_list}")

            i = i+1

            if i >= iter_limit:
                logging.warning(f"Too many iterations of task optimisations: {i}")
                dict = {item.Name: {'Name': item.Name, 'Using': item.Using, 'Description': item.Description} for item in response.TaskList}
                return dict

                # Convert list of objects into a dictionary where name is the key and description is the value
        dict = {item.Name: {'Name': item.Name, 'Using': item.Using, 'Description': item.Description} for item in response.TaskList}

        return dict

    def combine_tasks_pairwise(self, llm, user_prompt, tasks):
        """
        Combine tasks pairwise based on a shared "Using" attribute and validation from llm_combine_tasks_pairwise.

        :param tasks: Dictionary of tasks.
        :return: Updated dictionary of tasks after combinations.
        """
        # Convert dictionary to list for easier manipulation
        task_items = list(tasks.items())
        i = 0
        while i < len(task_items) - 1:
            main_task_key, main_task = task_items[i]
            secondary_task_key, secondary_task = task_items[i+1]

            # Ensure both tasks use the same technology or tool
            if main_task['Using'] == secondary_task['Using']:
                response = llm.llm_combine_tasks_pairwise(main_task, secondary_task)
                if response == "Can combine tasks.":
                    # Append the description of the secondary task to the main task
                    main_task['Description'] += ". " + secondary_task['Description']
                    # Remove the secondary task from the list
                    task_items.pop(i+1)
                else:
                    # If tasks cannot be combined, move to the next task as the new main task
                    i += 1
            else:
                # Move to the next task as the new main task if 'Using' values differ
                i += 1

        # Convert list back to dictionary
        return dict(task_items)