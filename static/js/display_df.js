

// Code for handling processes related to displaying dfs


function update_page(df_key, df_html) {
    // given a df key and a df html table,
    // execute our update routine

    $("#operations").show();
    $("#select_df_dropdown").show();

    $("#df").html(df_html);

    update_loaded_df_list();
    update_df_key_display(df_key);
    update_menu_left();
}


function clear_page(){
    // executes our clear routine

    $("#operations").hide();
    $("#select_df_dropdown").hide();
    
    $("#df").html("No dataframe selected.");

    update_loaded_df_list();
    update_df_key_display("");
    set_menu_left({'duplicates': 'None'});
}


function update_display_with_rows(rows) {
    // get the <tr> elements from the rows parameter
    // the rows parameter has the structure <body> -> <tbody> -> <tr>
    let d = document.createElement('div');
    d.innerHTML = rows;
    let new_rows = d.firstChild.childNodes[1].childNodes;
    let i = 1;
    while(i < new_rows.length){
        let new_row = new_rows[i];
        $(".dataframe > tbody").append(new_row);
        i+=1;
    }
}


$(document).ready( function() {
    // handles loading more df rows
    $(window).scroll(function() {
        // has the user scrolled to the bottom of the page?
        if($(window).scrollTop() == $(document).height() - $(window).height()) {
            $.ajax({
                url: "/check_df_rows",
                type: "get",
                success: function(response) {
                    var resp = JSON.parse(response);
                    if (resp["loading_complete"] === false && resp['display_all'] === true){
                        console.log('Adding more rows');
                        update_display_with_rows(resp["rows"])
                    }
                    else{
                        console.log('All rows loaded or \'All\' not selected.')
                    }
                },
                error: function(xhr) {
                    alert("error updating rows.");
                }
            });
        }
    });
});


function display_df(df_key) {
    // asks the server for a given df and displays it if it's found
    $.ajax({
        url: "/display_df",
        type: "get",
        data: {command: df_key},
        success: function(response) {
            update_page(df_key, response);
        },
        error: function(xhr) {
            alert("error getting sample df.");
        }
    });
}


function update_df_key_display(name){
    $('#df_key').html(name);
}

