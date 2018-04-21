$(document).ready(function() {
    $('#signup-link').on('click', function() {
        document.getElementById("overlay").style.display = "block";
        document.getElementById("overlay-inner").style.display = "block"
    });
    $('#login-button').on('click', function() {
        $.ajax({
            url: '/Login',
            data: $('#form-login').serialize(),
            type: 'POST',
            success: function(response) {
                console.log(response);
                if (response.authenticated === true) {
                    localStorage.setItem('userdata', JSON.stringify(response.user));
                    populateUser();
                }
                else {
                    $('#errorMessageLogin').text('Incorrect login information.');
                }
            },
            error: function(error) {
                console.log(error);
            }
        });
    });
    $('signup-button').on('click', function() {
        $.ajax({
            url: '/SignupUser',
            data: $('#form-signup').serialize(),
            type: 'POST',
            success: function(response) {
                console.log(response);
                if (response.registered === true) {
                    $('#errorMessageSignup').text('Signup successful!');
                }
                else {
                    $('#errorMessageSignup').text('Error! Please try again.');
                }
            },
            error: function(error) {
                console.log(error)
            }
        });
    });
    function populateUser() {
        var user = JSON.parse(localStorage.getItem('userdata'));
        console.log(user);
        $('#greeting').append(user.firstName);
    }
});