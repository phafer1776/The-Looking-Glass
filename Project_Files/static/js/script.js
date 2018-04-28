/**********************************************************************************************************************
* JavaScript event handlers and functions for The Looking Glass
* Advanced Python - Spring 2018 - University of South Florida
* Group 2: Paul Hafer, Conner Wulf, Timothy Carney, Denis Saez Rodriguez, Joshua Imarhiagbe
**********************************************************************************************************************/
$(document).ready(function() {

    // Show the Login / Sign Up overlay.
    $('.signup-link').on('click', function() {
        document.getElementById("overlay").style.display = "inline";
        document.getElementById("overlay-inner").style.display = "inline";
    });

    // Make an AJAX call to post the form data to the server for authentication and redirect to the Dashboard
    // upon success. Display an error message if login information does not match
    $('#login-button').on('click', function() {
        $.ajax({
            url: '../../Login',
            data: $('#form-login').serialize(),
            type: 'POST',
            success: function(response) {
                console.log(response);
                if (response.authenticated === true) {
                    localStorage.setItem('userdata', JSON.stringify(response.user));
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

    // Make an AJAX call to post the form data to the server to be added to the DB if it is valid data. Clear data from
    // the form upon success. Display an error message if something goes wrong.
    $('#signup-button').on('click', function() {
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

    // Send the search bar text to the server for searching for matches in the DB.
    $('#search-button').on('click', function() {
        window.location.href = '../../Search/' + $('#search-bar').val();
    });

    // Send the comment and rating to the server to add them to the DB.
    $('#send-comment').on('click', function() {
        window.location.href = '../../Photo/' + $('#image-id').text() + '/' + $('#comment-box').val() +
            '/' + $('#rating-selector').val();
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

    // Helper function to verify that name is alphabetic and capitalize the first letter to keep DB consistent.
    // Currently not being used.
    function validateName(str) {
        if (isAlpha(str)) {
            return str.charAt(0).toUpperCase() + str.slice(1);
        }
        else {
            $('#alert-message-signup').text('First name and last name may only contain alphabetic characters.')
        }
    }
});
