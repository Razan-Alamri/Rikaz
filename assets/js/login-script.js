$('.form').find('input, textarea').on('keyup blur focus', function(e) {

    var $this = $(this),
        label = $this.prev('label');

    if (e.type === 'keyup') {
        if ($this.val() === '') {
            label.removeClass('active highlight');
        } else {
            label.addClass('active highlight');
        }
    } else if (e.type === 'blur') {
        if ($this.val() === '') {
            label.removeClass('active highlight');
        } else {
            label.removeClass('highlight');
        }
    } else if (e.type === 'focus') {

        if ($this.val() === '') {
            label.removeClass('highlight');
        } else if ($this.val() !== '') {
            label.addClass('highlight');
        }
    }

});

$('.tab a').on('click', function(e) {

    e.preventDefault();

    $(this).parent().addClass('active');
    $(this).parent().siblings().removeClass('active');

    target = $(this).attr('href');

    $('.tab-content > div').not(target).hide();

    $(target).fadeIn(600);

});


$(document).ready(function() {
    // Handle login form submission
    $('#login-form').submit(function(e) {
        e.preventDefault(); // Prevent form submission

        // Perform login form validation
        var email = $('#login-email').val();
        var password = $('#login-password').val();

        if (email === '' || password === '') {
            alert('Please fill in all fields.');
            return;
        }

        // Additional validation logic if needed

        // Redirect to the dashboard page
        window.location.href = "dashboard.html";
    });

    // Handle sign-up form submission
    $('#signup-form').submit(function(e) {
        e.preventDefault(); // Prevent form submission

        // Perform sign-up form validation
        var firstName = $('#signup-firstname').val();
        var lastName = $('#signup-lastname').val();
        var email = $('#signup-email').val();
        var password = $('#signup-password').val();

        if (firstName === '' || lastName === '' || email === '' || password === '') {
            alert('Please fill in all fields.');
            return;
        }

        // Additional validation logic if needed

        // Redirect to the dashboard page
        window.location.href = "dashboard.html";
    });
});