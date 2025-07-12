
// Language Switcher JavaScript
class LanguageSwitcher {
    constructor() {
        this.currentLanguage = this.getCurrentLanguage();
        this.init();
    }
    
    getCurrentLanguage() {
        // Get language from session or localStorage
        return localStorage.getItem('preferredLanguage') || 'en';
    }
    
    init() {
        // Add language switcher to navigation if not already present
        this.addLanguageSwitcherToNav();
        
        // Listen for language changes
        document.addEventListener('DOMContentLoaded', () => {
            this.setupLanguageSwitcher();
        });
    }
    
    addLanguageSwitcherToNav() {
        const navbars = document.querySelectorAll('.navbar, .header, nav');
        if (navbars.length > 0) {
            const navbar = navbars[0];
            const langSwitcher = this.createLanguageSwitcherDropdown();
            navbar.appendChild(langSwitcher);
        }
    }
    
    createLanguageSwitcherDropdown() {
        const languages = {
            'en': { name: 'English', flag: '🇺🇸' },
            'hi': { name: 'हिंदी', flag: '🇮🇳' },
            'ta': { name: 'தமிழ்', flag: '🇮🇳' },
            'te': { name: 'తెలుగు', flag: '🇮🇳' },
            'kn': { name: 'ಕನ್ನಡ', flag: '🇮🇳' },
            'ml': { name: 'മലയാളം', flag: '🇮🇳' },
            'bn': { name: 'বাংলা', flag: '🇮🇳' },
            'es': { name: 'Español', flag: '🇪🇸' },
            'fr': { name: 'Français', flag: '🇫🇷' },
            'ar': { name: 'العربية', flag: '🇸🇦' },
            'zh': { name: '中文', flag: '🇨🇳' }
        };
        
        const dropdown = document.createElement('div');
        dropdown.className = 'language-switcher dropdown';
        dropdown.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 1000;
        `;
        
        const currentLang = languages[this.currentLanguage];
        dropdown.innerHTML = `
            <button class="btn btn-outline-light btn-sm dropdown-toggle" type="button" data-bs-toggle="dropdown">
                ${currentLang.flag} ${currentLang.name}
            </button>
            <ul class="dropdown-menu">
                ${Object.entries(languages).map(([code, lang]) => `
                    <li>
                        <a class="dropdown-item ${code === this.currentLanguage ? 'active' : ''}" 
                           href="#" onclick="languageSwitcher.changeLanguage('${code}')">
                            ${lang.flag} ${lang.name}
                        </a>
                    </li>
                `).join('')}
            </ul>
        `;
        
        return dropdown;
    }
    
    setupLanguageSwitcher() {
        // Handle language selection in settings page
        const languageOptions = document.querySelectorAll('.language-option');
        languageOptions.forEach(option => {
            option.addEventListener('click', (e) => {
                const langCode = e.currentTarget.dataset.language;
                if (langCode) {
                    this.changeLanguage(langCode);
                }
            });
        });
    }
    
    changeLanguage(langCode) {
        // Store preference
        localStorage.setItem('preferredLanguage', langCode);
        
        // Send to server
        fetch('/api/set-language', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ language: langCode })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Reload page to apply new language
                window.location.reload();
            } else {
                console.error('Failed to change language:', data.message);
            }
        })
        .catch(error => {
            console.error('Error changing language:', error);
        });
    }
    
    // Method to translate text dynamically (for AJAX content)
    async translateText(key, langCode = null) {
        try {
            const lang = langCode || this.currentLanguage;
            const response = await fetch(`/api/translations/${lang}`);
            const translations = await response.json();
            return translations[key] || key.replace('_', ' ').split(' ').map(word => 
                word.charAt(0).toUpperCase() + word.slice(1)
            ).join(' ');
        } catch (error) {
            console.error('Translation error:', error);
            return key;
        }
    }
}

// Initialize language switcher
const languageSwitcher = new LanguageSwitcher();

// Utility function for dynamic content translation
async function t(key, langCode = null) {
    return await languageSwitcher.translateText(key, langCode);
}
