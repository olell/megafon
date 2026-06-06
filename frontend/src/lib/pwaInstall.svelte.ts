// PWA install affordance.
//
// Chromium (Android / desktop Chrome, Edge, …) fires `beforeinstallprompt`,
// which we capture and replay from an in-app button → near one-tap install.
// iOS Safari supports no programmatic install at all, so there we just flag
// that a manual "Add to Home Screen" hint should be shown instead.

interface BeforeInstallPromptEvent extends Event {
	prompt: () => Promise<void>;
	userChoice: Promise<{ outcome: 'accepted' | 'dismissed' }>;
}

let deferred: BeforeInstallPromptEvent | null = null;

export const install = $state<{
	/** Chromium gave us a deferred prompt we can trigger. */
	canPrompt: boolean;
	/** iOS Safari tab — only a manual Home-Screen hint is possible. */
	iosHint: boolean;
	/** Already running as an installed/standalone app. */
	installed: boolean;
}>({ canPrompt: false, iosHint: false, installed: false });

const isIos = () =>
	/ip(hone|ad|od)/i.test(navigator.userAgent) ||
	// iPadOS reports as "MacIntel" but is touch-capable.
	(navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1);

const isStandalone = () =>
	window.matchMedia?.('(display-mode: standalone)').matches ||
	(navigator as unknown as { standalone?: boolean }).standalone === true;

export const initInstall = () => {
	if (typeof window === 'undefined') return;

	install.installed = isStandalone();
	if (install.installed) return;

	// iOS can't prompt programmatically — offer the manual hint up front.
	if (isIos()) install.iosHint = true;

	window.addEventListener('beforeinstallprompt', (e) => {
		e.preventDefault();
		deferred = e as BeforeInstallPromptEvent;
		install.canPrompt = true;
		install.iosHint = false; // a real prompt beats the manual hint
	});

	window.addEventListener('appinstalled', () => {
		install.installed = true;
		install.canPrompt = false;
		install.iosHint = false;
		deferred = null;
	});
};

export const promptInstall = async () => {
	if (!deferred) return;
	await deferred.prompt();
	await deferred.userChoice;
	// A prompt can only be used once.
	deferred = null;
	install.canPrompt = false;
};
