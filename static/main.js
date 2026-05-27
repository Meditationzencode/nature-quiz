// Progressive enhancement: once a form is submitted, disable its submit
// controls so a slow response can't be double-posted, and signal that
// something is happening. The server remains the source of truth for
// validation and duplicate-submission guards.
document.addEventListener("submit", (event) => {
    const controls = event.target.querySelectorAll(
        "button[type='submit'], button:not([type])"
    );
    controls.forEach((button) => {
        button.setAttribute("aria-busy", "true");
        // Defer disabling so the clicked button's name/value is still
        // included in this submission, then lock the form.
        setTimeout(() => {
            button.disabled = true;
        }, 0);
    });
});
