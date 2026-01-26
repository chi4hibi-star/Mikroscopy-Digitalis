from pygame import surfarray
import numpy as np
from traceback import print_exc
from cv2 import (GaussianBlur,medianBlur,bilateralFilter,filter2D, 
                 Canny,Sobel,Laplacian,erode,dilate,morphologyEx,
                 threshold,adaptiveThreshold,getRotationMatrix2D,warpAffine,
                 resize,INTER_LINEAR,MORPH_OPEN,MORPH_CLOSE,THRESH_BINARY,THRESH_OTSU,
                 ADAPTIVE_THRESH_MEAN_C,fastNlMeansDenoisingColored,fastNlMeansDenoising,
                 Scharr,dft,idft,DFT_COMPLEX_OUTPUT,getGaborKernel,CV_32F,
                 MORPH_RECT,MORPH_ELLIPSE,MORPH_CROSS,getStructuringElement,
                 MORPH_GRADIENT,MORPH_BLACKHAT,MORPH_TOPHAT,BORDER_CONSTANT,
                 BORDER_REPLICATE,BORDER_REFLECT,BORDER_WRAP,undistort, 
                 getOptimalNewCameraMatrix,flip,BORDER_REFLECT_101,copyMakeBorder,
                 watershed,distanceTransform,DIST_L2,connectedComponents,
                 connectedComponentsWithStats,CC_STAT_AREA,contourArea,arcLength, 
                 convexHull,rectangle,circle,putText,FONT_HERSHEY_SIMPLEX,
                 CC_STAT_AREA,CC_STAT_LEFT,CC_STAT_TOP,CC_STAT_WIDTH,CC_STAT_HEIGHT,
                 findContours,RETR_EXTERNAL,CHAIN_APPROX_SIMPLE)

