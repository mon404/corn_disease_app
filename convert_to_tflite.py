import os
import tensorflow as tf

def convert_model(model_path, output_path):
    if not os.path.exists(model_path):
        print(f"Model path does not exist: {model_path}")
        return
        
    print(f"\nLoading Keras model from {model_path}...")
    model = tf.keras.models.load_model(model_path)
    
    print(f"Converting to TensorFlow Lite...")
    converter = tf.lite.TFLiteConverter.from_keras_model(model)
    # Enable standard optimizations for mobile deployment
    converter.optimizations = [tf.lite.Optimize.DEFAULT]
    tflite_model = converter.convert()
    
    # Save the model
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'wb') as f:
        f.write(tflite_model)
    print(f"Saved TFLite model to {output_path} (Size: {os.path.getsize(output_path) / (1024*1024):.2f} MB)")

if __name__ == "__main__":
    # Convert both models
    convert_model("models/cnn_model.keras", "models/cnn_model.tflite")
    convert_model("models/mobilenet_model.keras", "models/mobilenet_model.tflite")
