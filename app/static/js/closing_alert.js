var closeBtn = document.querySelector('#success-alert .close');

closeBtn.addEventListener('click', function() {
    var alert = document.querySelector('#success-alert');
    alert.style.display = 'none';
});
