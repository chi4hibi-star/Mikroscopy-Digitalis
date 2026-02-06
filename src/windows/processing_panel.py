import numpy as np
from scipy.ndimage import sobel,uniform_filter
from typing import Dict, Any, List, Optional, Union
from traceback import print_exc

class PipelineExecutor:
    """
    Executes image processing pipelines defined by node graphs
    
    Takes a pipeline definition (nodes + connections) and processes
    images through the pipeline, executing each node's operation.
    """
    
    def __init__(self, pipeline_data: Dict[str, Any]):
        """
        Initialize the pipeline executor
        
        Args:
            pipeline_data: Dictionary containing 'nodes' and 'connections'
        """
        self.pipeline_data = pipeline_data
        self.nodes = pipeline_data.get('nodes', [])
        self.connections = pipeline_data.get('connections', [])
        self.execution_order = self._build_execution_order()
        self.node_map = {node['id']: node for node in self.nodes}
        return

    def execute(self, input_image: np.ndarray) -> Union[np.ndarray, Dict[str, Any]]:
        """
        Execute the pipeline on an input image
        
        Args:
            input_image: Input image as numpy array (H, W, C)
            
        Returns:
            Processed image as numpy array, or dict with 'image' and 'data' keys
        """
        node_outputs = {}
        input_node_id = None
        for node in self.nodes:
            if node.get('node_type') == 'input':
                input_node_id = node['id']
                node_outputs[input_node_id] = {'image': input_image}
                break
        if input_node_id is None:
            raise ValueError("No input node found in pipeline")
        for node_id in self.execution_order:
            node = self.node_map[node_id]
            node_type = node.get('node_type')
            if node_type == 'input':
                continue
            inputs = self._get_node_inputs(node_id, node_outputs)
            try:
                if node_type == 'output':
                    node_outputs[node_id] = inputs
                elif node_type == 'process':
                    result = self._execute_process_node(node, inputs)
                    node_outputs[node_id] = result
                elif node_type == 'algorithm':
                    result = self._execute_algorithm_node(node, inputs)
                    node_outputs[node_id] = result
                else:
                    print(f"Unknown node type: {node_type}")
                    node_outputs[node_id] = inputs
            except Exception as e:
                print(f"Error executing node {node.get('name', node_id)}: {e}")
                print_exc()
                node_outputs[node_id] = inputs
        output_node_id = None
        for node in self.nodes:
            if node.get('node_type') == 'output':
                output_node_id = node['id']
                break
        if output_node_id and output_node_id in node_outputs:
            result = node_outputs[output_node_id]
            if 'data' in result and result['data'] is not None:
                return {
                    'image': result.get('image'),
                    'data': result.get('data')
                }
            else:
                return result.get('image')
        return input_image
    
    def _build_execution_order(self) -> List[str]:
        """
        Build topological execution order for nodes
        
        Returns:
            List of node IDs in execution order
        """
        order = []
        visited = set()
        input_node = None
        for node in self.nodes:
            if node.get('node_type') == 'input':
                input_node = node
                break
        if not input_node:
            return [node['id'] for node in self.nodes]
        queue = [input_node['id']]
        visited.add(input_node['id'])
        order.append(input_node['id'])
        while queue:
            current_id = queue.pop(0)
            for conn in self.connections:
                if conn['from_node'] == current_id:
                    to_node_id = conn['to_node']
                    if to_node_id not in visited:
                        visited.add(to_node_id)
                        order.append(to_node_id)
                        queue.append(to_node_id)
        for node in self.nodes:
            if node['id'] not in visited:
                order.append(node['id'])
        return order
    
    def _get_node_inputs(self, node_id: str, node_outputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get inputs for a node from previous nodes' outputs
        
        Args:
            node_id: ID of the node
            node_outputs: Dictionary of previous nodes' outputs
            
        Returns:
            Dictionary mapping parameter names to values
        """
        inputs = {}
        for conn in self.connections:
            if conn['to_node'] == node_id:
                from_node_id = conn['from_node']
                to_parameter = conn.get('to_parameter', 'image')
                from_output = conn.get('from_output', 'image')
                if from_node_id in node_outputs:
                    prev_output = node_outputs[from_node_id]
                    if isinstance(prev_output, dict):
                        value = prev_output.get(from_output)
                    else:
                        value = prev_output
                    inputs[to_parameter] = value
        return inputs
    
    def _execute_process_node(self, node: Dict[str, Any], inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a process node operation
        
        Args:
            node: Node data dictionary
            inputs: Input values for the node
            
        Returns:
            Dictionary with 'image' and optionally 'data' keys
        """
        node_name = node.get('name', 'unknown')
        parameters = node.get('parameters', {})
        input_image = inputs.get('image')
        if input_image is None:
            return {'image': None, 'data': None}
        try:
            if node_name == "Grayscale":
                output_image = self._op_grayscale(input_image, parameters)
                return {'image': output_image, 'data': None}
            elif node_name == "Blur":
                output_image = self._op_blur(input_image, parameters)
                return {'image': output_image, 'data': None}
            elif node_name == "Threshold":
                output_image = self._op_threshold(input_image, parameters)
                return {'image': output_image, 'data': None}
            elif node_name == "Edge Detection":
                output_image = self._op_edge_detection(input_image, parameters)
                return {'image': output_image, 'data': None}
            elif node_name == "Brightness":
                output_image = self._op_brightness(input_image, parameters)
                return {'image': output_image, 'data': None}
            elif node_name == "Contrast":
                output_image = self._op_contrast(input_image, parameters)
                return {'image': output_image, 'data': None}
            else:
                print(f"Unknown operation: {node_name}, passing through")
                return {'image': input_image, 'data': None}
        except Exception as e:
            print(f"Error in operation {node_name}: {e}")
            print_exc()
            return {'image': input_image, 'data': None}
    
    def _execute_algorithm_node(self, node: Dict[str, Any], inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute an algorithm node (nested pipeline)
        
        Args:
            node: Node data dictionary
            inputs: Input values for the node
            
        Returns:
            Dictionary with 'image' and optionally 'data' keys
        """
        pipeline_data = node.get('pipeline_data', {})
        if not pipeline_data:
            print("Algorithm node has no pipeline data")
            return inputs
        sub_executor = PipelineExecutor(pipeline_data)
        input_image = inputs.get('image')
        if input_image is None:
            return {'image': None, 'data': None}
        result = sub_executor.execute(input_image)
        if isinstance(result, dict):
            return result
        else:
            return {'image': result, 'data': None}
    
    def _op_grayscale(self, image: np.ndarray, params: Dict[str, Any]) -> np.ndarray:
        """Convert image to grayscale"""
        if len(image.shape) == 2:
            return image
        gray = np.dot(image[..., :3], [0.299, 0.587, 0.114])
        return np.stack([gray, gray, gray], axis=-1).astype(np.uint8)
    
    def _op_blur(self, image: np.ndarray, params: Dict[str, Any]) -> np.ndarray:
        """Apply blur filter"""
        kernel_size = params.get('kernel_size', 5)
        blurred = uniform_filter(image, size=(kernel_size, kernel_size, 1))
        return blurred.astype(np.uint8)
    
    def _op_threshold(self, image: np.ndarray, params: Dict[str, Any]) -> np.ndarray:
        """Apply threshold"""
        threshold = params.get('threshold', 128)
        if len(image.shape) == 3:
            gray = np.dot(image[..., :3], [0.299, 0.587, 0.114])
        else:
            gray = image
        binary = (gray > threshold).astype(np.uint8) * 255
        return np.stack([binary, binary, binary], axis=-1)
    
    def _op_edge_detection(self, image: np.ndarray, params: Dict[str, Any]) -> np.ndarray:
        """Apply edge detection"""
        if len(image.shape) == 3:
            gray = np.dot(image[..., :3], [0.299, 0.587, 0.114])
        else:
            gray = image
        sx = sobel(gray, axis=0)
        sy = sobel(gray, axis=1)
        edges = np.hypot(sx, sy)
        edges = (edges / edges.max() * 255).astype(np.uint8)
        return np.stack([edges, edges, edges], axis=-1)
    
    def _op_brightness(self, image: np.ndarray, params: Dict[str, Any]) -> np.ndarray:
        """Adjust brightness"""
        brightness = params.get('brightness', 0)  # -100 to +100
        adjusted = np.clip(image.astype(np.int16) + brightness, 0, 255)
        return adjusted.astype(np.uint8)
    
    def _op_contrast(self, image: np.ndarray, params: Dict[str, Any]) -> np.ndarray:
        """Adjust contrast"""
        contrast = params.get('contrast', 1.0)  # 0.5 to 2.0
        adjusted = np.clip((image.astype(np.float32) - 128) * contrast + 128, 0, 255)
        return adjusted.astype(np.uint8)