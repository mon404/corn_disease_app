import sys
from kivy.lang import Builder
from kivymd.app import MDApp
import kivymd.uix.behaviors.elevation

class T(MDApp):
    def build(self):
        print("Listing all rules in Builder...")
        for rule_key in Builder.rules:
            # rule_key is typically a string (e.g. 'MDCard') or a class object
            try:
                name = rule_key.__name__ if hasattr(rule_key, '__name__') else str(rule_key)
                print(f"Rule name: {name}")
            except Exception as e:
                print("Error printing rule key:", e)
        sys.exit(0)

if __name__ == '__main__':
    T().run()
