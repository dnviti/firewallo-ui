/**
 * Plugin Theme Initialization Script
 * This script ensures all plugin WebUIs properly initialize and maintain theme consistency
 * Include this script in any plugin WebUI that needs theme support
 */

(function() {
    'use strict';

    // Theme initialization for plugins
    const PluginTheme = {
        init() {
            // Ensure theme is initialized even if main theme system isn't loaded
            if (typeof theme === 'undefined') {
                this.createFallbackThemeSystem();
            }

            // Force theme application on plugin load
            this.applyTheme();

            // Set up theme persistence
            this.setupThemePersistence();

            // Initialize theme toggle if present
            this.initializeThemeToggle();

            // Apply plugin-specific theme fixes
            this.applyPluginFixes();
        },

        createFallbackThemeSystem() {
            window.theme = {
                init() {
                    const savedTheme = localStorage.getItem('theme');
                    if (savedTheme) {
                        this.set(savedTheme);
                    } else if (window.matchMedia('(prefers-color-scheme: dark)').matches) {
                        this.set('dark');
                    } else {
                        this.set('light');
                    }
                },

                set(themeName) {
                    document.documentElement.setAttribute('data-theme', themeName);
                    localStorage.setItem('theme', themeName);
                    this.updateComponents();
                },

                toggle() {
                    const current = document.documentElement.getAttribute('data-theme');
                    this.set(current === 'dark' ? 'light' : 'dark');
                },

                get() {
                    return document.documentElement.getAttribute('data-theme') || 'light';
                },

                updateComponents() {
                    // Force update any components that might not be responding to CSS variables
                    const event = new CustomEvent('themeChanged', {
                        detail: { theme: this.get() }
                    });
                    document.dispatchEvent(event);
                }
            };

            // Initialize the fallback theme system
            window.theme.init();
        },

        applyTheme() {
            // Get current theme or detect from system
            let currentTheme = document.documentElement.getAttribute('data-theme');

            if (!currentTheme) {
                const savedTheme = localStorage.getItem('theme');
                if (savedTheme) {
                    currentTheme = savedTheme;
                } else {
                    currentTheme = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
                }
                document.documentElement.setAttribute('data-theme', currentTheme);
            }

            // Force apply theme to body and html
            document.body.classList.remove('theme-light', 'theme-dark');
            document.body.classList.add(`theme-${currentTheme}`);
        },

        setupThemePersistence() {
            // Listen for theme changes from other tabs/windows
            window.addEventListener('storage', (e) => {
                if (e.key === 'theme' && e.newValue) {
                    document.documentElement.setAttribute('data-theme', e.newValue);
                    this.applyTheme();
                    this.updateThemeToggleIcon();
                }
            });

            // Listen for system theme preference changes
            window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
                const savedTheme = localStorage.getItem('theme');
                if (!savedTheme) {
                    const newTheme = e.matches ? 'dark' : 'light';
                    document.documentElement.setAttribute('data-theme', newTheme);
                    this.applyTheme();
                    this.updateThemeToggleIcon();
                }
            });
        },

        initializeThemeToggle() {
            const themeToggle = document.getElementById('theme-toggle');
            const themeIcon = document.getElementById('theme-icon');

            if (themeToggle && themeIcon) {
                // Update icon based on current theme
                this.updateThemeToggleIcon();

                // Handle theme toggle clicks
                themeToggle.addEventListener('click', (e) => {
                    e.preventDefault();

                    if (typeof theme !== 'undefined') {
                        theme.toggle();
                    } else {
                        const currentTheme = document.documentElement.getAttribute('data-theme');
                        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
                        document.documentElement.setAttribute('data-theme', newTheme);
                        localStorage.setItem('theme', newTheme);
                    }

                    this.updateThemeToggleIcon();
                    this.animateThemeToggle();
                });
            }
        },

        updateThemeToggleIcon() {
            const themeIcon = document.getElementById('theme-icon');
            const themeToggle = document.getElementById('theme-toggle');

            if (themeIcon && themeToggle) {
                const currentTheme = document.documentElement.getAttribute('data-theme');
                if (currentTheme === 'dark') {
                    themeIcon.className = 'bi bi-sun';
                    themeToggle.title = 'Switch to light theme';
                } else {
                    themeIcon.className = 'bi bi-moon';
                    themeToggle.title = 'Switch to dark theme';
                }
            }
        },

        animateThemeToggle() {
            const themeIcon = document.getElementById('theme-icon');
            if (themeIcon) {
                themeIcon.style.transform = 'rotate(180deg)';
                setTimeout(() => {
                    themeIcon.style.transform = 'rotate(0deg)';
                }, 300);
            }
        },

        applyPluginFixes() {
            // Fix any elements that might have hardcoded styles
            this.fixHardcodedElements();

            // Apply theme to dynamically loaded content
            this.setupDynamicContentTheme();

            // Fix plugin-specific components
            this.fixPluginComponents();
        },

        fixHardcodedElements() {
            // Remove any hardcoded style attributes that conflict with theme
            const elementsWithHardcodedBg = document.querySelectorAll('[style*="background-color"]');
            elementsWithHardcodedBg.forEach(el => {
                // Only remove if it's a basic color, not gradients or images
                const bgColor = el.style.backgroundColor;
                if (bgColor && (bgColor.includes('rgb') || bgColor.includes('#'))) {
                    el.style.backgroundColor = '';
                    el.classList.add('bg-surface');
                }
            });

            const elementsWithHardcodedColor = document.querySelectorAll('[style*="color"]');
            elementsWithHardcodedColor.forEach(el => {
                const color = el.style.color;
                if (color && (color.includes('rgb') || color.includes('#'))) {
                    el.style.color = '';
                    el.classList.add('text-primary-custom');
                }
            });
        },

        setupDynamicContentTheme() {
            // Watch for dynamically added content and apply theme
            if (typeof MutationObserver !== 'undefined') {
                const observer = new MutationObserver((mutations) => {
                    mutations.forEach((mutation) => {
                        if (mutation.type === 'childList') {
                            mutation.addedNodes.forEach((node) => {
                                if (node.nodeType === 1) { // Element node
                                    this.applyThemeToElement(node);
                                }
                            });
                        }
                    });
                });

                observer.observe(document.body, {
                    childList: true,
                    subtree: true
                });
            }
        },

        applyThemeToElement(element) {
            // Apply theme classes to new elements
            if (element.classList) {
                // Cards
                if (element.classList.contains('card') || element.tagName === 'DIV' && element.className.includes('card')) {
                    element.style.backgroundColor = '';
                    element.style.borderColor = '';
                    element.style.color = '';
                }

                // Tables
                if (element.classList.contains('table') || element.tagName === 'TABLE') {
                    element.style.backgroundColor = '';
                    element.style.color = '';
                }

                // Forms
                if (element.classList.contains('form-control') || element.classList.contains('form-select')) {
                    element.style.backgroundColor = '';
                    element.style.borderColor = '';
                    element.style.color = '';
                }
            }

            // Apply to child elements as well
            const childElements = element.querySelectorAll('*');
            childElements.forEach(child => {
                if (child.style && (child.style.backgroundColor || child.style.color)) {
                    // Only clear basic colors, preserve gradients and special styling
                    if (child.style.backgroundColor &&
                        !child.style.backgroundColor.includes('gradient') &&
                        !child.style.backgroundColor.includes('linear') &&
                        !child.style.backgroundColor.includes('radial')) {
                        child.style.backgroundColor = '';
                    }

                    if (child.style.color &&
                        !child.classList.contains('text-success') &&
                        !child.classList.contains('text-danger') &&
                        !child.classList.contains('text-warning') &&
                        !child.classList.contains('text-info')) {
                        child.style.color = '';
                    }
                }
            });
        },

        fixPluginComponents() {
            // Fix any known plugin-specific components
            setTimeout(() => {
                // WireGuard specific fixes
                const wireguardElements = document.querySelectorAll('.wg-server, .wg-client, .wg-config');
                wireguardElements.forEach(el => {
                    el.style.backgroundColor = '';
                    el.style.color = '';
                });

                // Generic plugin element fixes
                const pluginElements = document.querySelectorAll('[class*="plugin-"], [class*="wg-"], [class*="vpn-"]');
                pluginElements.forEach(el => {
                    if (el.style.backgroundColor &&
                        (el.style.backgroundColor.includes('#f8f9fa') ||
                         el.style.backgroundColor.includes('#343a40') ||
                         el.style.backgroundColor.includes('white') ||
                         el.style.backgroundColor.includes('black'))) {
                        el.style.backgroundColor = '';
                    }
                });
            }, 100);
        },

        // Utility method to force theme re-application
        forceThemeUpdate() {
            const currentTheme = document.documentElement.getAttribute('data-theme') || 'light';
            document.documentElement.removeAttribute('data-theme');
            setTimeout(() => {
                document.documentElement.setAttribute('data-theme', currentTheme);
                this.applyTheme();
            }, 10);
        }
    };

    // Initialize immediately if DOM is ready, otherwise wait
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            PluginTheme.init();
        });
    } else {
        PluginTheme.init();
    }

    // Also initialize on window load as a backup
    window.addEventListener('load', () => {
        PluginTheme.forceThemeUpdate();
    });

    // Export for global access
    window.PluginTheme = PluginTheme;

    // Auto-fix common theme issues every 2 seconds (only for the first 10 seconds after load)
    let fixAttempts = 0;
    const maxFixes = 5;
    const fixInterval = setInterval(() => {
        PluginTheme.applyPluginFixes();
        fixAttempts++;

        if (fixAttempts >= maxFixes) {
            clearInterval(fixInterval);
        }
    }, 2000);

})();
