

// Code for handling df operations


function operate_df(operation)
{
    // asks the server for a given df and displays it if it's found
    $.ajax({
        url: "/operate_df",
        type: "get",
        data: {command: operation},
        success: function(response) {
            $("#df").html(response);
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

