let domains = [];
let game = null;
let result = -1;
let modal_on =  false;

$(function() {
    $('[data-toggle="popover"]').popover();
    if (user_id != "None") {
        $.get("/api/game/init", function (d, status) {
            $.get("/api/domains", function (d, status) {
                domains = d;
                get_game();
            });
        });
        update_game_cnt();
    }
    // $('.django-select2').djangoSelect2({placeholder: 'Select an option'});
    $("#tie").click(function(){
        if (result == 0.5)
            result = -1;
        else
            result = 0.5;
        save_game();
    });
    $("#player0_link").click(function() {
        result = 1;
        save_game();
    });
    $("#player1_link").click(function() {
        result = 0;
        save_game();
    });
    $("#leader_tab").click(function() {
        let div = $("#leader_board_list");
        div.empty();
        $.get("/api/game/count", function(d, status){
            d.forEach(function(cnt, i){
                let tmp_user_id = cnt.user__id == undefined ? 'Not played': cnt.user__id;
                let hl = "";
                // highlight logged in user
                if (tmp_user_id == user_id)
                 hl = " class='text-info'";
                let tr = `<tr${hl}>
                    <th scope="row">${i+1}</th>
                    <td>${tmp_user_id} </td>
                    <td>${cnt.cnt}</td>
                </tr>`;
                div.append(tr);
            })
        });
    });

    $("#survey_btn").click(function() {
        $(this).blur();
        let base_url = 'https://redcap.vanderbilt.edu/surveys/?s=MN3DFJ33NL&';
        let url = base_url + 'username=' + user_id + '&casenum=' + game.id;
        window.open(
            url,
            '_blank' // <- This is what makes it open in a new window.
        );
    });
    $("#inst_add").click(function() {
        let inst_name = $("#inst_name").val();
        if (inst_name != "" || inst_name != undefined){
            let institution = {
                name: inst_name,
            };
            save_institution(institution);
        }
    });
    $('#skipModal').on('shown.bs.modal', function (e) {
        modal_on = true;
        $('#skip').one('focus', function(e){$(this).blur();});
    })
    $('#skipModal').on('hidden.bs.modal', function (e) {
        modal_on = false;
    })
    $("#skip_confirm").click(function() {
        let choice = $("input[name='skipActions']:checked")[0].value;
        let action = {
            action_type: 'SKIP',
            time_stamp: new Date()
        };
        if (choice == '0')
        {
            action.game = game.id;
            save_skip_action(action);
        }
        else if (choice == '3')
        {
            action.patient = game.player1.id;
            save_skip_action(action);
            action.patient = game.player2.id;
            save_skip_action(action);
        }
        else if (choice == '1')
        {
            action.patient = game.player1.id;
            save_skip_action(action);
        }
        else if (choice == '2')
        {
            action.patient = game.player2.id;
            save_skip_action(action);
        }
        get_game();
    });
});
/* add hot key. f for case 1, j for case 2, space for tie */
$(document).on('keydown', function ( e ) {
    //ignore keyboard events when modal is on
    if (modal_on) return;
    if(game != null) {
        let key = String.fromCharCode(e.which).toLowerCase();
        if (e.which == 32) {
            result = 0.5
            save_game();
        }
        else if (key === 'f') {
            result = 1;
            save_game();
        } else if (key === 'j') {
            result = 0;
            save_game();
        }
        else
            reset();
    }
    else
        get_game();
});

function reset(){
    result = -1;
    $("#player0_link").addClass("btn-light").removeClass("btn-info");
    $("#player1_link").addClass("btn-light").removeClass("btn-info");
}

function update_game_cnt()
{
    $.get("/api/game/count/" + user_id, function(d, status){
        $("#game_cnt").text(d);
    });
}

function save_institution(institution)
{
    $.ajax({
        url:"/api/institutions/",
        type:"POST",
        data:JSON.stringify(institution),
        contentType:"application/json; charset=utf-8",
        dataType:"json",
        beforeSend: function (xhr, settings) {
            xhr.setRequestHeader("X-CSRFToken", window.CSRF_TOKEN);
        },
        complete: function(xhr, textStatus) {
            let status = xhr.status;
            if (status == '303')
                alert(institution.name + " already exists");
            else if (status == '201')
                $('#instModal').modal('toggle');
            else
                alert("error adding " + institution.name);
        }
    });
}
function save_skip_action(action)
{
    $.ajax({
        url:"/api/actions/",
        type:"POST",
        data:JSON.stringify(action),
        contentType:"application/json; charset=utf-8",
        dataType:"json",
        beforeSend: function (xhr, settings) {
            xhr.setRequestHeader("X-CSRFToken", window.CSRF_TOKEN);
        },
        success: function(ret){
            $('#skipModal').modal('toggle');
        }
    });
}

function save_game()
{
    if (result <0 || result > 1)
        return;
    highlight_winner();
    game.result = result;
    game.time_stamp = new Date();

    $.ajax({
        url:"/api/games/"+ game.id + "/",
        type:"PATCH",
        data:JSON.stringify(game),
        contentType:"application/json; charset=utf-8",
        dataType:"json",
        beforeSend: function (xhr, settings) {
            xhr.setRequestHeader("X-CSRFToken", window.CSRF_TOKEN);
        },
        success: function(ret){
            update_game_cnt();
            get_game();
        }
    });
}

function get_game(){
    if (user_id == undefined || user_id == 'None') return;
    $.get("/api/game/generate/" + user_id, function(g, status){
        game = g;
        let match = [g.player1, g.player2];
        reset();
        match.forEach(function(e, i){
            let div = $("#player" + i + "_info");
            div.empty();
            domains.forEach(function(d, j){
                let domain_entry = e['domain' + d.id] ;
                if (domain_entry != null) {
                    let p = "<p class='text-left text-wrap'>" + domain_entry + "</p>"
                    div.append(p);
                }
            });
        });
    });
}

function highlight_winner()
{
    if (result == 0.5)
    {
        $("#player0_link").addClass("btn-info").removeClass("btn-light");
        $("#player1_link").addClass("btn-info").removeClass("btn-light");
    }
    else if (result == 0 || result == 1){
        let winner_index = Math.abs(result -1);
        $("#player" + winner_index + "_link").addClass("btn-info").removeClass("btn-light");
        $("#player" + result + "_link").addClass("btn-light").removeClass("btn-info");
    }
    else
        reset();
}



$(document).ready(function() {
    console.log($('#leader_board table #leader_board_list .text-info th').html());
    i = parseInt($('#leader_board table #leader_board_list .text-info th').html());
    var j = i % 10,
        k = i % 100;
        if (j == 1 && k != 11){
            tnum = i + "st";
        }
        if (j == 2 && k != 12){
            tnum = i + "nd";
        }
        if (j == 3 && k != 13){
            tnum = i + "rd";
        } else {
            tnum = i + "th";
        }
     $('.leader_tab .ranking').html(tnum);
console.log(tnum);

        $.fn.rowCount = function() {
            return $('tr', $(this).find('tbody')).length;
        };

        $('#tcounter').html($('#leader_board_list').rowCount());
});