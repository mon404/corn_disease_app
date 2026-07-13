import os
import shutil
import numpy as np
from PIL import Image

try:
    from plyer import camera
except ImportError:
    camera = None

# Import Kivy
import kivy
kivy.require('2.0.0')
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.properties import StringProperty, ListProperty, ObjectProperty, NumericProperty
from kivy.uix.popup import Popup
from kivy.uix.filechooser import FileChooserIconView
from kivy.uix.boxlayout import BoxLayout
from kivy.core.window import Window

# Set window size to mimic a mobile phone for desktop testing (only on desktop)
from kivy.utils import platform
if platform not in ('android', 'ios'):
    Window.size = (400, 720)

from kivymd.app import MDApp
from kivymd.uix.card import MDCard
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDRaisedButton

# Kivy 2.3.1 + KivyMD 1.2.0 compatibility patch for BoxShadow border_radius ValueError
def patch_elevation_behavior():
    import kivymd.uix.behaviors.elevation
    to_remove = []
    for key in list(Builder.rules):
        if "commonelevationbehavior" in str(key).lower():
            to_remove.append(key)
    for key in to_remove:
        if isinstance(Builder.rules, dict):
            Builder.rules.pop(key, None)
        else:
            try:
                Builder.rules.remove(key)
            except Exception:
                pass
    patched_kv = """
<CommonElevationBehavior>
    canvas.before:
        PushMatrix
        Scale:
            x: self.scale_value_x
            y: self.scale_value_y
            z: self.scale_value_x
            origin:
                self.center \
                if not self.scale_value_center else \
                self.scale_value_center
        Rotate:
            angle: self.rotate_value_angle
            axis: tuple(self.rotate_value_axis)
            origin: self.center
        Color:
            rgba:
                (0, 0, 0, 0) \
                if self.disabled or not self.elevation else \
                root.shadow_color
        BoxShadow:
            pos: self.pos
            size: self.size
            offset: root.shadow_offset
            spread_radius: -(root.shadow_softness), -(root.shadow_softness)
            blur_radius: root.elevation * 10
            border_radius:
                (root.radius if (hasattr(root, "radius") and len(root.radius) == 4) else [0, 0, 0, 0]) \
                if (len(root.shadow_radius) == 4 and root.shadow_radius == [0.0, 0.0, 0.0, 0.0]) else \
                (root.shadow_radius if len(root.shadow_radius) == 4 else [0, 0, 0, 0])
    canvas.after:
        PopMatrix
"""
    Builder.load_string(patched_kv)

patch_elevation_behavior()


# Try to import tflite_runtime interpreter and capture errors for debugging
Interpreter = None
has_tflite = False
import_error_log = ""
try:
    from tflite_runtime.interpreter import Interpreter
    has_tflite = True
    print("Using tflite_runtime for prediction")
except Exception as e:
    import traceback
    import_error_log += f"Failed to import tflite_runtime:\n{traceback.format_exc()}\n"
    try:
        import tensorflow as tf
        Interpreter = tf.lite.Interpreter
        has_tflite = True
        print("Using tensorflow.lite Interpreter for prediction")
    except Exception as e2:
        import_error_log += f"Failed to import tensorflow.lite:\n{traceback.format_exc()}\n"

# We will load TensorFlow Keras dynamically for PC fallback
has_keras = False
try:
    import tensorflow as tf
    has_keras = True
except ImportError:
    print("Warning: TensorFlow Keras is not installed. Will fallback to TFLite or Mock predictions.")



class WelcomeScreen(Screen):
    pass

