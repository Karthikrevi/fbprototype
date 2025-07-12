
import json
import os
from flask import session, request

class I18nManager:
    def __init__(self):
        self.translations = {}
        self.default_language = 'en'
        self.supported_languages = {
            'en': 'English',
            'hi': 'हिंदी (Hindi)',
            'ta': 'தமிழ் (Tamil)',
            'te': 'తెలుగు (Telugu)',
            'kn': 'ಕನ್ನಡ (Kannada)',
            'ml': 'മലയാളം (Malayalam)',
            'bn': 'বাংলা (Bengali)',
            'gu': 'ગુજરાતી (Gujarati)',
            'mr': 'मराठी (Marathi)',
            'pa': 'ਪੰਜਾਬੀ (Punjabi)',
            'or': 'ଓଡ଼ିଆ (Odia)',
            'as': 'অসমীয়া (Assamese)',
            'ur': 'اردو (Urdu)',
            'es': 'Español',
            'fr': 'Français',
            'de': 'Deutsch',
            'pt': 'Português',
            'ar': 'العربية',
            'zh': '中文',
            'ja': '日本語',
            'ko': '한국어',
            'ru': 'Русский'
        }
        self.load_translations()
    
    def load_translations(self):
        """Load all translation files"""
        translations_dir = 'translations'
        if not os.path.exists(translations_dir):
            os.makedirs(translations_dir)
        
        for lang_code in self.supported_languages.keys():
            try:
                with open(f'{translations_dir}/{lang_code}.json', 'r', encoding='utf-8') as f:
                    self.translations[lang_code] = json.load(f)
            except FileNotFoundError:
                if lang_code == 'en':
                    # Create default English translations
                    self.translations[lang_code] = self.get_default_translations()
                    self.save_translation_file(lang_code)
                else:
                    # Copy English as fallback
                    self.translations[lang_code] = self.translations.get('en', {})
    
    def get_default_translations(self):
        """Default English translations"""
        return {
            # Navigation
            'home': 'Home',
            'login': 'Login',
            'register': 'Register',
            'logout': 'Logout',
            'dashboard': 'Dashboard',
            'profile': 'Profile',
            'settings': 'Settings',
            'language': 'Language',
            
            # Dashboard
            'welcome_back': 'Welcome Back!',
            'your_pets': 'Your Pets',
            'marketplace': 'Marketplace',
            'grooming': 'Grooming',
            'veterinary': 'Veterinary',
            'boarding': 'Boarding',
            'my_bookings': 'My Bookings',
            'my_orders': 'My Orders',
            'messages': 'Messages',
            'furrwings_handlers': 'FurrWings Handlers',
            'my_travel_bookings': 'My Travel Bookings',
            'manage_pets': 'Manage Pets',
            
            # Pet Management
            'add_pet': 'Add Pet',
            'edit_pet': 'Edit Pet',
            'pet_name': 'Pet Name',
            'pet_breed': 'Pet Breed',
            'pet_birthday': 'Pet Birthday',
            'pet_parent_name': 'Pet Parent Name',
            'pet_parent_phone': 'Pet Parent Phone',
            'blood_type': 'Blood Type',
            'pet_photo': 'Pet Photo',
            'save': 'Save',
            'cancel': 'Cancel',
            'delete': 'Delete',
            
            # Marketplace
            'shop_products': 'Shop for pet products and supplies',
            'professional_grooming': 'Professional grooming services',
            'pet_healthcare': 'Healthcare for your pets',
            'safe_boarding': 'Safe and comfortable boarding',
            'price': 'Price',
            'quantity': 'Quantity',
            'add_to_cart': 'Add to Cart',
            'checkout': 'Checkout',
            'total': 'Total',
            'delivery_address': 'Delivery Address',
            'payment_method': 'Payment Method',
            'place_order': 'Place Order',
            
            # Bookings
            'book_service': 'Book Service',
            'select_service': 'Select Service',
            'select_date': 'Select Date',
            'select_time': 'Select Time',
            'confirm_booking': 'Confirm Booking',
            'booking_confirmed': 'Booking Confirmed',
            'pending': 'Pending',
            'confirmed': 'Confirmed',
            'completed': 'Completed',
            'cancelled': 'Cancelled',
            
            # Vendor/ERP
            'vendor_dashboard': 'Vendor Dashboard',
            'products': 'Products',
            'orders': 'Orders',
            'bookings': 'Bookings',
            'reports': 'Reports',
            'inventory': 'Inventory',
            'analytics': 'Analytics',
            'expenses': 'Expenses',
            'sales': 'Sales',
            'customers': 'Customers',
            'online': 'Online',
            'offline': 'Offline',
            'add_product': 'Add Product',
            'edit_product': 'Edit Product',
            'product_name': 'Product Name',
            'description': 'Description',
            'category': 'Category',
            'buy_price': 'Buy Price',
            'sale_price': 'Sale Price',
            'stock_quantity': 'Stock Quantity',
            'product_image': 'Product Image',
            
            # FurrWings
            'pet_passport': 'Pet Passport',
            'handlers': 'Handlers',
            'international_transport': 'International pet transport specialists',
            'veterinarian': 'Veterinarian',
            'handler': 'Handler',
            'isolation_center': 'Isolation Center',
            'travel_arrangements': 'Track your pet\'s international travel arrangements',
            'microchip_certificate': 'Microchip Certificate',
            'vaccination_records': 'Vaccination Records',
            'health_certificate': 'Health Certificate',
            'dgft_certificate': 'DGFT Certificate',
            'aqcs_certificate': 'AQCS Certificate',
            'quarantine_clearance': 'Quarantine Clearance',
            'upload_document': 'Upload Document',
            'document_status': 'Document Status',
            'approved': 'Approved',
            'rejected': 'Rejected',
            'under_review': 'Under Review',
            
            # Chat
            'start_conversation': 'Start Conversation',
            'type_message': 'Type your message...',
            'send': 'Send',
            'no_messages': 'No messages yet',
            'chat_with_vendor': 'Chat with Vendor',
            
            # Forms
            'email': 'Email',
            'password': 'Password',
            'confirm_password': 'Confirm Password',
            'name': 'Name',
            'phone': 'Phone',
            'address': 'Address',
            'city': 'City',
            'submit': 'Submit',
            'update': 'Update',
            'search': 'Search',
            'filter': 'Filter',
            'sort': 'Sort',
            'clear': 'Clear',
            
            # Status Messages
            'success': 'Success',
            'error': 'Error',
            'warning': 'Warning',
            'info': 'Information',
            'loading': 'Loading...',
            'saved_successfully': 'Saved successfully',
            'updated_successfully': 'Updated successfully',
            'deleted_successfully': 'Deleted successfully',
            'operation_failed': 'Operation failed',
            'invalid_input': 'Invalid input',
            'required_field': 'This field is required',
            
            # Time & Dates
            'today': 'Today',
            'yesterday': 'Yesterday',
            'tomorrow': 'Tomorrow',
            'this_week': 'This Week',
            'this_month': 'This Month',
            'date': 'Date',
            'time': 'Time',
            'duration': 'Duration',
            
            # Numbers & Currency
            'currency_symbol': '₹',
            'items': 'items',
            'per_unit': 'per unit',
            'total_amount': 'Total Amount',
            'subtotal': 'Subtotal',
            'tax': 'Tax',
            'discount': 'Discount',
            'shipping': 'Shipping',
            
            # Common Actions
            'view': 'View',
            'edit': 'Edit',
            'delete': 'Delete',
            'add': 'Add',
            'remove': 'Remove',
            'select': 'Select',
            'choose': 'Choose',
            'browse': 'Browse',
            'upload': 'Upload',
            'download': 'Download',
            'print': 'Print',
            'share': 'Share',
            'copy': 'Copy',
            'paste': 'Paste',
            'refresh': 'Refresh',
            'reload': 'Reload',
            'back': 'Back',
            'next': 'Next',
            'previous': 'Previous',
            'continue': 'Continue',
            'finish': 'Finish',
            'close': 'Close',
            'open': 'Open',
            'show': 'Show',
            'hide': 'Hide',
            'expand': 'Expand',
            'collapse': 'Collapse',
            
            # Settings
            'general_settings': 'General Settings',
            'account_settings': 'Account Settings',
            'privacy_settings': 'Privacy Settings',
            'notification_settings': 'Notification Settings',
            'language_settings': 'Language Settings',
            'theme_settings': 'Theme Settings',
            'save_settings': 'Save Settings',
            'reset_settings': 'Reset Settings',
            
            # Footer
            'about_us': 'About Us',
            'contact_us': 'Contact Us',
            'terms_of_service': 'Terms of Service',
            'privacy_policy': 'Privacy Policy',
            'help': 'Help',
            'support': 'Support',
            'faq': 'FAQ',
            
            # Branding
            'app_name': 'FurrButler',
            'app_tagline': 'Because pets deserve butlers too.',
            'furrwings': 'FurrWings',
            'furrwings_tagline': 'Global Pet Transport Excellence',
            
            # Additional translations
            'welcome': 'Welcome',
            'welcome_to': 'Welcome to',
            'to_home': 'to Home',
            'dont_have_account': "Don't have an account?",
            'select_language': 'Select Language',
            'language_updated_successfully': 'Language updated successfully',
            'invalid_language_selection': 'Invalid language selection',
            'track_grooming_appointments': 'Track your pet\'s grooming and service appointments',
            'track_marketplace_orders': 'Track your marketplace orders and deliveries',
            'chat_with_vendors': 'Chat with vendors and service providers',
            'email_notifications': 'Email Notifications',
            'sms_notifications': 'SMS Notifications',
            'make_profile_public': 'Make Profile Public',
            'allow_data_sharing': 'Allow Data Sharing'
        }
    
    def save_translation_file(self, lang_code):
        """Save translation file"""
        translations_dir = 'translations'
        if not os.path.exists(translations_dir):
            os.makedirs(translations_dir)
        
        with open(f'{translations_dir}/{lang_code}.json', 'w', encoding='utf-8') as f:
            json.dump(self.translations.get(lang_code, {}), f, ensure_ascii=False, indent=2)
    
    def get_current_language(self):
        """Get current language from session or default"""
        return session.get('language', self.default_language)
    
    def set_language(self, lang_code):
        """Set current language in session"""
        if lang_code in self.supported_languages:
            session['language'] = lang_code
            return True
        return False
    
    def translate(self, key, lang_code=None):
        """Get translation for a key"""
        if lang_code is None:
            lang_code = self.get_current_language()
        
        # Try to get translation in requested language
        if lang_code in self.translations:
            translation = self.translations[lang_code].get(key)
            if translation:
                return translation
        
        # Fallback to English
        if lang_code != 'en' and 'en' in self.translations:
            translation = self.translations['en'].get(key)
            if translation:
                return translation
        
        # Last resort: return the key itself
        return key.replace('_', ' ').title()
    
    def get_supported_languages(self):
        """Get list of supported languages"""
        return self.supported_languages

# Global instance
i18n = I18nManager()

# Template function for Jinja2
def t(key, lang_code=None):
    """Translation function for templates"""
    return i18n.translate(key, lang_code)

def get_supported_languages():
    """Get supported languages for templates"""
    return i18n.get_supported_languages()

def get_current_language():
    """Get current language for templates"""
    return i18n.get_current_language()
