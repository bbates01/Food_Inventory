from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen
from kivymd.app import MDApp
from kivymd.uix.list import OneLineAvatarListItem
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.boxlayout import BoxLayout
from kivymd.uix.button import MDIconButton
from database_setup import FoodDatabase
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition, FadeTransition, WipeTransition, NoTransition
from kivy.clock import Clock
from kivy.graphics.texture import Texture
from kivy.uix.camera import Camera
import cv2
import threading
import requests
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDFlatButton
import numpy as np
from pyzbar.pyzbar import decode

# Initialize database instance
db = FoodDatabase()

# Load Kivy files
Builder.load_file("kivy_files/home.kv")
Builder.load_file("kivy_files/add_item.kv")
Builder.load_file("kivy_files/meals.kv")


class HomeScreen(Screen):
    # In your HomeScreen class
    def on_enter(self):
        """Load inventory items when entering the screen."""
        self.ids.food_list.clear_widgets()
        items = db.get_all_items()
        for item in items:
            self.add_food_item_to_list(item)
        
        # If no items, show a message
        if not items:
            self.ids.food_list.add_widget(
                BoxLayout(
                    orientation="vertical",
                    size_hint_y=None,
                    height="100dp"
                )
            )
            self.ids.food_list.add_widget(
                MDLabel(
                    text="No items in your inventory yet.\nTap + to add food items.",
                    halign="center",
                    theme_text_color="Secondary",
                    padding=("0dp", "40dp")
                )
            )

    def add_food_item_to_list(self, item):
        # Create layout components with standard Kivy widgets
        box = BoxLayout(orientation="horizontal", size_hint_y=None, height="80dp")
        
        # For the icon, use MDIconButton instead of MDIcon
        icon_name = "food-apple"
        if item[2] == "Dairy":
            icon_name = "cup"
        elif item[2] == "Meat":
            icon_name = "food-steak"
        
        # Create an icon button using md_icons
        icon_button = MDIconButton(icon=icon_name)
        # Or for a non-clickable icon, use a Label with the icon character
        # icon_label = Label(text=md_icons[icon_name], font_name="path/to/materialdesignicons-webfont.ttf")
        
        # Add other components
        name_label = MDLabel(text=item[1])
        expiry_label = MDLabel(text=f"Expires: {item[4]}")
        qty_label = MDLabel(text=f"Qty: {item[3]}")

        # Add delete button - important to capture the item ID
        delete_button = MDIconButton(
            icon="delete",
            theme_text_color="Custom",
            text_color=(0.9, 0.2, 0.2, 1), # Red color
            on_release=lambda x, item_id=item[0]: self.delete_food_item(item_id)
        )
        
        box.add_widget(icon_button)  # or icon_label
        box.add_widget(name_label)
        box.add_widget(expiry_label)
        box.add_widget(qty_label)
        box.add_widget(delete_button)
        
        self.ids.food_list.add_widget(box)

    def go_to_meal_suggestions(self):
        """Navigate to meal suggestions with right-to-left animation."""
        self.manager.transition = SlideTransition(direction='left')
        self.manager.transition.duration = 0.1
        self.manager.current = 'meal_suggestions'

    def go_to_add_item(self):
        """Navigate to add items screen with fade animation."""
        self.manager.transition = SlideTransition(direction='left')
        self.manager.transition.duration = 0.1
        self.manager.current = 'add_item'

    def delete_food_item(self, item_id):
        """Delete a food item from the databas."""
        # Show a confirmation dialog
        from kivymd.uix.dialog import MDDialog
        from kivymd.uix.button import MDFlatButton

        # Create confirmation dialog
        dialog = MDDialog(
            title="Delete Item",
            text="Are you sure you want to delete this item?",
            buttons=[
                MDFlatButton(
                    text="Cancel",
                    on_release=lambda x: dialog.dismiss()
                ),
                MDFlatButton(
                    text="Delete",
                    text_color=(0.9, 0.2, 0.2, 1), # Red color
                    on_release=lambda x: self._confirm_delete(item_id, dialog)
                ),
            ],
        )
        dialog.open()

    def _confirm_delete(self, item_id, dialog):
        """Execute the delete operation after confirmation"""
        dialog.dismiss()
        db.delete_item(item_id)
        # Refresh the screen
        self.on_enter()


