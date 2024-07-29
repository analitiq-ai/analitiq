from analitiq.logger.logger import logger
import os
import importlib.util
import re


class ServicesLoader:
    """
    ConfigLoader is responsible for loading configuration files
    and dynamically importing the specified services.
    """

    def parse_doc_string(self, doc_string):
        """Parses the doc string to extract input and output information.

        Args:
            doc_string (str): The documentation string of a method.

        Returns:
            tuple: A tuple containing lists of inputs and outputs.
        """
        inputs, outputs = [], []
        lines = doc_string.split('\n')
        mode = None
        for line in lines:
            if 'Args:' in line:
                mode = 'inputs'
            elif 'Parameters:' in line:
                mode = 'inputs'
            elif 'Returns:' in line:
                mode = 'outputs'
            elif mode == 'inputs' and line.strip():
                inputs.append(line.strip())
            elif mode == 'outputs' and line.strip():
                outputs.append(line.strip())

        return inputs, outputs

    @staticmethod
    def load_service_class(service_config: dict) -> bool:

        """
        This class runs checks on a service:
        1. whether service file and class exist
        2. whether it has the defined method.
        3. whether it is a duplicate of an existing service
        4. extract input and output definition from description

        Parameters:
        - service_config (dict): A dictionary containing the service configuration.

        Returns:
        - bool: True if all checks passed and service exists.

        Raises:
        - FileNotFoundError: If the specified file does not exist.
        - AttributeError: If the specified class or method does not exist within the file.
        - ValueError: If the service name is duplicate or invalid.
        """
        service_path = service_config['path']
        class_name = service_config['class']
        method_name = service_config['method']

        if not os.path.exists(service_path):
            raise FileNotFoundError(f"The specified service file does not exist: {service_path}")

        if not re.match("^[a-zA-Z0-9_-]+$", service_config['name']):
            raise ValueError(f"Invalid service name: {service_config['name']}")

        spec = importlib.util.spec_from_file_location(class_name, service_path)
        module = importlib.util.module_from_spec(spec)

        try:
            spec.loader.exec_module(module)
        except Exception as e:
            msg = f"Error loading service '{class_name}': {e}"
            raise ImportError(msg)
            logger.error(msg)
            return
        else:
            # Retrieve the class from the module using the constructed class name
            if hasattr(module, class_name):
                service_class = getattr(module, class_name, None)
            else:
                raise AttributeError(f"Class '{class_name}' not found in module '{service_path}'.")

        if method_name and not hasattr(service_class, method_name):
            raise AttributeError(f"The specified method '{method_name}' does not exist in the class '{class_name}'")

        return service_class

    def load_services_from_config(self, config: dict) -> dict:
        """
        Loads all services defined in the configuration file.

        Parameters:
        - config (dict): The config dictionary

        Returns:
        - dict: Dictionary of verified services

        Example:
            Services = {
                'ChartService': {
                    'name': 'ChartService',
                    'description': 'Class that represents a service to generate JavaScript charts based on user input and data.',
                    'path': 'analitiq/services/chart/chart.py',
                    'class': 'Chart',
                    'method': 'run',
                    'class_docstring_description': 'Class that represents a service to generate JavaScript charts based on user input and data.\n\nThis class determines the appropriate chart type for given data, and generates\nthe corresponding JavaScript chart code.',
                    'inputs': ["user_prompt (str): The user's description of the desired chart.", 'service_input: The input data for chart generation, either as a DataFrame or a pickled string.'],
                    'outputs': ['Response: An object containing the generated chart code and metadata.']
                },
                'MyCustomService': {
                    'name': 'MyCustomService',
                    'description': '',
                    'path': 'custom_services/my_service.py',
                    'class': 'MyService',
                    'method': 'run',
                    'class_docstring_description': None,
                    'inputs': ['- service_config (dict): A dictionary containing the service configuration.'],
                    'outputs': ['- bool: True if all checks passed and service exists.', 'Raises:', '- FileNotFoundError: If the specified file does not exist.', '- AttributeError: If the specified class or method does not exist within the file.', '- ValueError: If the service name is duplicate or invalid.']
                }
            }
        """

        verified_services = {}

        if 'services' not in config:
            logger.info("No Services found in Project config.")
            raise KeyError("No Services found in Project config.")
        else:
            for service in config['services']:
                logger.info(f"Loading service {service['name']}")

                try:
                    service_class = self.load_service_class(service)
                except (FileNotFoundError, ValueError, AttributeError, ImportError) as e:
                    # Log and display the error without breaking the execution
                    logger.error(e)
                    print(e)  # Displaying the error to the end user
                else:
                    verified_services[service['name']] = service
                    verified_services[service['name']]['class_inst'] = service_class

        return verified_services



