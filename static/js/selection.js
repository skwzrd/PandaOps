

// Code for handling the processes related to
// selecting a df from the dropdown menu


function makeUL(array) {
    // create a <ul> from a js array
    var list = document.createElement('ul');

    for (var i = 0; i < array.length; i++) {
        var item = document.createElement('li');
        item.appendChild(document.createTextNode(array[i]));
        list.appendChild(item);
    }
    return list;
}


function update_loaded_df_list() {
    // updates the dropdown menu with available df keys
    // and number of available keys
    
    $.ajax({
        url: "/loaded_dfs",
        type: "get",
        success: function(response) {
            var df_array = JSON.parse(response).toString().split(",");
            var df_UL = makeUL(df_array);
            $('#select_df_button').html("Select (" + df_array.length + ")");
            $("#loaded_dfs").html(df_UL);
        },
        error: function(xhr) {
            alert("error getting loaded dfs.");
        }
    });
}


function get_selected_df(){
    // retrieves the selected df key from the server
    var res = null;
    $.ajax({
        async: false, // needed to assign var res
        url: "/selected_df",
        type: "get",
        success: function(response) {
            res = response;
        },
        error: function(xhr) {
            alert("error getting selected df.");
        }
    });
    return res;
}


$(document).ready( function() {
    // display the sample df if chosen from the Select dropdown
    $('#sample_df').click(function() {
        update_df_key_display("Sample");
        display_df("Sample");
    });
});


$(document).ready( function() {
    // display the df chosen from the Select dropdown
    $("#loaded_dfs").on("click", "li", function(e){
        e.preventDefault();
        e.stopPropagation();

        var df_key = get_df_key_from_button(this);
        var selected_df = get_selected_df();
        if(df_key != selected_df){
            update_df_key_display(df_key);
            display_df(df_key);
        }
     });
});


function get_df_key_from_button(obj){
    return $(obj).text();
}

