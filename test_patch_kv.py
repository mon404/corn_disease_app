import sys
from kivy.lang import Builder
from kivymd.app import MDApp

# Import behaviors to trigger KV loading
import kivymd.uix.behaviors.elevation

class T(MDApp):
    def build(self):
        # Inspect Builder rules
        print("Looking for CommonElevationBehavior rules in Builder...")
        
        found = False
        for rule_name, rule_value in list(Builder.rules):
            if "CommonElevationBehavior" in str(rule_name):
                print("Found rule:", rule_name)
                found = True
                
        if not found:
            print("No rule found with name CommonElevationBehavior.")
            
        sys.exit(0)

if __name__ == '__main__':
    T().run()
