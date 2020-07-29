

// Code for handling file uploads


function upload_df(){
    // once a csv is chosen, submit it - dont require submit button
    console.log(this);
    $(this).change(function() {
        $(this).submit();
    });
}


$(document).ready( function() {
    // uploading a csv file

    // https://stackoverflow.com/a/20107080/9576988
    $(document).on("change", "#upload_df", function() {
        var obj = $('#upload_df');
        var form_data = new FormData(obj[0]);
        $.ajax({
            type: 'POST',
            url: '/upload_df',
            data: form_data,
            cache: false,
            // https://stackoverflow.com/a/45850898/9576988
            contentType: false,
            processData: false,
            success: function(response) {
                var df_name = $('input[type=file]').val().split('\\').pop()
                update_page(df_name, response);
            },
            error: function(data) {
                alert("error uploading df.")
            },
        });
    });
});

