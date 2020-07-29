

// Code for handling processes related to the server's cache


// clear df cache on server
$(document).ready( function() {
    // display the sample df if chosen
    $('#clear_df_cache').click(function() {
        $.ajax({
            url: "/clear_df_cache",
            type: "get",
            data: {command: "all"},
            success: function(response) {
                clear_page();
            },
            error: function(xhr) {
                alert("error clearing df cache.");
            }
        });
    });
});