class PredictionScreen(Screen):
    selected_image_path = StringProperty("")
    selected_model = StringProperty("mobilenet") # default model
    
    def open_image_source_dialog(self):
        # Create a vertical BoxLayout
        layout = BoxLayout(orientation='vertical', padding=15, spacing=15)
        
        popup = Popup(
            title="Pilih Sumber Gambar",
            content=layout,
            size_hint=(0.85, 0.45),
            auto_dismiss=True
        )
        
        btn_camera = MDRaisedButton(
            text="Kamera (Ambil Foto)",
            md_bg_color=[0.1, 0.27, 0.12, 1],
            size_hint_x=1,
            height=50,
            on_release=lambda x: [popup.dismiss(), self.take_photo()]
        )
        
        btn_gallery = MDRaisedButton(
            text="Galeri (Pilih Berkas)",
            md_bg_color=[0.1, 0.27, 0.12, 1],
            size_hint_x=1,
            height=50,
            on_release=lambda x: [popup.dismiss(), self.open_file_chooser()]
        )
        
        btn_cancel = MDRaisedButton(
            text="Batal",
            md_bg_color=[0.5, 0.5, 0.5, 1],
            size_hint_x=1,
            height=50,
            on_release=lambda x: popup.dismiss()
        )
        
        layout.add_widget(btn_camera)
        layout.add_widget(btn_gallery)
        layout.add_widget(btn_cancel)
        
        popup.open()

    def take_photo(self):
        from kivy.app import App
        import time
        app = App.get_running_app()
        temp_dir = app.user_data_dir
        self.temp_camera_path = os.path.join(temp_dir, f"temp_pic_{int(time.time())}.jpg")
        
        if camera:
            try:
                camera.take_picture(filename=self.temp_camera_path, on_complete=self.camera_callback)
            except Exception as e:
                self.show_error_dialog(f"Gagal membuka kamera: {str(e)}")
        else:
            self.show_error_dialog("Kamera tidak didukung di platform ini (gunakan HP Android).")

    def camera_callback(self, filepath):
        if filepath and os.path.exists(self.temp_camera_path):
            self.selected_image_path = self.temp_camera_path
        elif isinstance(filepath, str) and os.path.exists(filepath):
            self.selected_image_path = filepath
        else:
            if os.path.exists(self.temp_camera_path):
                self.selected_image_path = self.temp_camera_path

    def show_error_dialog(self, text):
        dialog = MDDialog(
            title="Peringatan",
            text=text,
            buttons=[
                MDRaisedButton(
                    text="OK",
                    on_release=lambda x: dialog.dismiss()
                )
            ]
        )
        dialog.open()

    def open_file_chooser(self):
        from kivy.utils import platform
        if platform == 'android':
            try:
                from plyer import filechooser
                filechooser.open_file(on_selection=self.handle_gallery_selection)
            except Exception as e:
                self.show_error_dialog(f"Gagal membuka galeri: {str(e)}")
        else:
            # Fallback to standard Kivy FileChooserPopup for desktop
            content = FileChooserPopup(select_callback=self.select_image)
            self._popup = Popup(title="Pilih Gambar Daun Jagung", content=content,
                                size_hint=(0.95, 0.9))
            self._popup.open()

    def handle_gallery_selection(self, selection):
        if selection:
            uri_str = selection[0]
            local_path = self.copy_android_uri_to_file(uri_str)
            if local_path:
                self.selected_image_path = local_path

    def copy_android_uri_to_file(self, uri_str):
        from kivy.utils import platform
        if platform != 'android':
            return uri_str
            
        if not uri_str.startswith('content://'):
            if uri_str.startswith('file://'):
                return uri_str[7:]
            return uri_str
            
        try:
            from jnius import autoclass
            from kivy.app import App
            
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            activity = PythonActivity.mActivity
            content_resolver = activity.getContentResolver()
            
            Uri = autoclass('android.net.Uri')
            uri = Uri.parse(uri_str)
            
            input_stream = content_resolver.openInputStream(uri)
            
            app = App.get_running_app()
            import time
            local_path = os.path.join(app.user_data_dir, f"gallery_img_{int(time.time())}.jpg")
            
            FileOutputStream = autoclass('java.io.FileOutputStream')
            out_stream = FileOutputStream(local_path)
            
            from jnius import jarray
            buffer = jarray('b', 8192)
            
            while True:
                bytes_read = input_stream.read(buffer)
                if bytes_read == -1:
                    break
                out_stream.write(buffer, 0, bytes_read)
                
            input_stream.close()
            out_stream.close()
            return local_path
        except Exception as e:
            print("Error copying URI:", e)
            return uri_str
        
    def select_image(self, path):
        self.selected_image_path = path
        self._popup.dismiss()
        
    def select_model_type(self, model_type):
        self.selected_model = model_type
        # Update selection visual states
        if model_type == "mobilenet":
            self.ids.card_mobilenet.md_bg_color = [0.88, 0.95, 0.88, 1]
            self.ids.card_mobilenet.line_color = [0.1, 0.27, 0.12, 1]
            self.ids.card_cnn.md_bg_color = [1, 1, 1, 1]
            self.ids.card_cnn.line_color = [0.85, 0.85, 0.85, 1]
            self.ids.label_keterangan.text = "MobileNetV2 umumnya memberikan akurasi lebih tinggi dan komputasi lebih efisien."
        else:
            self.ids.card_cnn.md_bg_color = [0.88, 0.95, 0.88, 1]
            self.ids.card_cnn.line_color = [0.1, 0.27, 0.12, 1]
            self.ids.card_mobilenet.md_bg_color = [1, 1, 1, 1]
            self.ids.card_mobilenet.line_color = [0.85, 0.85, 0.85, 1]
            self.ids.label_keterangan.text = "Custom CNN adalah model konvolusi standar yang dilatih dari awal (scratch) pada dataset."

    def process_prediction(self):
        if not self.selected_image_path:
            # Show warning dialog
            dialog = MDDialog(
                title="Peringatan",
                text="Silakan unggah gambar daun jagung terlebih dahulu!",
                buttons=[
                    MDRaisedButton(
                        text="OK",
                        on_release=lambda x: dialog.dismiss()
                    )
                ]
            )
            dialog.open()
            return
            
        # Trigger prediction and pass data to ResultScreen
        app = MDApp.get_running_app()
        result_screen = app.root.get_screen('result')
        result_screen.run_classification(self.selected_image_path, self.selected_model)
        app.root.current = 'result'

