import tensorflow as tf
import pickle
import os

print("TensorFlow version:", tf.__version__)

def build_cnn(input_shape=(224, 224, 3), num_classes=4):
    from tensorflow.keras import layers, models
    model = models.Sequential([
        layers.Rescaling(1./255, input_shape=input_shape),
        
        layers.Conv2D(32, (3, 3), activation='relu'),
        layers.MaxPooling2D((2, 2)),
        
        layers.Conv2D(64, (3, 3), activation='relu'),
        layers.MaxPooling2D((2, 2)),
        
        layers.Conv2D(128, (3, 3), activation='relu'),
        layers.MaxPooling2D((2, 2)),
        
        layers.Conv2D(128, (3, 3), activation='relu'),
        layers.MaxPooling2D((2, 2)),
        
        layers.Flatten(),
        layers.Dense(128, activation='relu'),
        layers.Dropout(0.5),
        layers.Dense(num_classes, activation='softmax')
    ])
    return model

def build_mobilenetv2(input_shape=(224, 224, 3), num_classes=4):
    from tensorflow.keras import layers, models
    base_model = tf.keras.applications.MobileNetV2(
        input_shape=input_shape,
        include_top=False,
        weights=None  # load None since we will overwrite weights
    )
    base_model.trainable = False
    
    model = models.Sequential([
        layers.Rescaling(scale=2./255, offset=-1., input_shape=input_shape),
        base_model,
        layers.GlobalAveragePooling2D(),
        layers.Dense(128, activation='relu'),
        layers.Dropout(0.3),
        layers.Dense(num_classes, activation='softmax')
    ])
    return model

# 1. Convert CNN Model
cnn_weights_path = "models/cnn_weights.pkl"
if os.path.exists(cnn_weights_path):
    print("Reconstructing CNN and loading weights from PKL...")
    cnn_model = build_cnn()
    with open(cnn_weights_path, "rb") as f:
        cnn_weights = pickle.load(f)
    cnn_model.set_weights(cnn_weights)
    
    print("Converting CNN model to legacy TFLite...")
    converter = tf.lite.TFLiteConverter.from_keras_model(cnn_model)
    tflite_model = converter.convert()
    with open("models/cnn_model.tflite", "wb") as f:
        f.write(tflite_model)
    print("Saved models/cnn_model.tflite successfully!")
else:
    print("CNN weights PKL not found, skipping.")

# 2. Convert MobileNetV2 Model
mobilenet_weights_path = "models/mobilenet_weights.pkl"
if os.path.exists(mobilenet_weights_path):
    print("Reconstructing MobileNetV2 and loading weights from PKL...")
    mobilenet_model = build_mobilenetv2()
    with open(mobilenet_weights_path, "rb") as f:
        mobilenet_weights = pickle.load(f)
    mobilenet_model.set_weights(mobilenet_weights)
    
    print("Converting MobileNetV2 model to legacy TFLite...")
    converter = tf.lite.TFLiteConverter.from_keras_model(mobilenet_model)
    tflite_model = converter.convert()
    with open("models/mobilenet_model.tflite", "wb") as f:
        f.write(tflite_model)
    print("Saved models/mobilenet_model.tflite successfully!")
else:
    print("MobileNetV2 weights PKL not found, skipping.")
