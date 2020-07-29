

// Code for handling the left menu


function set_menu_left(data){
    $("#duplicates").html(data['duplicates'].toString());
}


function update_menu_left(){
    // asks the server for df metadata
    $.ajax({
        url: "/left_menu_data",
        type: "get",
        success: function(response) {
            let resp = JSON.parse(response);
            set_menu_left(resp);
        },
        error: function(xhr) {
            alert("error getting sample df.");
        }
    });
}