class ResultScreen(Screen):
    image_path = StringProperty("")
    pred_class = StringProperty("")
    pred_confidence = StringProperty("")
    model_name = StringProperty("")
    
    # Probabilities for 4 classes
    prob_blight = NumericProperty(0)
    prob_rust = NumericProperty(0)
    prob_gray = NumericProperty(0)
    prob_healthy = NumericProperty(0)
    
    prob_blight_pct = StringProperty("0%")
    prob_rust_pct = StringProperty("0%")
    prob_gray_pct = StringProperty("0%")
    prob_healthy_pct = StringProperty("0%")

    def run_classification(self, img_path, model_type):
        self.image_path = img_path
        self.model_name = "MobileNetV2" if model_type == "mobilenet" else "Custom CNN"
        
        # Call model predictor
        app = MDApp.get_running_app()
        predicted_class, probabilities = app.predictor.predict(img_path, model_type)
        
        # Format display name
        display_names = {
            'Blight': 'Blight',
            'Common_Rust': 'Common Rust',
            'Gray_Leaf_Spot': 'Gray Leaf Spot',
            'Healthy': 'Healthy'
        }
        self.pred_class = display_names.get(predicted_class, predicted_class)
        
        # Map probabilities
        class_order = app.predictor.class_names
        
        idx_blight = class_order.index('Blight') if 'Blight' in class_order else 0
        idx_rust = class_order.index('Common_Rust') if 'Common_Rust' in class_order else 1
        idx_gray = class_order.index('Gray_Leaf_Spot') if 'Gray_Leaf_Spot' in class_order else 2
        idx_healthy = class_order.index('Healthy') if 'Healthy' in class_order else 3
        
        p_blight = probabilities[idx_blight]
        p_rust = probabilities[idx_rust]
        p_gray = probabilities[idx_gray]
        p_healthy = probabilities[idx_healthy]
        
        # Set numeric values (0 to 100 for ProgressBars)
        self.prob_blight = p_blight * 100
        self.prob_rust = p_rust * 100
        self.prob_gray = p_gray * 100
        self.prob_healthy = p_healthy * 100
        
        # Set text labels
        self.prob_blight_pct = f"{round(p_blight * 100)}%"
        self.prob_rust_pct = f"{round(p_rust * 100)}%"
        self.prob_gray_pct = f"{round(p_gray * 100)}%"
        self.prob_healthy_pct = f"{round(p_healthy * 100)}%"
        
        # Find predicted confidence
        max_prob = max(p_blight, p_rust, p_gray, p_healthy)
        self.pred_confidence = f"{max_prob:.2f} ({round(max_prob * 100)}%)"

    def save_results(self):
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = f"klasifikasi_hasil_{timestamp}.txt"
        
        try:
            with open(report_path, "w") as f:
                f.write(f"=== LAPORAN HASIL KLASIFIKASI PENYAKIT DAUN JAGUNG ===\n")
                f.write(f"Tanggal: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Model: {self.model_name}\n")
                f.write(f"Gambar Input: {self.image_path}\n")
                f.write(f"Prediksi Utama: {self.pred_class} ({self.pred_confidence})\n\n")
                f.write(f"Probabilitas Kelas:\n")
                f.write(f"- Blight: {self.prob_blight_pct}\n")
                f.write(f"- Common Rust: {self.prob_rust_pct}\n")
                f.write(f"- Gray Leaf Spot: {self.prob_gray_pct}\n")
                f.write(f"- Healthy: {self.prob_healthy_pct}\n")
                
            dialog = MDDialog(
                title="Berhasil Disimpan",
                text=f"Hasil klasifikasi telah disimpan di:\n{os.path.abspath(report_path)}",
                buttons=[
                    MDRaisedButton(
                        text="OK",
                        on_release=lambda x: dialog.dismiss()
                    )
                ]
            )
            dialog.open()
        except Exception as e:
            print("Error saving results:", e)

