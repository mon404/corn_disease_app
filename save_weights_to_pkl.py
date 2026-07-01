import tensorflow as tf
import pickle
import os

os.makedirs("models", exist_ok=True)

# 1. Save CNN weights
cnn_keras = "models/cnn_model.keras"
if os.path.exists(cnn_keras):
    print("Loading CNN Keras model...")
    model = tf.keras.models.load_model(cnn_keras)
    weights = model.get_weights()
    with open("models/cnn_weights.pkl", "wb") as f:
        pickle.dump(weights, f)
    print("Saved CNN weights to models/cnn_weights.pkl")
else:
    print("CNN model not found.")

# 2. Save MobileNet weights
mobilenet_keras = "models/mobilenet_model.keras"
if os.path.exists(mobilenet_keras):
    print("Loading MobileNet Keras model...")
    model = tf.keras.models.load_model(mobilenet_keras)
    weights = model.get_weights()
    with open("models/mobilenet_weights.pkl", "wb") as f:
        pickle.dump(weights, f)
    print("Saved MobileNet weights to models/mobilenet_weights.pkl")
else:
    print("MobileNet model not found.")
