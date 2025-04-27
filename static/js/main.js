// Flash message auto-hide
document.addEventListener('DOMContentLoaded', function() {
    const flashMessages = document.querySelectorAll('.flash-message');
    flashMessages.forEach(message => {
        setTimeout(() => {
            message.style.opacity = '0';
            setTimeout(() => {
                message.remove();
            }, 300);
        }, 3000);
    });

    // Price calculation for booking form
    const bookingForm = document.querySelector('#booking-form');
    if (bookingForm) {
        const startDate = document.querySelector('#start_date');
        const endDate = document.querySelector('#end_date');
        const pricePerDay = parseFloat(document.querySelector('#price_per_day').value);
        const totalPriceDisplay = document.querySelector('#total_price');

        function calculateTotalPrice() {
            if (startDate.value && endDate.value) {
                const start = new Date(startDate.value);
                const end = new Date(endDate.value);
                const days = Math.ceil((end - start) / (1000 * 60 * 60 * 24)) + 1;
                const totalPrice = days * pricePerDay;
                totalPriceDisplay.textContent = `$${totalPrice.toFixed(2)}`;
            }
        }

        startDate.addEventListener('change', calculateTotalPrice);
        endDate.addEventListener('change', calculateTotalPrice);
    }

    // Car search functionality
    const searchForm = document.querySelector('#search-form');
    if (searchForm) {
        searchForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const searchTerm = document.querySelector('#search-input').value.toLowerCase();
            const carCards = document.querySelectorAll('.car-card');

            carCards.forEach(card => {
                const title = card.querySelector('.car-title').textContent.toLowerCase();
                const price = card.querySelector('.car-price').textContent.toLowerCase();
                
                if (title.includes(searchTerm) || price.includes(searchTerm)) {
                    card.style.display = 'block';
                } else {
                    card.style.display = 'none';
                }
            });
        });
    }

    // Star rating system
    const ratingInputs = document.querySelectorAll('.rating-input');
    ratingInputs.forEach(input => {
        input.addEventListener('change', function() {
            const stars = this.parentElement.querySelectorAll('.star');
            const rating = this.value;
            
            stars.forEach((star, index) => {
                if (index < rating) {
                    star.classList.add('active');
                } else {
                    star.classList.remove('active');
                }
            });
        });
    });

    // Price calculation for car details page
    const startDateInput = document.getElementById('start_date');
    const endDateInput = document.getElementById('end_date');
    const totalPriceSpan = document.getElementById('total-price');
    const pricePerDay = parseFloat(document.querySelector('.car-price h2').textContent.replace('$', '').replace('/day', ''));

    if (startDateInput && endDateInput && totalPriceSpan) {
        function calculatePrice() {
            const startDate = new Date(startDateInput.value);
            const endDate = new Date(endDateInput.value);
            const days = Math.max(1, (endDate - startDate) / (1000 * 60 * 60 * 24) + 1);
            const totalPrice = days * pricePerDay;
            totalPriceSpan.textContent = `$${totalPrice.toFixed(2)}`;
        }

        startDateInput.addEventListener('change', calculatePrice);
        endDateInput.addEventListener('change', calculatePrice);
    }
}); 