class AddItemScreen(Screen):
    def add_item(self):
        """Add a new food item to the database."""
        name = self.ids.item_name.text
        category = self.ids.item_category.text
        quantity = int(self.ids.item_quantity.text)
        expiration_date = self.ids.item_expiration.text

        # Input validation
        if not name or not category or not expiration_date:
            self.show_error_dialog("Please fill out all required fields.")
            return
        
        try:
            quantity = int(quantity) if quantity else 1
        except ValueError:
            self.show_error_dialog("Quantity must be a number.")
            return
        
        db.add_item(name=name, category=category, quantity=quantity, expiration_date=expiration_date)
        # Set transition direction explicitly
        self.manager.transition = SlideTransition(direction='right')
        self.manager.transition.duration = 0.1
        self.manager.current = "home"
        self.manager.get_screen("home").on_enter()
    
    def show_error_dialog(self, text):
        dialog = MDDialog(
            title="Error",
            text=text,
            buttons=[
                MDFlatButton(
                    text="OK",
                    on_release=lambda x: dialog.dismiss()
                )
            ]
        )
        dialog.open()

    def go_back_to_home(self):
        """Navigate back to homescreen with fade animation."""
        self.manager.transition = SlideTransition(direction='right')
        self.manager.transition.duration = 0.1
        self.manager.current = 'home'

    def go_to_scan_barcode(self):
        """Navigate to barcode scanning screen."""
        self.manager.transition = NoTransition()
        self.manager.current = 'barcode_scan'


class MealSuggestionsScreen(Screen):
    def on_enter(self):
        """Generate meal suggestions based on inventory."""
        # Clear previous widgets first to avoid duplication
        self.ids.meal_container.clear_widgets()
        
        items = db.get_all_items()
        ingredients = [item[1] for item in items]
        
        # Placeholder meal suggestions logic
        meals = [
            {"name": "Pasta", "ingredients": ["Pasta", "Tomato Sauce", "Cheese"]},
            {"name": "Salad", "ingredients": ["Lettuce", "Tomato", "Cucumber"]},
            {"name": "Omelette", "ingredients": ["Eggs", "Cheese", "Milk"]},
        ]

        has_suggestions = False
        for meal in meals:
            available_ingredients = [i for i in meal["ingredients"] if i in ingredients]
            if len(available_ingredients) >= 2:  # At least 2 ingredients available
                has_suggestions = True
                # Create a card for each meal suggestion
                card = MDCard(
                    orientation="vertical",
                    size_hint=(1, None),
                    height="120dp",
                    padding="8dp",
                    spacing="8dp",
                    md_bg_color=[0.9, 0.9, 0.9, 1],
                    radius=[10, 10, 10, 10],
                    elevation=1,
                    margin="10dp"
                )
                
                # Add meal name to the card
                card.add_widget(MDLabel(
                    text=meal["name"],
                    theme_text_color="Primary",
                    font_style="H6",
                    halign="center"
                ))
                
                # Add ingredients info
                ingredients_text = f"Ingredients: {', '.join(meal['ingredients'])}\n"
                ingredients_text += f"You have: {', '.join(available_ingredients)}"
                card.add_widget(MDLabel(
                    text=ingredients_text,
                    theme_text_color="Secondary",
                    halign="center"
                ))
                
                self.ids.meal_container.add_widget(card)
        
        # Show message if no suggestions available
        if not has_suggestions:
            # Create a card with centered text
            card = MDCard(
                orientation="vertical",
                size_hint=(1,None),
                height="150dp",
                padding="20dp",
                md_bg_color=[0.95, 0.95, 0.95, 1],
                radius=[10, 10, 10, 10],
                elevation=1
            )
        
            # Add the message label
            card.add_widget(MDLabel(
                text="No meal suggestions available with your current inventory.",
                theme_text_color="Primary",
                halign="center",
                valign="center",
                size_hint_y=1
            ))

            self.ids.meal_container.add_widget(card)  # Fixed typo: 'contatiner' to 'container'

    def go_back_to_home(self):
        """Navigate back to home with left-to-right animation."""
        self.manager.transition = SlideTransition(direction='right')
        self.manager.transition.duration = 0.1
        self.manager.current = 'home'
        

