/**
 * Theme Initialization Script - Include this in all templates AFTER Tailwind
 * This script applies the theme class to the HTML element based on data-theme attribute
 */

function applyTheme() {
  const themeData = document.documentElement.getAttribute('data-theme');
  if (themeData === 'dark') {
    document.documentElement.classList.add('dark');
  } else {
    document.documentElement.classList.remove('dark');
  }
}

// Apply theme immediately on load
applyTheme();

// Also apply on DOMContentLoaded to handle late-loading elements
document.addEventListener('DOMContentLoaded', applyTheme);

// Listen for theme changes (in case it's changed dynamically via AJAX)
const observer = new MutationObserver((mutations) => {
  mutations.forEach((mutation) => {
    if (mutation.attributeName === 'data-theme') {
      applyTheme();
    }
  });
});

observer.observe(document.documentElement, { attributes: true });

// Special handler for form submissions that change theme
document.addEventListener('submit', function(e) {
  const form = e.target;
  if (form.action && form.action.includes('toggle_theme')) {
    // Delay to allow form to process, then reapply theme
    setTimeout(() => {
      applyTheme();
    }, 100);
  }
});
