/**
 * GPToutfit — Calendar Sync Module (FR-44 + FR-49 Demo Mode)
 * Connects to Google Calendar or Microsoft Outlook via OAuth.
 * FR-49: Demo mode with hardcoded events for users without OAuth.
 * Calendar token stored in sessionStorage only (never localStorage).
 */
const Calendar = (() => {
    let _events = [];
    let _connected = false;
    let _isDemoMode = false;

    function getTokenKey() {
        const user = Auth.getCurrentUser();
        return user ? `calendar_token_${user}` : null;
    }

    function getEventsKey() {
        const user = Auth.getCurrentUser();
        return user ? `calendar_events_${user}` : null;
    }

    function getToken() {
        const key = getTokenKey();
        return key ? sessionStorage.getItem(key) : null;
    }

    function setToken(token) {
        const key = getTokenKey();
        if (key) sessionStorage.setItem(key, token);
    }

    function clearToken() {
        const key = getTokenKey();
        if (key) sessionStorage.removeItem(key);
        const ek = getEventsKey();
        if (ek) sessionStorage.removeItem(ek);
        _events = [];
        _connected = false;
        _isDemoMode = false;
    }

    function isConnected() {
        return _connected || _isDemoMode || !!getToken();
    }

    function isDemoMode() {
        return _isDemoMode;
    }

    /** Start OAuth flow for the given provider. */
    function connectCalendar(provider) {
        if (!Auth.isLoggedIn()) return;
        const url = provider === "outlook"
            ? "/wardrobe/calendar/auth/outlook"
            : "/wardrobe/calendar/auth/google";
        window.location.href = url;
    }

    /** After OAuth callback, extract token from URL and sync. */
    async function handleCallback() {
        const params = new URLSearchParams(window.location.search);
        const token = params.get("calendar_token");
        const provider = params.get("calendar_provider");
        if (token && Auth.isLoggedIn()) {
            setToken(token);
            // Clean URL
            const url = new URL(window.location);
            url.searchParams.delete("calendar_token");
            url.searchParams.delete("calendar_provider");
            window.history.replaceState({}, "", url.pathname);
            await loadEvents(provider || "google");
        }
    }

    /** Load demo events from backend (FR-49). */
    async function loadDemoEvents() {
        const user = Auth.getCurrentUser();
        if (!user) return [];

        try {
            const res = await fetch("/wardrobe/calendar/demo", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ username: user })
            });

            if (!res.ok) return [];
            const data = await res.json();
            _events = data.events || [];
            _isDemoMode = data.demo === true;
            _connected = _events.length > 0;

            // Cache in sessionStorage
            const ek = getEventsKey();
            if (ek) sessionStorage.setItem(ek, JSON.stringify(_events));

            return _events;
        } catch (err) {
            console.error("Demo calendar error:", err);
            return [];
        }
    }

    /** Fetch events from backend using stored token. */
    async function loadEvents(provider) {
        const token = getToken();
        if (!token) return [];

        try {
            const res = await fetch("/wardrobe/calendar/sync", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    provider: provider || "google",
                    access_token: token,
                    days_ahead: 30
                })
            });

            if (res.status === 401) {
                _connected = false;
                return [];
            }

            if (!res.ok) throw new Error("Calendar sync failed");

            const data = await res.json();
            _events = data.events || [];
            _connected = true;

            const ek = getEventsKey();
            if (ek) sessionStorage.setItem(ek, JSON.stringify(_events));

            return _events;
        } catch (err) {
            console.error("Calendar sync error:", err);
            return [];
        }
    }

    /** Get cached events (from memory or sessionStorage). */
    function getEvents() {
        if (_events.length > 0) return _events;
        const ek = getEventsKey();
        if (ek) {
            try {
                _events = JSON.parse(sessionStorage.getItem(ek)) || [];
                if (_events.length > 0) _connected = true;
            } catch { _events = []; }
        }
        return _events;
    }

    /** Update a single event in the list (for Edit Event modal). */
    function updateEvent(eventId, updates) {
        const idx = _events.findIndex(e => e.id === eventId);
        if (idx >= 0) {
            Object.assign(_events[idx], updates);
            const ek = getEventsKey();
            if (ek) sessionStorage.setItem(ek, JSON.stringify(_events));
        }
    }

    /** Get events within the next N days. */
    function getUpcomingEvents(days) {
        const now = new Date();
        const cutoff = new Date(now.getTime() + days * 86400000);
        return getEvents().filter(e => {
            const d = new Date(e.date);
            return d >= now && d <= cutoff;
        });
    }

    /** Call /wardrobe/discover with the event's occasion_hint. */
    async function getOutfitForEvent(event) {
        const gender = Auth.getUserGender() || "Men";
        const profile = JSON.parse(sessionStorage.getItem("wardrobe_profile") || "{}");
        const styleVibe = profile.style_vibe || "Smart Casual";

        const res = await fetch("/wardrobe/discover", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                occasion: event.occasion_hint || event.title,
                gender: gender,
                style_vibe: styleVibe,
                top_k: 20
            })
        });

        if (!res.ok) throw new Error("Failed to get outfit ideas");
        return res.json();
    }

    return {
        connectCalendar, handleCallback, loadEvents, loadDemoEvents,
        getEvents, getUpcomingEvents, getOutfitForEvent,
        isConnected, isDemoMode, clearToken, getToken, updateEvent
    };
})();
