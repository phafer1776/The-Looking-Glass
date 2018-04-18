$(document).ready(function() {
    $('#signup-link').on('click', function () {
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
                if (response.authentication === true) {
                    localStorage.setItem('userdata', JSON.stringify(response.user));
                    populateUser();
                }
                else {
                    $('#errorMessageLogin').text('Incorrect login information.');
                }
            },
            error: function (error) {
                console.log(error);
            }
        });
    });

    // function show_overlay() {
    //     document.getElementById("overlay").style.display = "block";
    //     document.getElementById("overlay-inner").style.display = "block"
    // }
    //
    // function hide_overlay() {
    //     document.getElementById("overlay").style.display = "none";
    // }

    function populateUser() {
        var user = JSON.parse(localStorage.getItem('userdata'));
        console.log(user);
        $('#greeting').append(user.firstName);
    }
});