class FileChooserPopup(BoxLayout):
    select_callback = ObjectProperty(None)
    
    def __init__(self, select_callback, **kwargs):
        super().__init__(**kwargs)
        self.select_callback = select_callback
        self.orientation = 'vertical'
        self.padding = 10
        self.spacing = 10
        
        # File chooser configuration
        self.file_chooser = FileChooserIconView(
            filters=['*.png', '*.jpg', '*.jpeg'],
            path=os.path.expanduser('~')
        )
        self.add_widget(self.file_chooser)
        
        # Buttons layout
        btn_layout = BoxLayout(size_hint_y=0.15, spacing=10, padding=5)
        
        select_btn = MDRaisedButton(
            text="Pilih Gambar",
            md_bg_color=[0.1, 0.27, 0.12, 1], # Forest Green
            on_release=self.on_select
        )
        cancel_btn = MDRaisedButton(
            text="Batal",
            md_bg_color=[0.5, 0.5, 0.5, 1],
            on_release=self.on_cancel
        )
        
        btn_layout.add_widget(select_btn)
        btn_layout.add_widget(cancel_btn)
        self.add_widget(btn_layout)
        
    def on_select(self, instance):
        if self.file_chooser.selection:
            selected_path = self.file_chooser.selection[0]
            if self.select_callback:
                self.select_callback(selected_path)
                
    def on_cancel(self, instance):
        # Close popup
        self.parent.parent.parent.dismiss()

