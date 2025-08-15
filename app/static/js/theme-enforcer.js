/**
 * Theme Enforcer Script
 * Aggressively enforces theme consistency across all plugin WebUIs
 * This script runs continuously to ensure no plugin can override the global theme
 */

(function() {
    'use strict';

    const ThemeEnforcer = {
        // Configuration
        config: {
            enforceInterval: 1000, // Check every second
            maxAttempts: 50, // Stop after 50 attempts (50 seconds)
            debugMode: false
        },

        // Tracking
        attempts: 0,
        isEnforcing: false,

        // Initialize the enforcer
        init() {
            this.log('Theme Enforcer initializing...');

            // Start enforcement immediately
            this.enforce();

            // Set up continuous enforcement
            this.startContinuousEnforcement();

            // Listen for theme changes
            this.setupThemeListener();

            // Handle page navigation
            this.setupNavigationListener();

            this.log('Theme Enforcer initialized');
        },

        // Main enforcement function
        enforce() {
            if (this.isEnforcing) return;
            this.isEnforcing = true;

            try {
                this.log('Enforcing theme consistency...');

                // 1. Ensure theme attribute is set
                this.ensureThemeAttribute();

                // 2. Fix sidebar issues
                this.fixSidebar();

                // 3. Fix navigation issues
                this.fixNavigation();

                // 4. Fix table issues
                this.fixTables();

                // 5. Fix card issues
                this.fixCards();

                // 6. Fix form issues
                this.fixForms();

                // 7. Fix text color issues
                this.fixTextColors();

                // 8. Remove conflicting inline styles
                this.removeConflictingStyles();

                this.log('Theme enforcement complete');

            } catch (error) {
                this.log('Error during theme enforcement:', error);
            } finally {
                this.isEnforcing = false;
            }
        },

        // Ensure theme attribute is properly set
        ensureThemeAttribute() {
            if (!document.documentElement.getAttribute('data-theme')) {
                const savedTheme = localStorage.getItem('theme');
                const systemPrefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
                const theme = savedTheme || (systemPrefersDark ? 'dark' : 'light');

                document.documentElement.setAttribute('data-theme', theme);
                this.log(`Set theme attribute to: ${theme}`);
            }
        },

        // Fix sidebar styling issues
        fixSidebar() {
            const sidebarSelectors = [
                '.sidebar',
                'nav.sidebar',
                '.col-md-3.sidebar',
                '.col-lg-2.sidebar',
                'nav.col-md-3',
                'nav.col-lg-2'
            ];

            sidebarSelectors.forEach(selector => {
                const elements = document.querySelectorAll(selector);
                elements.forEach(element => {
                    // Remove any hardcoded background styles
                    element.style.removeProperty('background-color');
                    element.style.removeProperty('background');
                    element.style.removeProperty('border-right-color');
                    element.style.removeProperty('border-right');
                    element.style.removeProperty('color');

                    // Add theme classes
                    element.classList.add('sidebar-themed');
                });
            });

            // Fix sidebar links
            const linkSelectors = [
                '.sidebar .nav-link',
                '.sidebar a.nav-link',
                'nav.sidebar .nav-link',
                'nav.sidebar a.nav-link'
            ];

            linkSelectors.forEach(selector => {
                const links = document.querySelectorAll(selector);
                links.forEach(link => {
                    link.style.removeProperty('background-color');
                    link.style.removeProperty('background');
                    link.style.removeProperty('color');
                    link.classList.add('sidebar-link-themed');
                });
            });
        },

        // Fix navigation issues
        fixNavigation() {
            const navbars = document.querySelectorAll('.navbar, nav.navbar');
            navbars.forEach(navbar => {
                navbar.style.removeProperty('background-color');
                navbar.style.removeProperty('background');
                navbar.classList.add('navbar-themed');
            });

            const navLinks = document.querySelectorAll('.navbar .nav-link, .navbar a.nav-link');
            navLinks.forEach(link => {
                link.style.removeProperty('color');
                link.classList.add('navbar-link-themed');
            });
        },

        // Fix table issues
        fixTables() {
            const tables = document.querySelectorAll('.table');
            tables.forEach(table => {
                table.style.removeProperty('background-color');
                table.style.removeProperty('background');
                table.style.removeProperty('color');
                table.classList.add('table-themed');

                // Fix table rows
                const rows = table.querySelectorAll('tr');
                rows.forEach(row => {
                    row.style.removeProperty('background-color');
                    row.style.removeProperty('background');
                    row.style.removeProperty('color');
                });

                // Fix table cells
                const cells = table.querySelectorAll('td, th');
                cells.forEach(cell => {
                    cell.style.removeProperty('background-color');
                    cell.style.removeProperty('background');
                    cell.style.removeProperty('color');
                });
            });
        },

        // Fix card issues
        fixCards() {
            const cards = document.querySelectorAll('.card');
            cards.forEach(card => {
                card.style.removeProperty('background-color');
                card.style.removeProperty('background');
                card.style.removeProperty('border-color');
                card.style.removeProperty('color');
                card.classList.add('card-themed');

                // Fix card headers and bodies
                const cardParts = card.querySelectorAll('.card-header, .card-body, .card-footer');
                cardParts.forEach(part => {
                    part.style.removeProperty('background-color');
                    part.style.removeProperty('background');
                    part.style.removeProperty('color');
                });
            });
        },

        // Fix form issues
        fixForms() {
            const formElements = document.querySelectorAll('.form-control, .form-select, input, select, textarea');
            formElements.forEach(element => {
                element.style.removeProperty('background-color');
                element.style.removeProperty('background');
                element.style.removeProperty('border-color');
                element.style.removeProperty('color');
                element.classList.add('form-themed');
            });

            const labels = document.querySelectorAll('.form-label, label');
            labels.forEach(label => {
                label.style.removeProperty('color');
                label.classList.add('label-themed');
            });
        },

        // Fix text color issues
        fixTextColors() {
            // Find elements with hardcoded text colors that aren't part of status indicators
            const textElements = document.querySelectorAll('h1, h2, h3, h4, h5, h6, p, span, div');
            textElements.forEach(element => {
                // Skip elements that should keep their colors (badges, buttons, etc.)
                if (element.classList.contains('badge') ||
                    element.classList.contains('btn') ||
                    element.classList.contains('alert') ||
                    element.classList.contains('text-success') ||
                    element.classList.contains('text-danger') ||
                    element.classList.contains('text-warning') ||
                    element.classList.contains('text-info') ||
                    element.closest('.status-indicator') ||
                    element.closest('.progress-bar')) {
                    return;
                }

                // Remove hardcoded colors
                if (element.style.color &&
                    (element.style.color.includes('#') || element.style.color.includes('rgb'))) {
                    element.style.removeProperty('color');
                    element.classList.add('text-themed');
                }
            });
        },

        // Remove conflicting inline styles
        removeConflictingStyles() {
            const elementsWithStyles = document.querySelectorAll('[style]');
            elementsWithStyles.forEach(element => {
                const style = element.getAttribute('style');

                // Remove problematic background colors
                if (style.includes('background-color: #f8f9fa') ||
                    style.includes('background-color: #343a40') ||
                    style.includes('background-color: white') ||
                    style.includes('background-color: black') ||
                    style.includes('background: #f8f9fa') ||
                    style.includes('background: #343a40')) {

                    element.style.removeProperty('background-color');
                    element.style.removeProperty('background');
                    this.log('Removed conflicting background style from element:', element);
                }

                // Remove problematic text colors
                if (style.includes('color: #333') ||
                    style.includes('color: #666') ||
                    style.includes('color: #999') ||
                    style.includes('color: white') ||
                    style.includes('color: black')) {

                    element.style.removeProperty('color');
                    this.log('Removed conflicting text color from element:', element);
                }
            });
        },

        // Start continuous enforcement
        startContinuousEnforcement() {
            const enforceInterval = setInterval(() => {
                this.attempts++;

                if (this.attempts > this.config.maxAttempts) {
                    clearInterval(enforceInterval);
                    this.log('Theme enforcement stopped after maximum attempts');
                    return;
                }

                this.enforce();
            }, this.config.enforceInterval);
        },

        // Set up theme change listener
        setupThemeListener() {
            const observer = new MutationObserver((mutations) => {
                mutations.forEach((mutation) => {
                    if (mutation.type === 'attributes' &&
                        mutation.attributeName === 'data-theme') {
                        this.log('Theme changed, re-enforcing...');
                        setTimeout(() => this.enforce(), 100);
                    }
                });
            });

            observer.observe(document.documentElement, {
                attributes: true,
                attributeFilter: ['data-theme']
            });
        },

        // Set up navigation listener for SPA-like behavior
        setupNavigationListener() {
            // Listen for hash changes
            window.addEventListener('hashchange', () => {
                setTimeout(() => this.enforce(), 200);
            });

            // Listen for popstate (back/forward navigation)
            window.addEventListener('popstate', () => {
                setTimeout(() => this.enforce(), 200);
            });

            // Monitor for AJAX content changes
            const contentObserver = new MutationObserver(() => {
                setTimeout(() => this.enforce(), 300);
            });

            const mainContent = document.querySelector('.main-content, main');
            if (mainContent) {
                contentObserver.observe(mainContent, {
                    childList: true,
                    subtree: true
                });
            }
        },

        // Logging utility
        log(message, ...args) {
            if (this.config.debugMode) {
                console.log(`[ThemeEnforcer] ${message}`, ...args);
            }
        },

        // Public method to force immediate enforcement
        forceEnforce() {
            this.log('Force enforcement requested');
            this.enforce();
        },

        // Public method to enable debug mode
        enableDebug() {
            this.config.debugMode = true;
            this.log('Debug mode enabled');
        },

        // Public method to disable debug mode
        disableDebug() {
            this.config.debugMode = false;
        }
    };

    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            ThemeEnforcer.init();
        });
    } else {
        ThemeEnforcer.init();
    }

    // Also run on window load as backup
    window.addEventListener('load', () => {
        setTimeout(() => ThemeEnforcer.forceEnforce(), 500);
    });

    // Export for global access
    window.ThemeEnforcer = ThemeEnforcer;

    // Emergency fallback - run enforcement every 5 seconds for the first minute
    let emergencyAttempts = 0;
    const emergencyInterval = setInterval(() => {
        ThemeEnforcer.forceEnforce();
        emergencyAttempts++;

        if (emergencyAttempts >= 12) { // 12 * 5 seconds = 1 minute
            clearInterval(emergencyInterval);
        }
    }, 5000);

})();
