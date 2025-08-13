
import { useState, useEffect } from 'react'
import { Button } from '../ui/button'
import { Card, CardContent } from '../ui/card'
import { api } from '../../lib/api'
import { useAuthStore } from '../../lib/stores/auth'

interface ConsentPreferences {
  essential: boolean
  analytics: boolean
  marketing: boolean
}

export function ConsentBanner() {
  const [showBanner, setShowBanner] = useState(false)
  const [showPreferences, setShowPreferences] = useState(false)
  const [preferences, setPreferences] = useState<ConsentPreferences>({
    essential: true, // Always required
    analytics: false,
    marketing: false
  })
  const { isAuthenticated } = useAuthStore()

  useEffect(() => {
    // Check if user has already provided consent
    const hasConsent = localStorage.getItem('furrbutler-consent')
    if (!hasConsent) {
      setShowBanner(true)
    }
  }, [])

  const handleAcceptAll = async () => {
    const newPreferences = {
      essential: true,
      analytics: true,
      marketing: true
    }
    await saveConsent(newPreferences)
  }

  const handleRejectAll = async () => {
    const newPreferences = {
      essential: true,
      analytics: false,
      marketing: false
    }
    await saveConsent(newPreferences)
  }

  const handleSavePreferences = async () => {
    await saveConsent(preferences)
  }

  const saveConsent = async (prefs: ConsentPreferences) => {
    try {
      // Save consent to backend if user is authenticated
      if (isAuthenticated) {
        await Promise.all([
          api.consent.updateConsent('essential', prefs.essential),
          api.consent.updateConsent('analytics', prefs.analytics),
          api.consent.updateConsent('marketing', prefs.marketing)
        ])
      }
      
      // Save consent locally
      localStorage.setItem('furrbutler-consent', JSON.stringify(prefs))
      
      // Initialize analytics if consented
      if (prefs.analytics) {
        initializeAnalytics()
      }
      
      setShowBanner(false)
      setShowPreferences(false)
    } catch (error) {
      console.error('Failed to save consent:', error)
    }
  }

  const initializeAnalytics = () => {
    // Initialize Google Analytics, Mixpanel, etc. only after consent
    const gaId = import.meta.env.VITE_GOOGLE_ANALYTICS_ID
    if (gaId && typeof gtag !== 'undefined') {
      gtag('config', gaId)
    }
  }

  if (!showBanner) {
    return null
  }

  return (
    <div className="fixed bottom-0 left-0 right-0 z-50 p-4 bg-background/95 backdrop-blur border-t">
      <Card className="max-w-4xl mx-auto">
        <CardContent className="p-6">
          {!showPreferences ? (
            // Initial consent banner
            <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
              <div className="flex-1">
                <h3 className="font-semibold mb-2">🍪 We value your privacy</h3>
                <p className="text-sm text-muted-foreground">
                  We use cookies and similar technologies to provide essential services, 
                  analyze site usage, and improve your experience. You can manage your 
                  preferences at any time.
                </p>
              </div>
              <div className="flex gap-2 flex-wrap">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setShowPreferences(true)}
                >
                  Manage Preferences
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleRejectAll}
                >
                  Reject All
                </Button>
                <Button
                  size="sm"
                  onClick={handleAcceptAll}
                >
                  Accept All
                </Button>
              </div>
            </div>
          ) : (
            // Detailed preferences
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="font-semibold">Cookie Preferences</h3>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setShowPreferences(false)}
                >
                  ✕
                </Button>
              </div>
              
              <div className="space-y-4">
                {/* Essential cookies */}
                <div className="flex items-center justify-between p-3 border rounded">
                  <div>
                    <h4 className="font-medium">Essential Cookies</h4>
                    <p className="text-sm text-muted-foreground">
                      Required for the website to function properly
                    </p>
                  </div>
                  <div className="text-sm text-muted-foreground">Always On</div>
                </div>
                
                {/* Analytics cookies */}
                <div className="flex items-center justify-between p-3 border rounded">
                  <div>
                    <h4 className="font-medium">Analytics Cookies</h4>
                    <p className="text-sm text-muted-foreground">
                      Help us understand how you use our website
                    </p>
                  </div>
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={preferences.analytics}
                      onChange={(e) => setPreferences(prev => ({
                        ...prev,
                        analytics: e.target.checked
                      }))}
                      className="mr-2"
                    />
                    <span className="text-sm">Enable</span>
                  </label>
                </div>
                
                {/* Marketing cookies */}
                <div className="flex items-center justify-between p-3 border rounded">
                  <div>
                    <h4 className="font-medium">Marketing Cookies</h4>
                    <p className="text-sm text-muted-foreground">
                      Used to deliver personalized advertisements
                    </p>
                  </div>
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={preferences.marketing}
                      onChange={(e) => setPreferences(prev => ({
                        ...prev,
                        marketing: e.target.checked
                      }))}
                      className="mr-2"
                    />
                    <span className="text-sm">Enable</span>
                  </label>
                </div>
              </div>
              
              <div className="flex justify-end gap-2">
                <Button variant="outline" onClick={handleRejectAll}>
                  Reject All
                </Button>
                <Button onClick={handleSavePreferences}>
                  Save Preferences
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
