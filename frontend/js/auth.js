/**
 * GPToutfit — Authentication Module (FR-43)
 * Demo mode: hardcoded credentials, no backend auth.
 * Guest enters without friction. Javier/Laura persist wardrobe in localStorage.
 */
const Auth = (() => {
    const VALID_USERS = {
        javier: { password: "javier", name: "Javier", gender: "Men" },
        laura:  { password: "laura",  name: "Laura",  gender: "Women" }
    };

    const SESSION_KEY = "gptoutfit_auth_user";

    function login(username, password) {
        const key = username.trim().toLowerCase();
        const user = VALID_USERS[key];
        if (!user || user.password !== password) {
            return { success: false, error: "Invalid credentials" };
        }
        sessionStorage.setItem(SESSION_KEY, key);
        // Load persisted wardrobe for this user
        const saved = localStorage.getItem(`wardrobe_basket_${key}`);
        if (saved) {
            sessionStorage.setItem("wardrobe_basket", saved);
        }
        return { success: true, user: key, name: user.name };
    }

    function logout() {
        const user = getCurrentUser();
        if (user) {
            // Persist wardrobe before clearing
            const basket = sessionStorage.getItem("wardrobe_basket");
            if (basket) {
                localStorage.setItem(`wardrobe_basket_${user}`, basket);
            }
            // Clear calendar token
            sessionStorage.removeItem(`calendar_token_${user}`);
            sessionStorage.removeItem(`calendar_events_${user}`);
        }
        sessionStorage.removeItem(SESSION_KEY);
        sessionStorage.removeItem("wardrobe_basket");
        sessionStorage.removeItem("active_profile");
        sessionStorage.removeItem("wardrobe_profile");
        sessionStorage.removeItem("survey_completed");
    }

    function getCurrentUser() {
        return sessionStorage.getItem(SESSION_KEY) || null;
    }

    function isLoggedIn() {
        return getCurrentUser() !== null;
    }

    function getUserDisplayName() {
        const user = getCurrentUser();
        return user ? VALID_USERS[user]?.name || user : null;
    }

    function getUserGender() {
        const user = getCurrentUser();
        return user ? VALID_USERS[user]?.gender || "Men" : null;
    }

    /** Persist wardrobe for logged-in user (call on every basket change). */
    function persistWardrobe(basketJson) {
        const user = getCurrentUser();
        if (user) {
            localStorage.setItem(`wardrobe_basket_${user}`, basketJson);
        }
    }

    return { login, logout, getCurrentUser, isLoggedIn, getUserDisplayName, getUserGender, persistWardrobe };
})();
