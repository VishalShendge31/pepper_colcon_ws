#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from std_msgs.msg import String
from cv_bridge import CvBridge
from PIL import Image as PILImage
import torch
from transformers import AutoProcessor, AutoModelForVision2Seq
from rclpy.qos import QoSProfile, QoSHistoryPolicy, QoSReliabilityPolicy

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"


class SmolVLMNode(Node):

    def __init__(self):
        super().__init__("smolvlm_node")

        self.get_logger().info("Loading SmolVLM model...")

        self.processor = AutoProcessor.from_pretrained(
            "HuggingFaceTB/SmolVLM-500M-Instruct",
            size={"longest_edge": 512}  # Faster on Jetson
        )

        self.model = AutoModelForVision2Seq.from_pretrained(
            "HuggingFaceTB/SmolVLM-500M-Instruct",
            torch_dtype=torch.bfloat16 if DEVICE == "cuda" else torch.float32,
        ).to(DEVICE)

        self.bridge = CvBridge()

        # Use BEST_EFFORT for camera stream
        qos = QoSProfile(
            history=QoSHistoryPolicy.KEEP_LAST,
            depth=1,
            reliability=QoSReliabilityPolicy.BEST_EFFORT
        )

        # Subscribe to image stream
        self.subscription = self.create_subscription(
            Image,
            "/naoqi_driver/camera/front/image_raw",
            self.image_callback,
            qos
        )

        # Publisher for result
        self.publisher = self.create_publisher(String, "/smolvlm/output", 10)

        # Throttle processing to 1 Hz
        self.timer_rate = self.create_rate(1.0)  # 1 Hz

        self.get_logger().info("SmolVLM node ready.")

    def image_callback(self, msg):
        self.get_logger().info("Received image")

        try:
            # Convert ROS image to PIL
            cv_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding="bgr8")
            pil_image = PILImage.fromarray(cv_image[:, :, ::-1])

            # Prompt: description + emotion
            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "image"},
                        {"type": "text", "text": "Describe this image concisely in 1-2 sentences. Include the emotion, age, and gender of the person."}
                    ]
                }
            ]

            prompt = self.processor.apply_chat_template(messages, add_generation_prompt=True)

            inputs = self.processor(
                text=prompt,
                images=[pil_image],
                return_tensors="pt"
            ).to(DEVICE)

            with torch.no_grad():
                generated_ids = self.model.generate(**inputs, max_new_tokens=40)

            generated_text = self.processor.batch_decode(generated_ids, skip_special_tokens=True)[0]
            if "ASSISTANT:" in generated_text:
                generated_text = generated_text.split("ASSISTANT:")[1].strip()

            # Publish result
            msg_out = String()
            msg_out.data = generated_text
            self.publisher.publish(msg_out)
            self.get_logger().info(f"Generated: {generated_text}")

        except Exception as e:
            self.get_logger().error(f"Error processing image: {str(e)}")

        # Enforce 1 Hz processing
        self.timer_rate.sleep()


def main(args=None):
    rclpy.init(args=args)
    node = SmolVLMNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()   
