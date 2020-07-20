
// LOADED DFs

function update_loaded_df_list(){
    $.ajax({
        url: "/loaded_dfs",
        type: "get",
        success: function(response) {
            $("#loaded_dfs").html(response);
        },
        error: function(xhr) {
            alert("error getting loaded dfs.");
        }
    });
}




// SAMPLE DF

// asks the server for a given df and displays it if it's found
function display_df(df_name)
{
    $.ajax({
        url: "/display_df",
        type: "get",
        data: {command: df_name},
        success: function(response) {
            $("#df_display_area").html(response);
            $("#operations").show();
            update_loaded_df_list();
        },
        error: function(xhr) {
            alert("error getting sample df.");
        }
    });
}

$(document).ready( function() {
    // display the sample df if chosen
    $('#sample_df').click(function() {
        display_df("df_sample");
    });
});


$(document).ready( function() {
    // display the sample df if chosen
    $("#loaded_dfs").on("click", "li", function(e){
        e.preventDefault();
        e.stopPropagation();
        var selected_df = $(this).text();
        display_df(selected_df);
     });
});

// DF CACHE

// clear df cache on server
$(document).ready( function() {
    // display the sample df if chosen
    $('#clear_df_cache').click(function() {
        $.ajax({
            url: "/clear_df_cache",
            type: "get",
            data: {command: "all"},
            success: function(response) {
                $("#operations").hide();
                $("#df_display_area").html("");
                update_loaded_df_list();
            },
            error: function(xhr) {
                alert("error clearing df cache.");
            }
        });
    });
});



// DF UPLOAD

function upload_df(){
    console.log(this);
    $(this).change(function() {
        $(this).submit();
    });
}

$(document).on("change", "#upload_df", function() {
    var form_data = new FormData($('#upload_df')[0]);
    $.ajax({
        type: 'POST',
        url: '/upload_df',
        data: form_data,
        contentType: false,
        cache: false,
        processData: false,
        success: function(response) {
            $("#df_display_area").html(response);
            $("#operations").show();
            update_loaded_df_list();
        },
        error: function(data) {
            alert("error uploading df.")
        },
    });
});




// DF OPERATIONS

// asks the server for a given df and displays it if it's found
function operate_df(operation)
{
    $.ajax({
        url: "/operate_df",
        type: "get",
        data: {command: operation},
        success: function(response) {
            $("#df_display_area").html(response);
        },
        error: function(xhr) {
            alert("error making operation on df.");
        }
    });
}


$(document).ready( function() {
    // display the sample df if chosen
    $("#operations > button:contains('All')").click(function() {
        operate_df("All");
    });
    $("#operations > button:contains('Head')").click(function() {
        operate_df("Head");
    });
    $("#operations > button:contains('Tail')").click(function() {
        operate_df("Tail");
    });
    $("#operations > button:contains('Stats')").click(function() {
        operate_df("Stats");
    });
});
