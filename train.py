import tensorflow as tf
from tensorflow.keras import layers, models
import os
import matplotlib.pyplot as plt

# Konfigurasi Parameter
DATA_DIR = r"D:\Dataset-Project\data"
BATCH_SIZE = 32
IMG_SIZE = (224, 224)
EPOCHS = 25  # Pilihan rentang 20-30
LEARNING_RATE = 0.001

def main():
    print("=== Mempersiapkan Dataset ===")
    if not os.path.exists(DATA_DIR):
        print(f"Error: Direktori dataset {DATA_DIR} tidak ditemukan!")
        return

    # Memuat dataset pelatihan dan validasi (split 80/20)
    train_ds, val_ds = tf.keras.utils.image_dataset_from_directory(
        DATA_DIR,
        validation_split=0.2,
        subset="both",
        seed=42,
        image_size=IMG_SIZE,
        batch_size=BATCH_SIZE,
        label_mode="categorical"
    )

    class_names = train_ds.class_names
    num_classes = len(class_names)
    print(f"Kelas yang ditemukan ({num_classes}): {class_names}")

    # Simpan nama kelas ke file untuk digunakan oleh aplikasi Kivy
    os.makedirs("models", exist_ok=True)
    with open("models/class_names.txt", "w") as f:
        for name in class_names:
            f.write(name + "\n")
    print("Nama kelas disimpan di models/class_names.txt")

    # Optimasi performa loading data
    AUTOTUNE = tf.data.AUTOTUNE
    train_ds = train_ds.prefetch(buffer_size=AUTOTUNE)
    val_ds = val_ds.prefetch(buffer_size=AUTOTUNE)

    # 1. Melatih Model Custom CNN
    print("\n=== Melatih Model Custom CNN ===")
    cnn_model = build_cnn(input_shape=(224, 224, 3), num_classes=num_classes)
    cnn_model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=LEARNING_RATE),
        loss="categorical_crossentropy",
        metrics=["accuracy"]
    )
    cnn_model.summary()

    cnn_history = cnn_model.fit(
        train_ds,
        validation_data=val_ds,
        epochs=EPOCHS
    )
    
    print("Menyimpan model Custom CNN...")
    cnn_model.save("models/cnn_model.keras")
    print("Model Custom CNN berhasil disimpan di models/cnn_model.keras")

    # 2. Melatih Model MobileNetV2 (Transfer Learning)
    print("\n=== Melatih Model MobileNetV2 (Transfer Learning) ===")
    mobilenet_model = build_mobilenetv2(input_shape=(224, 224, 3), num_classes=num_classes)
    mobilenet_model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=LEARNING_RATE),
        loss="categorical_crossentropy",
        metrics=["accuracy"]
    )
    mobilenet_model.summary()

    mobilenet_history = mobilenet_model.fit(
        train_ds,
        validation_data=val_ds,
        epochs=EPOCHS
    )

    print("Menyimpan model MobileNetV2...")
    mobilenet_model.save("models/mobilenet_model.keras")
    print("Model MobileNetV2 berhasil disimpan di models/mobilenet_model.keras")

    # Menyimpan grafik performa pelatihan
    plot_training_history(cnn_history, mobilenet_history)
    print("\n=== Pelatihan Selesai! Semua model berhasil disimpan ===")

def build_cnn(input_shape, num_classes):
    model = models.Sequential([
        # Rescaling pixel ke rentang [0, 1]
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

def build_mobilenetv2(input_shape, num_classes):
    # Mengambil base model MobileNetV2 dengan bobot pre-trained ImageNet
    base_model = tf.keras.applications.MobileNetV2(
        input_shape=input_shape,
        include_top=False,
        weights='imagenet'
    )
    base_model.trainable = False  # Membekukan bobot base model
    
    model = models.Sequential([
        # Rescaling pixel ke rentang [-1, 1] sesuai kebutuhan MobileNetV2
        layers.Rescaling(scale=2./255, offset=-1., input_shape=input_shape),
        
        base_model,
        layers.GlobalAveragePooling2D(),
        layers.Dense(128, activation='relu'),
        layers.Dropout(0.3),
        layers.Dense(num_classes, activation='softmax')
    ])
    return model

def plot_training_history(cnn_history, mobilenet_history):
    epochs_range = range(EPOCHS)
    
    plt.figure(figsize=(12, 8))
    
    # Akurasi
    plt.subplot(2, 2, 1)
    plt.plot(epochs_range, cnn_history.history['accuracy'], label='CNN Train Acc')
    plt.plot(epochs_range, cnn_history.history['val_accuracy'], label='CNN Val Acc')
    plt.title('Custom CNN Accuracy')
    plt.legend(loc='lower right')
    
    plt.subplot(2, 2, 2)
    plt.plot(epochs_range, mobilenet_history.history['accuracy'], label='MobileNet Train Acc')
    plt.plot(epochs_range, mobilenet_history.history['val_accuracy'], label='MobileNet Val Acc')
    plt.title('MobileNetV2 Accuracy')
    plt.legend(loc='lower right')
    
    # Loss
    plt.subplot(2, 2, 3)
    plt.plot(epochs_range, cnn_history.history['loss'], label='CNN Train Loss')
    plt.plot(epochs_range, cnn_history.history['val_loss'], label='CNN Val Loss')
    plt.title('Custom CNN Loss')
    plt.legend(loc='upper right')
    
    plt.subplot(2, 2, 4)
    plt.plot(epochs_range, mobilenet_history.history['loss'], label='MobileNet Train Loss')
    plt.plot(epochs_range, mobilenet_history.history['val_loss'], label='MobileNet Val Loss')
    plt.title('MobileNetV2 Loss')
    plt.legend(loc='upper right')
    
    plt.tight_layout()
    os.makedirs("reports", exist_ok=True)
    plt.savefig("reports/training_history.png")
    print("Grafik hasil pelatihan disimpan di reports/training_history.png")

if __name__ == "__main__":
    main()
