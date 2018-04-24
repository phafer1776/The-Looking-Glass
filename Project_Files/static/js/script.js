$(document).ready(function() {
    // Show the Login / Sign Up overlay.
    $('.signup-link').on('click', function() {
        document.getElementById("overlay").style.display = "inline";
        document.getElementById("overlay-inner").style.display = "inline";
    });
    $('#login-button').on('click', function() {
        $.ajax({
            url: '../../Login',
            data: $('#form-login').serialize(),
            type: 'POST',
            success: function(response) {
                console.log(response);
                if (response.authenticated === true) {
                    localStorage.setItem('userdata', JSON.stringify(response.user));
                    populateUser();
                    location = '../../Dashboard';
                }
                else {
                    $('#alert-message-login').text('Incorrect username or password.');
                }
            },
            error: function(error) {
                console.log(error);
            }
        });
    });
    $('#signup-button').on('click', function() {
        // $('#form-signup').find("input[name=firstName], textarea").val(validateName(textContent));
        // $('#form-signup').find("input[name=lastName], textarea").val(validateName(textContent));
        $.ajax({
            url: '../../SignupUser',
            data: $('#form-signup').serialize(),
            type: 'POST',
            success: function(response) {
                console.log(response);
                if (response.registered === true) {
                    // Clear the input from the text boxes
                    $('#form-signup').find("input[type=text], textarea").val("");
                    $('#form-signup').find("input[type=password], textarea").val("");
                    $('#alert-message-signup').text('Successfully signed up!');
                }
                else {
                    $('#alert-message-signup').text('Signup Error! Please try again.');
                }
            },
            error: function(error) {
                console.log(error)
            }
        });
    });

    // Hide the Login / Sign Up overlay when clicked outside of inner section.
    $(document).mouseup(function(e) {
        var inner = $('#overlay-inner');
        if (e.target.id != inner.attr('id') && !inner.has(e.target).length) {
            inner.fadeOut();
            $('#overlay').fadeOut();
        }
    });

    // Helper function to run regex on a string
    function isAlpha(str) {
        return /^[a-zA-Z ]+$/.test(str);
    }

    function populateUser() {
        var user = JSON.parse(localStorage.getItem('userdata'));
        console.log(user);
        $('.greeting').append(user.firstName);
    }

    // Verify that name is alphabetic and capitalize the first letter to keep DB consistent.
    function validateName(str) {
        if (isAlpha(str)) {
            return str.charAt(0).toUpperCase() + str.slice(1);
        }
        else {
            $('#alert-message-signup').text('First name and last name may only contain alphabetic characters.')
        }
    }

});