class ModelPredictor:
    def __init__(self):
        self.cnn_model = None
        self.mobilenet_model = None
        self.cnn_is_tflite = False
        self.mobilenet_is_tflite = False
        self.class_names = ['Blight', 'Common_Rust', 'Gray_Leaf_Spot', 'Healthy']
        self.error_log = import_error_log
        
        # 1. Load CNN Model
        if os.path.exists("models/cnn_model.tflite") and Interpreter is not None:
            try:
                self.cnn_model = Interpreter(model_path="models/cnn_model.tflite")
                self.cnn_model.allocate_tensors()
                self.cnn_is_tflite = True
                print("Loaded CNN TFLite model successfully")
            except Exception as e:
                import traceback
                self.error_log += f"Error loading CNN TFLite:\n{traceback.format_exc()}\n"
                print("Error loading CNN TFLite model:", e)
                
        if self.cnn_model is None and os.path.exists("models/cnn_model.keras") and has_keras:
            try:
                self.cnn_model = tf.keras.models.load_model("models/cnn_model.keras")
                self.cnn_is_tflite = False
                print("Loaded CNN Keras model successfully (fallback)")
            except Exception as e:
                print("Error loading CNN Keras model:", e)
                
        # 2. Load MobileNetV2 Model
        if os.path.exists("models/mobilenet_model.tflite") and Interpreter is not None:
            try:
                self.mobilenet_model = Interpreter(model_path="models/mobilenet_model.tflite")
                self.mobilenet_model.allocate_tensors()
                self.mobilenet_is_tflite = True
                print("Loaded MobileNetV2 TFLite model successfully")
            except Exception as e:
                import traceback
                self.error_log += f"Error loading MobileNetV2 TFLite:\n{traceback.format_exc()}\n"
                print("Error loading MobileNetV2 TFLite model:", e)
                
        if self.mobilenet_model is None and os.path.exists("models/mobilenet_model.keras") and has_keras:
            try:
                self.mobilenet_model = tf.keras.models.load_model("models/mobilenet_model.keras")
                self.mobilenet_is_tflite = False
                print("Loaded MobileNetV2 Keras model successfully (fallback)")
            except Exception as e:
                print("Error loading MobileNetV2 Keras model:", e)
                
        if os.path.exists("models/class_names.txt"):
            try:
                with open("models/class_names.txt") as f:
                    self.class_names = [line.strip() for line in f.readlines()]
                print("Loaded class names:", self.class_names)
            except Exception as e:
                print("Error loading class names:", e)

    def predict(self, img_path, model_type):
        model = self.cnn_model if model_type == 'cnn' else self.mobilenet_model
        is_tflite = self.cnn_is_tflite if model_type == 'cnn' else self.mobilenet_is_tflite
        
        if model is None:
            # Fallback mock prediction if models are not trained yet
            print(f"Model {model_type} tidak ditemukan di folder 'models'. Menggunakan simulasi prediksi...")
            import random
            probs = [random.uniform(0.05, 0.20) for _ in range(4)]
            max_idx = random.randint(0, 3)
            probs[max_idx] = random.uniform(0.70, 0.95)
            total = sum(probs)
            probs = [p / total for p in probs]
            return self.class_names[max_idx], probs
            
        try:
            img = Image.open(img_path).convert('RGB')
            img = img.resize((224, 224))
            img_array = np.array(img, dtype=np.float32)
            img_array = np.expand_dims(img_array, axis=0) # shape (1, 224, 224, 3)
            
            if is_tflite:
                # Running TFLite inference
                input_details = model.get_input_details()
                output_details = model.get_output_details()
                
                model.set_tensor(input_details[0]['index'], img_array)
                model.invoke()
                
                predictions = model.get_tensor(output_details[0]['index'])
                prob_list = predictions[0].tolist()
            else:
                # Running Keras inference
                predictions = model.predict(img_array)
                prob_list = predictions[0].tolist()
                
            max_idx = np.argmax(prob_list)
            return self.class_names[max_idx], prob_list
        except Exception as e:
            print("Error running prediction:", e)
            return self.class_names[0], [0.25, 0.25, 0.25, 0.25]


class CornLeafApp(MDApp):
    def build(self):
        self.title = "Corn Leaf Disease Classifier"
        self.theme_cls.primary_palette = "Green"
        self.theme_cls.primary_hue = "800" # Forest Green style
        
        # Load KV layout file
        Builder.load_file('corn_disease.kv')
        
        # Initialize model predictor
        self.predictor = ModelPredictor()
        
        # Create and return ScreenManager
        sm = ScreenManager()
        sm.add_widget(WelcomeScreen(name='welcome'))
        sm.add_widget(PredictionScreen(name='predict'))
        sm.add_widget(ResultScreen(name='result'))
        
        return sm

    def on_start(self):
        from kivy.utils import platform
        if platform == 'android':
            from android.permissions import request_permissions, Permission
            request_permissions([
                Permission.CAMERA,
                Permission.WRITE_EXTERNAL_STORAGE,
                Permission.READ_EXTERNAL_STORAGE
            ])
            
            # Bypassing FileUriExposedException on Android 7.0+
            try:
                from jnius import autoclass
                StrictMode = autoclass('android.os.StrictMode')
                StrictMode.disableDeathOnFileUriExposure()
                print("Bypassed StrictMode FileUriExposedException successfully")
            except Exception as e:
                print("Failed to bypass StrictMode:", e)
                
        # Check if there was any error during TFLite model loading
        if self.predictor.error_log:
            # We delay the dialog slightly using Clock to let the window draw first
            from kivy.clock import Clock
            Clock.schedule_once(self.show_startup_error_dialog, 1)

    def show_startup_error_dialog(self, dt):
        error_msg = self.predictor.error_log
        dialog = MDDialog(
            title="Peringatan: Model AI Gagal Dimuat",
            text=f"Aplikasi terpaksa menggunakan simulasi prediksi acak karena kegagalan pemuatan model:\n\n{error_msg}",
            buttons=[
                MDRaisedButton(
                    text="Mengerti",
                    on_release=lambda x: dialog.dismiss()
                )
            ]
        )
        dialog.open()

if __name__ == "__main__":
    CornLeafApp().run()
