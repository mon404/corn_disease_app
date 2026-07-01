import sys
from kivy.lang import Builder
from kivymd.app import MDApp
from kivymd.uix.card import MDCard
from kivymd.uix.button import MDRaisedButton
from kivymd.uix.toolbar import MDTopAppBar

class T(MDApp):
    def build(self):
        # We will try to instantiate different widgets and catch the crash
        print("Testing MDTopAppBar...")
        try:
            w = MDTopAppBar(
                title="Test",
                elevation=2
            )
            print("MDTopAppBar instantiated successfully!")
        except Exception as e:
            print("MDTopAppBar CRASHED:", e)
            
        print("\nTesting MDCard with default style and elevation 1...")
        try:
            w = MDCard(
                radius=[15, 15, 15, 15],
                shadow_radius=[15, 15, 15, 15],
                elevation=1
            )
            print("MDCard instantiated successfully!")
        except Exception as e:
            print("MDCard CRASHED:", e)
            
        print("\nTesting MDRaisedButton...")
        try:
            w = MDRaisedButton(
                text="Test",
                radius=[10, 10, 10, 10]
            )
            print("MDRaisedButton instantiated successfully!")
        except Exception as e:
            print("MDRaisedButton CRASHED:", e)
            
        sys.exit(0)

if __name__ == '__main__':
    T().run()
