from concurrent.futures import ThreadPoolExecutor, as_completed
from analitiq.logger.logger import logger
import inspect
import json


class InvalidServiceNameException(Exception):
    """Exception raised for invalid service names."""


class ServiceNotFoundException(Exception):
    """Exception raised when a service is not found."""


class Node:
    """Represents a node in the execution graph, encapsulating a service."""

    def __init__(self, service_name, service_path, instructions):
        """Initializes a node with the service it represents (by name), its own name, and a shared context.

        Args:
        ----
            service_name (str): The fully qualified name of the service class this node represents,
                                including the module and class name (e.g., 'your_module.ServiceA').
            name (str): The name of the node, typically matching the service it represents.
            context (Context): A context object containing shared resources like the database engine.

        """
        self.service_name = service_name  # Store the service name for dynamic loading
        self.name = service_name
        self.instructions = instructions  # instructions for this node
        self.path = service_path  # the service path that is invoked importlib
        self.dependencies = []  # List of node names this node depends on
        self.consumers = []  # List of Node instances that depend on this node

    def add_dependency(self, dependency_node):
        """Adds a dependency to this node. This node's execution will wait until the dependency node has been executed.

        Args:
        ----
            dependency_node (Node): Another node that this node depends on.

        """
        self.dependencies.append(dependency_node)
        dependency_node.consumers.append(self)


class Graph:
    """Manages the execution graph of services based on their dependencies."""

    def __init__(self, available_services, db, llm, vdb):
        """Initialize the class instance.

        :param available_services: A list of available services.
        :param db: The database instance.
        :param llm: The large language model instance.
        :param vdb: The vector database instance.
        """
        self.available_services = available_services
        self.nodes = {}
        self.db = db
        self.llm = llm
        self.vdb = vdb

    def add_node(self, service, details):
        """Adds a node to the graph.

        Args:
        ----
            node (Node): The node to add to the graph.

        """
        if service not in self.available_services:
            logger.warning(f"Trying to add non existent service: {service}")
            return
        node = Node(
            service, self.available_services[service]["path"], details["Instructions"]
        )

        self.nodes[node.name] = node

    def build_service_dependency(self, selected_services):
        # Then, set up dependencies based on the JSON response
        for service, details in selected_services.items():
            if len(details["DependsOn"]) > 0:
                try:
                    dependency_node = self.nodes.get(service)
                except Exception as e:
                    logger.warning(f"Dep node not found: {dependency_node}. {e}")

                for master_name in details["DependsOn"]:
                    try:
                        master_node = self.nodes.get(
                            master_name
                        )  # Retrieve the node from temporary storage
                    except Exception as e:
                        logger.warning(f"Dep node not found: {dependency_node}. {e}")

                    if master_node and dependency_node:
                        dependency_node.add_dependency(master_node)

    def run(self, services):
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
            ready_nodes = [
                node for node in self.nodes.values() if not node.dependencies
            ]

            while ready_nodes or futures_to_nodes:
                # Execute all ready nodes
                for node in ready_nodes:
                    if (
                        node.name not in executed_nodes
                    ):  # Check if node has been executed
                        logger.info(
                            f"[Service][Run]: {node.name}\n Prompt: {node.instructions} \n Inputs: {node_outputs!s}"
                        )  # Print the current node being executed

                        future = executor.submit(
                            self.run_service,
                            node,
                            services[node.name]["class_inst"],
                            node.instructions,
                            node_outputs,
                        )
                        futures_to_nodes[future] = node
                        executed_nodes.add(node.name)  # Mark node as executed
                ready_nodes.clear()

                # Wait for at least one node to complete
                for future in as_completed(futures_to_nodes):
                    completed_node = futures_to_nodes.pop(
                        future
                    )  # Pop to prevent re-execution
                    result = future.result()

                    # Store the result for dependent nodes as a BaseResponse object.
                    # node_outputs[completed_node.name] = result if result.content is not None else None

                    # Store the result for dependent nodes as a JSON.
                    node_outputs[completed_node.name] = (
                        result.to_json() if result.content is not None else None
                    )

                    # Check and schedule dependent nodes
                    for consumer in completed_node.consumers:
                        if (
                            all(
                                dep.name in node_outputs
                                and node_outputs[dep.name] is not None
                                for dep in consumer.dependencies
                            )
                            and consumer.name not in executed_nodes
                        ):  # Check if consumer has been executed
                            ready_nodes.append(consumer)

        return node_outputs  # Return the aggregated results

    def run_service(self, node, service_class, user_prompt=None, node_outputs=None):
        """Instantiates and runs a node's service, passing necessary parameters."""
        # Assuming dynamic loading if necessary or direct instantiation

        # Get the signature of the __init__ method
        init_signature = inspect.signature(service_class.__init__)

        # Get the parameters of the __init__ method
        init_params = init_signature.parameters

        # Prepare parameters
        params = {}

        for name in init_params:
            # print(f"Parameter: {name} - Default: {param.default}")
            if name == "db":
                params["db"] = self.db

            elif name == "llm":
                params["llm"] = self.llm

            elif name == "vdb":
                params["vdb"] = self.vdb

        # here we pass the prompt
        service_instance = service_class(**params)

        # Prepare parameters
        params = {}
        sig = inspect.signature(service_instance.run)
        if "user_prompt" in sig.parameters:
            params["user_prompt"] = user_prompt
        if "service_input" in sig.parameters:
            # Aggregate inputs from dependencies
            inputs = [
                node_outputs[dep.name]
                for dep in node.dependencies
                if dep.name in node_outputs
            ]
            params["service_input"] = inputs if inputs else None

        response = service_instance.run(**params)
        logger.info(f"Response from service {node.service_name}: {response}")
        # if we have a response with some data from a services, it will be structured as BaseResponse object

        return response

    def get_dependency_tree(self):
        """Prints the dependency tree of the graph."""

        def create_tree(node, level=0):
            tree = {"name": node.name, "level": level, "consumers": []}
            for consumer in node.consumers:
                tree["consumers"].append(create_tree(consumer, level + 1))
            return tree

        # Start from nodes without dependencies and print the tree
        root_nodes = [node for node in self.nodes.values() if not node.dependencies]
        trees = [create_tree(node) for node in root_nodes]
        tree_text = ""
        for branch in trees:
            tree_text = tree_text + json.dumps(branch)
        logger.info(f"Node Dependency: {tree_text}")