class PipelineExecutor:
    """Executes image processing pipelines"""
    def __init__(self, pipeline_data):
        self.pipeline_data = pipeline_data
        self.nodes = {}
        self.connections = []
        self.execution_order = []
        self._parse_pipeline()
        return
    
    def _parse_pipeline(self):
        """Parse pipeline data into nodes and connections"""
        for node_data in self.pipeline_data.get("nodes", []):
            node_id = node_data["id"]
            self.nodes[node_id] = node_data
        self.connections = self.pipeline_data.get("connections", [])
        self._compute_execution_order()
        return
    
    def _compute_execution_order(self):
        """Compute topological order for node execution"""
        input_node = None
        for node_id, node in self.nodes.items():
            if node.get("node_type") == "input":
                input_node = node_id
                break
        if not input_node:
            return
        adj = {node_id: [] for node_id in self.nodes}
        for conn in self.connections:
            from_id = conn["from_node"]
            to_id = conn["to_node"]
            adj[from_id].append(to_id)
        visited = set()
        order = []
        def dfs(node_id):
            if node_id in visited:
                return
            visited.add(node_id)
            for next_id in adj[node_id]:
                dfs(next_id)
            order.append(node_id)
        
        dfs(input_node)
        self.execution_order = list(reversed(order))
        return
    
    def execute(self, input_image_array):
        """Execute pipeline on input image array"""
        results = {}
        if hasattr(input_image_array, 'get_size'):
            input_image_array = surfarray.array3d(input_image_array)
            input_image_array = np.transpose(input_image_array, (1, 0, 2))
        for node_id in self.execution_order:
            node = self.nodes[node_id]
            node_type = node.get("node_type")
            node_name = node.get("name")

            print(f"Processing node: {node_name} (type: {node_type})")

            if node_type == "input":
                results[node_id] = {"image": input_image_array.copy()}
            elif node_type == "output":
                output_result = {
                    "image": None,
                    "data": None
                }
                for conn in self.connections:
                    if conn["to_node"] == node_id:
                        to_param = conn.get("to_parameter")
                        from_output = conn.get("from_output", "image")
                        from_node_results = results.get(conn["from_node"])
                        if isinstance(from_node_results, dict):
                            value = from_node_results.get(from_output)
                        else:
                            value = from_node_results
                            print(f"  value (not dict) type: {type(value)}")
                        if to_param == "image":
                            output_result["image"] = value
                        elif to_param == "data":
                            output_result["data"] = value
                        elif to_param is None:
                            output_result["image"] = value
                if output_result["image"] is not None and output_result["data"] is None:
                    results[node_id] = output_result["image"]
                else:
                    results[node_id] = output_result
            elif node_type == "process" or node_type == "algorithm":
                input_conn = None
                for conn in self.connections:
                    if conn["to_node"] == node_id and conn.get("to_parameter") is None:
                        input_conn = conn
                        break
                if not input_conn:
                    continue
                from_output = input_conn.get("from_output", "image")
                from_node_results = results.get(input_conn["from_node"])
                if from_node_results is None:
                    continue
                input_data = results.get(input_conn["from_node"])
                if input_data is None:
                    continue
                if isinstance(from_node_results, dict):
                    input_data = from_node_results.get(from_output)
                else:
                    input_data = from_node_results
                if input_data is None:
                    continue
                param_connections = {}
                for conn in self.connections:
                    if conn["to_node"] == node_id and conn.get("to_parameter") is not None:
                        param_name = conn["to_parameter"]
                        from_node_id = conn["from_node"]
                        from_output_name = conn.get("from_output", "output")
                        from_results = results.get(from_node_id)
                        if isinstance(from_results, dict):
                            param_value = from_results.get(from_output_name)
                        else:
                            param_value = from_results
                        if param_value is not None:
                            param_connections[param_name] = param_value
                if param_connections:
                    node["parameters"].update(param_connections)
                try:
                    output = self._apply_node_operation(node, input_data)
                    if isinstance(output, dict):
                        results[node_id] = output
                    else:
                        results[node_id] = {"image": output}
                except Exception as e:
                    print(f"Error executing node {node_name}: {e}")
                    print_exc()
                    results[node_id] = {"output": input_data}
        output_node = None
        for node_id, node in self.nodes.items():
            if node.get("node_type") == "output":
                output_node = node_id
                break
        if output_node and output_node in results:
            return results[output_node]
        return input_image_array
    
    def _apply_node_operation(self, node, input_data):
        """Apply the operation defined by a node"""
        node_name = node.get("name")
        node_type = node.get("node_type")
        params = node.get("parameters", {})
        if node_type == "algorithm":
            return self._execute_algorithm_node(node,input_data)
        if len(input_data.shape) == 2:
            input_data = np.stack([input_data] * 3, axis=-1)
        gray = None
        if len(input_data.shape) == 3:
            gray = np.dot(input_data[..., :3], [0.299, 0.587, 0.114]).astype(np.uint8)
        try:
            if node_name == "Add":
                value = params.get("Value", 0)
                result = np.clip(input_data.astype(np.int16) + value, 0, 255).astype(np.uint8)
                return result
            
            elif node_name == "Multiply":
                factor = params.get("Factor", 1.0)
                result = np.clip(input_data.astype(np.float32) * factor, 0, 255).astype(np.uint8)
                return result
            
            elif node_name == "Exponential":
                scale = params.get("Scale", 1.0)
                normalized = input_data.astype(np.float32) / 255.0
                result = np.exp(normalized * scale) - 1
                result = (result / (np.exp(scale) - 1)) * 255
                result = np.clip(result, 0, 255).astype(np.uint8)
                return result
            
            elif node_name == "Add Images":
                weight_a = params.get("Weight A", 0.5)
                weight_b = params.get("Weight B", 0.5)
                image_a = params.get("Image A")
                image_b = params.get("Image B")
                if image_a is not None and image_b is not None:
                    h = min(image_a.shape[0], image_b.shape[0])
                    w = min(image_a.shape[1], image_b.shape[1])
                    image_a = image_a[:h, :w]
                    image_b = image_b[:h, :w]
                    result = np.clip(image_a.astype(np.float32) * weight_a + 
                                    image_b.astype(np.float32) * weight_b, 0, 255).astype(np.uint8)
                    return result
                return input_data
            
            elif node_name == "Multiply Images":
                image_a = params.get("Image A")
                image_b = params.get("Image B")
                if image_a is not None and image_b is not None:
                    h = min(image_a.shape[0], image_b.shape[0])
                    w = min(image_a.shape[1], image_b.shape[1])
                    image_a = image_a[:h, :w]
                    image_b = image_b[:h, :w]
                    result = np.clip((image_a.astype(np.float32) / 255.0) * 
                                    (image_b.astype(np.float32) / 255.0) * 255.0, 0, 255).astype(np.uint8)
                    return result
                return input_data
            elif node_name == "Exponential Images":
                base_image = params.get("Base Image")
                exponent_image = params.get("Exponent Image")
                scale = params.get("Scale", 1.0)
                if base_image is not None and exponent_image is not None:
                    h = min(base_image.shape[0], exponent_image.shape[0])
                    w = min(base_image.shape[1], exponent_image.shape[1])
                    base_image = base_image[:h, :w]
                    exponent_image = exponent_image[:h, :w]
                    base_norm = base_image.astype(np.float32) / 255.0
                    exp_norm = exponent_image.astype(np.float32) / 255.0
                    result = np.power(base_norm, exp_norm * scale)
                    result = np.clip(result * 255.0, 0, 255).astype(np.uint8)
                    return result
                return input_data

            if node_name == "ROI":
                x = params.get("X", 0)
                y = params.get("Y", 0)
                width = params.get("Width", 100)
                height = params.get("Height", 100)
                img_height, img_width = input_data.shape[:2]
                x = max(0, min(x, img_width - 1))
                y = max(0, min(y, img_height - 1))
                width = max(1, min(width, img_width - x))
                height = max(1, min(height, img_height - y))
                roi = input_data[y:y+height, x:x+width]
                return roi
            
            elif node_name == "Crop to Center":
                h, w = input_data.shape[:2]
                crop_h, crop_w = h // 2, w // 2
                start_y, start_x = h // 4, w // 4
                return input_data[start_y:start_y+crop_h, start_x:start_x+crop_w]
            
            elif node_name == "Scale":
                width = params.get("Width", 100)
                height = params.get("Height", 100)
                return resize(input_data, (width, height), interpolation=INTER_LINEAR)
            
            elif node_name == "Rotate":
                angle = params.get("Angle", 0.0)
                h, w = input_data.shape[:2]
                center = (w // 2, h // 2)
                matrix = getRotationMatrix2D(center, angle, 1)
                return warpAffine(input_data, matrix, (w, h))
            
            elif node_name == "Translate":
                x_offset = params.get("X Offset", 0)
                y_offset = params.get("Y Offset", 0)
                border_value = params.get("Border Value", 0)
                h, w = input_data.shape[:2]
                translation_matrix = np.float32([[1, 0, x_offset],
                                                [0, 1, y_offset]])
                translated = warpAffine(input_data, translation_matrix, (w, h),
                                    borderMode=BORDER_CONSTANT,
                                    borderValue=(border_value, border_value, border_value))
                return translated
            
            elif node_name == "Undistort":
                k1 = params.get("K1", 0.0)
                k2 = params.get("K2", 0.0)
                p1 = params.get("P1", 0.0)
                p2 = params.get("P2", 0.0)
                k3 = params.get("K3", 0.0)
                fx = params.get("FX", 1000.0)
                fy = params.get("FY", 1000.0)
                h, w = input_data.shape[:2]
                cx = w / 2.0
                cy = h / 2.0
                camera_matrix = np.array([
                    [fx, 0, cx],
                    [0, fy, cy],
                    [0, 0, 1]
                ], dtype=np.float32)
                dist_coeffs = np.array([k1, k2, p1, p2, k3], dtype=np.float32)
                new_camera_matrix, roi = getOptimalNewCameraMatrix(
                    camera_matrix, dist_coeffs, (w, h), 1, (w, h)
                )
                undistorted = undistort(input_data, camera_matrix, dist_coeffs, 
                                    None, new_camera_matrix)
                return undistorted
            
            elif node_name == "Flip":
                direction = params.get("Direction", "Horizontal")
                if direction == "Horizontal":
                    flip_code = 1
                elif direction == "Vertical":
                    flip_code = 0
                elif direction == "Both":
                    flip_code = -1
                else:
                    flip_code = 1
                flipped = flip(input_data, flip_code)
                return flipped
            
            elif node_name == "Pad":
                top = params.get("Top", 10)
                bottom = params.get("Bottom", 10)
                left = params.get("Left", 10)
                right = params.get("Right", 10)
                border_type_str = params.get("Border Type", "Constant")
                border_value = params.get("Border Value", 0)
                border_map = {
                    "Constant": BORDER_CONSTANT,
                    "Replicate": BORDER_REPLICATE,
                    "Reflect": BORDER_REFLECT,
                    "Wrap": BORDER_WRAP,
                    "Reflect101": BORDER_REFLECT_101
                }
                border_type = border_map.get(border_type_str, BORDER_CONSTANT)
                if border_type == BORDER_CONSTANT:
                    padded = copyMakeBorder(input_data, top, bottom, left, right,
                                        border_type,
                                        value=(border_value, border_value, border_value))
                else:
                    padded = copyMakeBorder(input_data, top, bottom, left, right,
                                        border_type)
                return padded
            
            elif node_name == "Box Filter":
                ksize = params.get("Kernel Size", 5)
                if ksize % 2 == 0:
                    ksize += 1
                normalize = params.get("Normalize", True)
                kernel = np.ones((ksize, ksize), np.float32)
                if normalize:
                    kernel = kernel / (ksize * ksize)
                return filter2D(input_data, -1, kernel)
            elif node_name == "Gaussian Blur":
                ksize = params.get("Kernel Size", 5)
                if ksize % 2 == 0:
                    ksize += 1
                sigma = params.get("Sigma", 1.5)
                return GaussianBlur(input_data, (ksize, ksize), sigma)
            
            elif node_name == "Median Blur":
                ksize = params.get("Kernel Size", 5)
                if ksize % 2 == 0:
                    ksize += 1
                return medianBlur(input_data, ksize)
            
            elif node_name == "Bilateral Filter":
                d = params.get("Diameter", 9)
                sigma_color = params.get("Sigma Color", 75.0)
                sigma_space = params.get("Sigma Space", 75.0)
                return bilateralFilter(input_data, d, sigma_color, sigma_space)
            
            elif node_name == "NL Means Denoise":
                h = params.get("h", 10)
                template_window = params.get("Template Window", 7)
                search_window = params.get("Search Window", 21)
                if template_window % 2 == 0:
                    template_window += 1
                if search_window % 2 == 0:
                    search_window += 1
                if len(input_data.shape) == 3 and input_data.shape[2] == 3:
                    return fastNlMeansDenoisingColored(input_data, None, h, h, template_window, search_window)
                else:
                    if len(input_data.shape) == 3:
                        gray = np.dot(input_data[..., :3], [0.299, 0.587, 0.114]).astype(np.uint8)
                    else:
                        gray = input_data
                    denoised = fastNlMeansDenoising(gray, None, h, template_window, search_window)
                    return np.stack([denoised] * 3, axis=-1)
            
            elif node_name == "Laplacian":
                laplacian = Laplacian(gray, -1)
                laplacian = np.absolute(laplacian).astype(np.uint8)
                return np.stack([laplacian] * 3, axis=-1)
            
            elif node_name == "Sobel":
                sobelx = Sobel(gray, -1, 1, 0, ksize=3)
                sobely = Sobel(gray, -1, 0, 1, ksize=3)
                sobel = np.sqrt(sobelx**2 + sobely**2).astype(np.uint8)
                return np.stack([sobel] * 3, axis=-1)
            
            elif node_name == "Scharr":
                dx = params.get("dx", 1)
                dy = params.get("dy", 0)
                scale = params.get("Scale", 1.0)
                scharr_x = Scharr(gray, -1, dx, dy, scale=scale)
                scharr_y = Scharr(gray, -1, dy, dx, scale=scale)
                scharr = np.sqrt(scharr_x**2 + scharr_y**2).astype(np.uint8)
                return np.stack([scharr] * 3, axis=-1)

            elif node_name == "FFT Low Pass":
                cutoff_percent = params.get("Cutoff Percent", 10.0)
                order = params.get("Order", 2)
                if len(input_data.shape) == 3:
                    result = np.zeros_like(input_data)
                    for channel in range(input_data.shape[2]):
                        result[:, :, channel] = self._apply_butterworth_lowpass(
                            input_data[:, :, channel], cutoff_percent, order
                        )
                    return result
                else:
                    filtered = self._apply_butterworth_lowpass(gray, cutoff_percent, order)
                    return np.stack([filtered] * 3, axis=-1)

            elif node_name == "FFT High Pass":
                cutoff_percent = params.get("Cutoff Percent", 10.0)
                order = params.get("Order", 2)
                if len(input_data.shape) == 3:
                    result = np.zeros_like(input_data)
                    for channel in range(input_data.shape[2]):
                        result[:, :, channel] = self._apply_butterworth_highpass(
                            input_data[:, :, channel], cutoff_percent, order
                        )
                    return result
                else:
                    filtered = self._apply_butterworth_highpass(gray, cutoff_percent, order)
                    return np.stack([filtered] * 3, axis=-1)
                
            elif node_name == "Canny":
                thresh1 = params.get("Threshold 1", 100)
                thresh2 = params.get("Threshold 2", 200)
                edges = Canny(gray, thresh1, thresh2)
                return np.stack([edges] * 3, axis=-1)
            
            elif node_name == "Gabor Filter":
                ksize = params.get("Kernel Size", 21)
                if ksize % 2 == 0:
                    ksize += 1
                sigma = params.get("Sigma", 5.0)
                theta = params.get("Theta", 0.0) * np.pi / 180.0  # Convert to radians
                lambd = params.get("Lambda", 10.0)
                gamma = params.get("Gamma", 0.5)
                psi = params.get("Psi", 0.0) * np.pi / 180.0  # Convert to radians
                gabor_kernel = getGaborKernel((ksize, ksize), sigma, theta, lambd, gamma, psi, ktype=CV_32F)
                if len(input_data.shape) == 3:
                    result = np.zeros_like(input_data)
                    for channel in range(input_data.shape[2]):
                        filtered = filter2D(input_data[:, :, channel], -1, gabor_kernel)
                        filtered = np.clip(filtered, 0, 255).astype(np.uint8)
                        result[:, :, channel] = filtered
                    return result
                else:
                    filtered = filter2D(gray, -1, gabor_kernel)
                    filtered = np.clip(filtered, 0, 255).astype(np.uint8)
                    return np.stack([filtered] * 3, axis=-1)
            
            elif node_name == "Binary":
                thresh_val = params.get("Threshold", 127)
                max_val = params.get("Max Value", 255)
                _, binary = threshold(gray, thresh_val, max_val, THRESH_BINARY)
                return np.stack([binary] * 3, axis=-1)
            
            elif node_name == "Adaptive":
                binary = adaptiveThreshold(gray, 255, ADAPTIVE_THRESH_MEAN_C, 
                                          THRESH_BINARY, 11, 2)
                return np.stack([binary] * 3, axis=-1)
            
            elif node_name == "Otsu":
                _, binary = threshold(gray, 0, 255, THRESH_BINARY + THRESH_OTSU)
                return np.stack([binary] * 3, axis=-1)
            
            elif node_name == "Erode":
                ksize = params.get("Kernel Size", 5)
                iterations = params.get("Iterations", 1)
                kernel = np.ones((ksize, ksize), np.uint8)
                return erode(input_data, kernel, iterations=iterations)
            
            elif node_name == "Dilate":
                ksize = params.get("Kernel Size", 5)
                iterations = params.get("Iterations", 1)
                kernel = np.ones((ksize, ksize), np.uint8)
                return dilate(input_data, kernel, iterations=iterations)
            
            elif node_name == "Opening":
                ksize = params.get("Kernel Size", 5)
                iterations = params.get("Iterations", 1)
                kernel = np.ones((ksize, ksize), np.uint8)
                return morphologyEx(input_data, MORPH_OPEN, kernel, iterations=iterations)

            elif node_name == "Closing":
                ksize = params.get("Kernel Size", 5)
                iterations = params.get("Iterations", 1)
                kernel = np.ones((ksize, ksize), np.uint8)
                return morphologyEx(input_data, MORPH_CLOSE, kernel, iterations=iterations)
            
            elif node_name == "Morph Gradient":
                ksize = params.get("Kernel Size", 5)
                kernel_shape = params.get("Kernel Shape", "Rect")
                shape_map = {
                    "Rect": MORPH_RECT,
                    "Ellipse": MORPH_ELLIPSE,
                    "Cross": MORPH_CROSS
                }
                shape = shape_map.get(kernel_shape, MORPH_RECT)
                kernel = getStructuringElement(shape, (ksize, ksize))
                return morphologyEx(input_data, MORPH_GRADIENT, kernel)
            
            elif node_name == "Morph Top Hat":
                ksize = params.get("Kernel Size", 9)
                kernel_shape = params.get("Kernel Shape", "Rect")
                shape_map = {
                    "Rect": MORPH_RECT,
                    "Ellipse": MORPH_ELLIPSE,
                    "Cross": MORPH_CROSS
                }
                shape = shape_map.get(kernel_shape, MORPH_RECT)
                kernel = getStructuringElement(shape, (ksize, ksize))
                return morphologyEx(input_data, MORPH_TOPHAT, kernel)

            elif node_name == "Morph Black Hat":
                ksize = params.get("Kernel Size", 9)
                kernel_shape = params.get("Kernel Shape", "Rect")
                shape_map = {
                    "Rect": MORPH_RECT,
                    "Ellipse": MORPH_ELLIPSE,
                    "Cross": MORPH_CROSS
                }
                shape = shape_map.get(kernel_shape, MORPH_RECT)
                kernel = getStructuringElement(shape, (ksize, ksize))
                return morphologyEx(input_data, MORPH_BLACKHAT, kernel)
            
            elif node_name == "Label Objects":
                connectivity_str = params.get("Connectivity", "8")
                connectivity = 8 if connectivity_str == "8" else 4
                min_area = params.get("Min Area", 50)
                if len(input_data.shape) == 3:
                    gray = np.dot(input_data[..., :3], [0.299, 0.587, 0.114]).astype(np.uint8)
                else:
                    gray = input_data
                _, binary = threshold(gray, 127, 255, THRESH_BINARY)
                num_labels, labels, stats, _ = connectedComponentsWithStats(binary, connectivity=connectivity)
                label_image = np.zeros_like(input_data)
                colors = np.random.randint(0, 255, size=(num_labels, 3), dtype=np.uint8)
                colors[0] = [0, 0, 0]
                for label in range(1, num_labels):
                    area = stats[label, CC_STAT_AREA]
                    if area >= min_area:
                        mask = labels == label
                        label_image[mask] = colors[label]
                return label_image
            
            elif node_name == "Object Characteristics":
                connectivity_str = params.get("Connectivity", "8")
                connectivity = 8 if connectivity_str == "8" else 4
                min_area = params.get("Min Area", 50)
                draw_labels = params.get("Draw Labels", True)
                draw_boxes = params.get("Draw Boxes", True)
                draw_centroids = params.get("Draw Centroids", True)
                if len(input_data.shape) == 3:
                    gray = np.dot(input_data[..., :3], [0.299, 0.587, 0.114]).astype(np.uint8)
                else:
                    gray = input_data
                _, binary = threshold(gray, 127, 255, THRESH_BINARY)
                num_labels, labels, stats, centroids = connectedComponentsWithStats(binary, connectivity=connectivity)
                result = input_data.copy()
                object_data = []
                valid_count = 0
                for label in range(1, num_labels):
                    area = stats[label, CC_STAT_AREA]
                    if area < min_area:
                        continue
                    valid_count += 1
                    x = stats[label, CC_STAT_LEFT]
                    y = stats[label, CC_STAT_TOP]
                    w = stats[label, CC_STAT_WIDTH]
                    h = stats[label, CC_STAT_HEIGHT]
                    cx, cy = centroids[label]
                    mask = (labels == label).astype(np.uint8)
                    contours, _ = findContours(mask, RETR_EXTERNAL, CHAIN_APPROX_SIMPLE)
                    if len(contours) > 0:
                        contour = contours[0]
                        perimeter = arcLength(contour, True)
                        hull = convexHull(contour)
                        hull_area = contourArea(hull)
                        circularity = (4 * np.pi * area) / (perimeter ** 2) if perimeter > 0 else 0
                        solidity = area / hull_area if hull_area > 0 else 0
                        aspect_ratio = w / h if h > 0 else 0
                        extent = area / (w * h) if (w * h) > 0 else 0
                        obj_info = {
                            "label": valid_count,
                            "area": float(area),
                            "perimeter": float(perimeter),
                            "centroid": (float(cx), float(cy)),
                            "bounding_box": (int(x), int(y), int(w), int(h)),
                            "circularity": float(circularity),
                            "solidity": float(solidity),
                            "aspect_ratio": float(aspect_ratio),
                            "extent": float(extent)
                        }
                        object_data.append(obj_info)
                        if draw_boxes:
                            rectangle(result, (x, y), (x + w, y + h), (0, 255, 0), 2)
                        if draw_centroids:
                            circle(result, (int(cx), int(cy)), 5, (255, 0, 0), -1)
                        if draw_labels:
                            putText(result, f"#{valid_count}", (x, y - 5), FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1)
                
                return_value = {
                    "image": result,
                    "data": object_data
                }
                return return_value

            elif node_name == "Skeleton":
                if len(input_data.shape) == 3:
                    gray = np.dot(input_data[..., :3], [0.299, 0.587, 0.114]).astype(np.uint8)
                else:
                    gray = input_data
                _, binary = threshold(gray, 127, 255, THRESH_BINARY)
                binary = binary // 255
                skeleton = np.zeros_like(binary)
                element = getStructuringElement(MORPH_CROSS, (3, 3))
                temp = binary.copy()
                while True:
                    eroded = erode(temp, element)
                    opened = dilate(eroded, element)
                    subset = temp - opened
                    skeleton = skeleton | subset
                    temp = eroded.copy()
                    if np.sum(temp) == 0:
                        break
                skeleton = skeleton * 255
                return np.stack([skeleton] * 3, axis=-1)
            
            elif node_name == "Watershed":
                thresh_val = params.get("Threshold", 127)
                min_distance = params.get("Min Distance", 10)
                if len(input_data.shape) == 3:
                    gray = np.dot(input_data[..., :3], [0.299, 0.587, 0.114]).astype(np.uint8)
                else:
                    gray = input_data
                _, binary = threshold(gray, thresh_val, 255, THRESH_BINARY)
                dist_transform = distanceTransform(binary, DIST_L2, 5)
                _, sure_fg = threshold(dist_transform, min_distance, 255, THRESH_BINARY)
                sure_fg = sure_fg.astype(np.uint8)
                kernel = np.ones((3, 3), np.uint8)
                sure_bg = dilate(binary, kernel, iterations=3)
                unknown = sure_bg - sure_fg
                _, markers = connectedComponents(sure_fg)
                markers = markers + 1
                markers[unknown == 255] = 0
                markers = watershed(input_data, markers)
                result = input_data.copy()
                result[markers == -1] = [255, 0, 0]
                return result
            
            else:
                print(f"Unknown node operation: {node_name}")
                return input_data
        except Exception as e:
            print(f"Error in {node_name}: {e}")
            return input_data
        
    def _apply_butterworth_lowpass(self, channel, cutoff_percent, order):
        """Apply Butterworth low pass filter in frequency domain"""
        img_float = np.float32(channel)
        dft_result = dft(img_float, flags=DFT_COMPLEX_OUTPUT)
        dft_shift = np.fft.fftshift(dft_result)
        rows, cols = channel.shape
        crow, ccol = rows // 2, cols // 2
        max_distance = np.sqrt(crow**2 + ccol**2)
        cutoff = (cutoff_percent / 100.0) * max_distance
        mask = np.zeros((rows, cols, 2), np.float32)
        for i in range(rows):
            for j in range(cols):
                distance = np.sqrt((i - crow)**2 + (j - ccol)**2)
                mask[i, j] = 1 / (1 + (distance / cutoff)**(2 * order))
        fshift = dft_shift * mask
        f_ishift = np.fft.ifftshift(fshift)
        img_back = idft(f_ishift)
        img_back = np.sqrt(img_back[:, :, 0]**2 + img_back[:, :, 1]**2)
        img_back = np.clip(img_back, 0, 255).astype(np.uint8)
        return img_back

    def _apply_butterworth_highpass(self, channel, cutoff_percent, order):
        """Apply Butterworth high pass filter in frequency domain"""
        img_float = np.float32(channel)
        dft_result = dft(img_float, flags=DFT_COMPLEX_OUTPUT)
        dft_shift = np.fft.fftshift(dft_result)
        rows, cols = channel.shape
        crow, ccol = rows // 2, cols // 2
        max_distance = np.sqrt(crow**2 + ccol**2)
        cutoff = (cutoff_percent / 100.0) * max_distance
        mask = np.zeros((rows, cols, 2), np.float32)
        for i in range(rows):
            for j in range(cols):
                distance = np.sqrt((i - crow)**2 + (j - ccol)**2)
                if distance == 0:
                    mask[i, j] = 0
                else:
                    mask[i, j] = 1 / (1 + (cutoff / distance)**(2 * order))
        fshift = dft_shift * mask
        f_ishift = np.fft.ifftshift(fshift)
        img_back = idft(f_ishift)
        img_back = np.sqrt(img_back[:, :, 0]**2 + img_back[:, :, 1]**2)
        img_back = np.clip(img_back, 0, 255).astype(np.uint8)
        return img_back
    
    def _execute_algorithm_node(self, algorithm_node, input_data):
        """Execute an algorithm node's embedded pipeline"""
        try:
            pipeline_data = algorithm_node.get("pipeline_data")
            if not pipeline_data:
                print(f"Algorithm node has no pipeline data")
                return input_data
            # Create a sub-executor for the algorithm's pipeline
            sub_executor = PipelineExecutor(pipeline_data)
            # Execute the embedded pipeline
            result = sub_executor.execute(input_data)
            return result
        except Exception as e:
            print(f"Error executing algorithm node: {e}")
            import traceback
            traceback.print_exc()
            return input_data