class BarcodeScanScreen(Screen):
    dialog = None
    capture = None
    is_scanning = False

    def on_enter(self):
        """Initialize camera when entering this screen."""
        self.start_scanning()

    def on_leave(self):
        """Stop camera when leaving this screen."""
        self.stop_scanning()

    def start_scanning(self):
        """Start the camera and scanning process."""
        self.is_scanning = True
        self.ids.scan_button.text = "Manual Entry"  # Change button text

        # Initialize camera with OpenCV
        # Try different camera indices
        for i in range(3):  # Try indices 0, 1, 2
            self.capture = cv2.VideoCapture(i)
            ret, frame = self.capture.read()
            if ret:
                break  # found a working camera
            else:
                if self.capture:
                    self.capture.release()
        if not self.capture or not ret:
            self.show_error("Could not initialize camera. Try manual entry.")
            return
        
        Clock.schedule_interval(self.update, 1.0/30.0)  # 30 FPS

    def stop_scanning(self):
        """Stop the camera and scanning process."""
        self.is_scanning = False
        Clock.unschedule(self.update)
        if self.capture:
            self.capture.release()
            self.capture = None
        self.ids.scan_button.text = "Enter Manually"
    
    def toggle_scanning(self):
        """Use button for manual entry."""
        self.manual_barcode_entry()

    def update(self, dt):
        """Update camera frame and check for barcodes using pyzbar."""
        if not self.capture or not self.is_scanning:
            return
        
        # Read frame from camera
        ret, frame = self.capture.read()
        if not ret:
            return
            
        # Convert frame for display
        buf = cv2.flip(frame, 0).tostring()
        texture = Texture.create(size=(frame.shape[1], frame.shape[0]), colorfmt='bgr')
        texture.blit_buffer(buf, colorfmt='bgr', bufferfmt='ubyte')
        self.ids.camera_preview.texture = texture
            
        try:
            # Convert to grayscale for better detection
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Try scanning for barcodes using pyzbar
            barcodes = decode(gray)
            
            if barcodes:
                for barcode in barcodes:
                    # Extract barcode data
                    barcode_data = barcode.data.decode("utf-8")
                    
                    # Draw rectangle around the barcode
                    (x, y, w, h) = barcode.rect
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                    
                    # Display barcode type and data
                    self.ids.detection_label.text = f"Detected: {barcode_data}"
                    
                    # Process the barcode after a short delay to show feedback to the user
                    Clock.schedule_once(lambda dt, data=barcode_data: self.process_delayed(data), 0.5)
                    return
                    
            # If pyzbar detection fails, try QR code detection as backup
            detector = cv2.QRCodeDetector()
            data, bbox, _ = detector.detectAndDecode(gray)
                
            if data:
                # QR code detected
                self.ids.detection_label.text = "QR Code detected!"
                # Use a short delay to give user feedback before processing
                Clock.schedule_once(lambda dt, code=data: self.process_delayed(code), 0.5)
                return
                
        except Exception as e:
            print(f"Detection error: {e}")
            # If pyzbar fails, don't show an error to the user - just keep scanning
            # This allows the app to fall back to manual entry if pyzbar library issues occur

    def process_delayed(self, barcode_data):
        """Process barcode after a short delay to show visual feedback"""
        self.process_barcode(barcode_data)
        self.stop_scanning()

    def manual_barcode_entry(self):
        """Allow manual entry of a barcode."""
        from kivymd.uix.textfield import MDTextField

        content = MDTextField(
            hint_text="Enter barcode number",
        )

        self.dialog = MDDialog(
            title="Manual Entry",
            type="custom",
            content_cls=content,
            buttons=[
                MDFlatButton(
                    text="Cancel",
                    on_release=lambda x: self.dialog.dismiss()
                ),
                MDFlatButton(
                    text="Look Up",
                    on_release=lambda x: self.lookup_manual_entry(content.text)
                )
            ]
        )
        self.dialog.open()

    def lookup_manual_entry(self, barcode):
        """Process manually entered barcode."""
        if not barcode:
            self.show_error("Please enter a barcode number")
            return
        
        self.dialog.dismiss()
        self.process_barcode(barcode)

    def process_barcode(self, barcode_data):
        """Process the scanned barcode data."""
        # Show dialog while fetching product info
        self.dialog = MDDialog(
            title="Scanning...",
            text=f"Lookup up product information for barcode: {barcode_data}"
        )
        self.dialog.open()

        # Start a thread to fetch product info
        threading.Thread(target=self.fetch_product_info, args=(barcode_data,)).start()
    
    def fetch_product_info(self, barcode_data):
        """Fetch product information from a barcode database."""
        try:
            # Example: using Open Food Facts API
            response = requests.get(f"https://world.openfoodfacts.org/api/v0/product/{barcode_data}.json")
            product_data = response.json()

            if product_data.get('status') == 1:
                product = product_data.get('product', {})
                product_name = product.get('product_name', 'Unknown Product')
                category = product.get('categories_tags', ['unknown'])[0].replace('en:', '') if product.get('categories_tags') else 'Unknown'
                
                # Store data for use in main thread
                self.product_info = (product_name, category)
                
                # Schedule UI updates on the main thread
                Clock.schedule_once(self._show_product_info_main_thread, 0)
            else:
                # Schedule error on main thread
                Clock.schedule_once(lambda dt: self.show_error("Product not found"), 0)
        except Exception as e:
            error_message = f"Error: {str(e)}"
            # Schedule error on main thread
            Clock.schedule_once(lambda dt, msg=error_message: self.show_error(msg), 0)

    def _show_product_info_main_thread(self, dt):
        """Called on the main thread to update UI after product fetch."""
        # Dismiss any existing dialog
        if self.dialog:
            self.dialog.dismiss()
        
        # Show product info with the data stored from the worker thread
        if hasattr(self, 'product_info'):
            name, category = self.product_info
            self.show_product_info(name, category)

    def show_product_info(self, name, category):
        """Show dialog with product information and options to add to inventory."""
        self.dialog = MDDialog(
            title="Product Found",
            text=f"Name: {name}\nCategory: {category}",
            buttons=[
                MDFlatButton(
                    text="Cancel",
                    on_release=lambda x: self.dialog.dismiss()
                ),
                MDFlatButton(
                    text="Add to Inventory",
                    on_release=lambda x: self.add_to_inventory(name, category)
                )
            ]
        )
        self.dialog.open()

    def add_to_inventory(self, name, category):
        """Add scanned item to inventory."""
        # Dismiss the dialog
        if self.dialog:
            self.dialog.dismiss()

        # Set the values in the add item form
        add_screen = self.manager.get_screen('add_item')
        add_screen.ids.item_name.text = name
        add_screen.ids.item_category.text = category

        # Navigate to add item screen to complete the form
        self.manager.transition = NoTransition()
        self.manager.current = 'add_item'

    def show_error(self, message):
        """Show error dialog - must be called from main thread."""
        # Always schedule on the main thread to be safe
        Clock.schedule_once(lambda dt: self._show_error_impl(message), 0)

    def _show_error_impl(self, message):
        """Implementation of error dialog display - called on the main thread."""
        if self.dialog:
            self.dialog.dismiss()
            
        self.dialog = MDDialog(
            title="Error",
            text=message,
            buttons=[
                MDFlatButton(
                    text="OK",
                    on_release=lambda x: self.dialog.dismiss()
                )
            ]
        )
        self.dialog.open()

    def go_back_to_add_item(self):
        """Navigate back to add item screen."""
        self.stop_scanning()
        self.manager.transition = SlideTransition(direction='right')
        self.manager.current = 'add_item'


class FoodInventoryApp(MDApp):
    def build(self):
        # Load the barcode scan kv file
        Builder.load_file("kivy_files/barcode_scan.kv")

        # Create a screen manager with default transition
        sm = ScreenManager(transition=NoTransition())
        sm.add_widget(HomeScreen(name="home"))
        sm.add_widget(AddItemScreen(name="add_item"))
        sm.add_widget(MealSuggestionsScreen(name="meal_suggestions"))
        sm.add_widget(BarcodeScanScreen(name="barcode_scan"))
        
        return sm


if __name__ == "__main__":
    FoodInventoryApp().run()
