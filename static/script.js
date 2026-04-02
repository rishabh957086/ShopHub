// Add to cart confirmation
document.addEventListener('DOMContentLoaded', function() {
    // Auto-hide alerts after 3 seconds
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 3000);
    });

    // Quantity input validation
    const quantityInputs = document.querySelectorAll('input[type="number"]');
    quantityInputs.forEach(input => {
        input.addEventListener('change', function() {
            if (this.value < 1) this.value = 1;
            if (this.max && this.value > this.max) this.value = this.max;
        });
    });
});

// Add to cart animation
function animateAddToCart(button) {
    button.innerHTML = '<i class="fas fa-check"></i> Added!';
    setTimeout(() => {
        button.innerHTML = '<i class="fas fa-cart-plus"></i> Add to Cart';
    }, 2000);
}