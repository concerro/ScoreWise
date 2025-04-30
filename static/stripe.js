// stripe.js: Handles Stripe Checkout redirection on upload

const stripe = Stripe('pk_test_51R7cMOQCSwJNKq1cKk2n7c5v4lQ6J0Z6r8n3y5n8w5v6p4x3j2l1k0h9g8f7e6d5c4b3a2s1d0f9g8h7j6k5l4m3n2b1v0'); // Replace with your Stripe test publishable key

document.addEventListener('DOMContentLoaded', function() {
    const uploadForm = document.getElementById('upload-form');
    if (!uploadForm) return;

    uploadForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        const formData = new FormData(uploadForm);
        // Optionally: Validate file before proceeding
        const response = await fetch('/create-checkout-session', {
            method: 'POST',
            headers: { 'Accept': 'application/json' },
            body: formData
        });
        const data = await response.json();
        if (data.url) {
            window.location.href = data.url;
        } else {
            alert('Error creating Stripe Checkout session: ' + (data.error || 'Unknown error'));
        }
    });
});
