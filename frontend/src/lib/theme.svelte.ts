// Light/dark theme state, persisted to localStorage and reflected as a `.dark`
// class on <html>. The initial class is set by a no-flash inline script in
// app.html *before* paint; this module just keeps the rune state in sync and
// handles toggling.

const STORAGE_KEY = 'megafon-theme';

export const theme = $state<{ dark: boolean }>({ dark: false });

/** Read the class the no-flash script already applied so the toggle icon matches. */
export const initTheme = () => {
	if (typeof document === 'undefined') return;
	theme.dark = document.documentElement.classList.contains('dark');
};

export const toggleTheme = () => {
	theme.dark = !theme.dark;
	document.documentElement.classList.toggle('dark', theme.dark);
	try {
		localStorage.setItem(STORAGE_KEY, theme.dark ? 'dark' : 'light');
	} catch {
		// ignore storage failures (private mode etc.)
	}
};
