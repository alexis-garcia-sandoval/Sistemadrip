// Auto-dismiss alerts after 4 seconds
document.addEventListener('DOMContentLoaded', () => {
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.style.transition = 'opacity .5s';
            alert.style.opacity = '0';
            setTimeout(() => alert.remove(), 500);
        }, 4000);
    });

    // Confirm delete/remove actions
    document.querySelectorAll('[data-confirm]').forEach(el => {
        el.addEventListener('click', e => {
            if (!confirm(el.dataset.confirm)) e.preventDefault();
        });
    });

    // Quantity input: prevent values below 1
    document.querySelectorAll('.qty-input').forEach(input => {
        input.addEventListener('change', () => {
            if (parseInt(input.value) < 1) input.value = 1;
        });
    });
});
