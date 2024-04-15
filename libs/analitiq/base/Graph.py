from concurrent.futures import ThreadPoolExecutor, as_completed
import importlib
import os
import logging
import json
import importlib.util
import inspect
import pandas as pd

class InvalidServiceNameException(Exception):
    """Exception raised for invalid service names."""
    pass


class ServiceNotFoundException(Exception):
    """Exception raised when a service is not found."""
    pass


class Node:
    """Represents a node in the execution graph, encapsulating a service."""

    def __init__(self, service_name, service_path, instructions):
        """
        Initializes a node with the service it represents (by name), its own name, and a shared context.

        Args:
            service_name (str): The fully qualified name of the service class this node represents,
                                including the module and class name (e.g., 'your_module.ServiceA').
            name (str): The name of the node, typically matching the service it represents.
            context (Context): A context object containing shared resources like the database engine.
        """
        self.service_name = service_name  # Store the service name for dynamic loading
        self.name = service_name
        self.instructions = instructions # instructions for this node
        self.path = service_path # the service path that is invoked importlib
        self.dependencies = []  # List of node names this node depends on
        self.consumers = []  # List of Node instances that depend on this node

    def add_dependency(self, dependency_node):
        """
        Adds a dependency to this node. This node's execution will wait until the dependency node has been executed.

        Args:
            dependency_node (Node): Another node that this node depends on.
        """
        self.dependencies.append(dependency_node)
        dependency_node.consumers.append(self)


class Graph:
    """Manages the execution graph of services based on their dependencies."""

    def __init__(self, available_services):
        """
        Initializes the graph with a shared database engine.

        Args:
            db_engine: The database engine available to all services in the graph.
        """
        self.available_services = available_services
        self.nodes = {}

    def add_node(self, node):
        """
        Adds a node to the graph.

        Args:
            node (Node): The node to add to the graph.
        """
        self.nodes[node.name] = node

    def get_service_class(self, service_name):
        """Get the class inside the given service's directory.
        TODO this is a duplicate of load_service in ProjectLoader
        """
        service = self.available_services.get(service_name)

        if not service:
            raise ServiceNotFoundException(f"Service '{service_name}' not found in available services.")

        if not os.path.exists(service['path']):
            raise FileNotFoundError(f"{service['path']} not found for service '{service_name}'.")

        # Dynamically import the module from the given path
        spec = importlib.util.spec_from_file_location(service['class'], service['path'])
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # Retrieve the class from the module using the constructed class name
        if hasattr(module, service['class']):
            return getattr(module, service['class'])
        else:
            raise AttributeError(f"Class '{service['class']}' not found in module '{service_name}.base'.")

    def run(self):
        """Executes the graph, respecting node dependencies, and allows for parallel execution.
        Key Assumptions:
        Parallel Execution: Nodes without dependencies are submitted for execution immediately. As each node completes, its output is stored, and the executor checks if dependent (consumer) nodes are ready to be executed (i.e., all their dependencies have completed). This allows for parallel execution where possible.

        Dynamic Parameter Passing: When executing a service, parameters (user_prompt and service_input) are dynamically passed based on the service method's signature. This flexible approach caters to different service requirements.

        Handling Multiple Dependencies: When a node has multiple dependencies, the outputs of all dependencies are collected into a list and passed as service_input. This approach assumes that services designed to accept inputs from multiple nodes can handle a list of inputs.

        """
        # Initialize execution queue with nodes having no dependencies

        with ThreadPoolExecutor() as executor:
            futures_to_nodes = {}
            node_outputs = {}
            executed_nodes = set()  # Track executed nodes

            # Identify initially ready nodes (no dependencies)
            ready_nodes = [node for node in self.nodes.values() if not node.dependencies]

            while ready_nodes or futures_to_nodes:
                # Execute all ready nodes
                for node in ready_nodes:
                    if node.name not in executed_nodes:  # Check if node has been executed
                        logging.debug(f"\n\n==== RUNNING SERVICE: {node.name}\n Prompt: {node.instructions} \n Inputs: {str(node_outputs)}")  # Print the current node being executed

                        future = executor.submit(self.run_service, node, node.instructions, node_outputs)
                        futures_to_nodes[future] = node
                        executed_nodes.add(node.name)  # Mark node as executed
                ready_nodes.clear()

                # Wait for at least one node to complete
                for future in as_completed(futures_to_nodes):
                    completed_node = futures_to_nodes.pop(future)  # Pop to prevent re-execution
                    result = future.result()

                    if isinstance(result, pd.DataFrame):
                        # Serializing with JSON
                        result_formatted = result.to_json(orient="split")
                        node_outputs[completed_node.name] = str(result_formatted)  # Store the result for dependent nodes
                    else:
                        result_formatted = result
                        node_outputs[completed_node.name] = str(result_formatted)  # Store the result for dependent nodes

                    # Check and schedule dependent nodes
                    for consumer in completed_node.consumers:
                        if all(dep.name in node_outputs for dep in consumer.dependencies):
                            if consumer.name not in executed_nodes:  # Check if consumer has been executed
                                ready_nodes.append(consumer)

        return node_outputs  # Return the aggregated results

    def run_service(self, node, user_prompt=None, node_outputs=None):
        """Instantiates and runs a node's service, passing necessary parameters."""
        # Assuming dynamic loading if necessary or direct instantiation

        service_class = self.get_service_class(node.service_name)

        # here we do not pass anything when instantiating a service class because global object management is done through a BaseService class
        service_instance = service_class()

        # Prepare parameters
        params = {}
        sig = inspect.signature(service_instance.run)
        if 'user_prompt' in sig.parameters:
            params['user_prompt'] = user_prompt
        if 'service_input' in sig.parameters:
            # Aggregate inputs from dependencies
            inputs = [node_outputs[dep.name] for dep in node.dependencies if dep.name in node_outputs]
            params['service_input'] = inputs if inputs else None

        response = service_instance.run(**params)
        logging.info(f"Response from service {node.service_name}: {response}")
        # if we have a response with some data from LLM, it will be in response.content
        # but if there is no data, then there could a response of False or just None, so we pass that
        if response is not None and response.content is not None:
            return response.content

        return response

    def get_dependency_tree(self):
        """Prints the dependency tree of the graph."""
        def print_tree(node, level=0):
            indent = "  " * level  # Indentation to represent tree structure
            logging.info(f"{indent}- {node.name}")
            for consumer in node.consumers:
                print_tree(consumer, level + 1)

        # Start from nodes without dependencies and print the tree
        root_nodes = [node for node in self.nodes.values() if not node.dependencies]
        logging.info("Node Dependency Tree:")
        for node in root_nodes:
            print_tree(node)