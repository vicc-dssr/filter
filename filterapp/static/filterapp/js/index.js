
$(document).ready(function() {

    $(".tcasea").each(function(){
        $(this).mouseover(function() {
            $(this).addClass('effect2');
        }).mouseout(function() {
            $(this).removeClass('effect2');
        });
    });
});


function dokeypress(event) {
  var x = event.keyCode;
  var jq,imgs = "";

  if (x == 102) {  // 27 is the f key
    jQuery('.keyf').attr("src",'/static/filterapp/images/keys_on_07.jpg');
    jq='keyf'; imgs='/static/filterapp/images/keys_07.jpg';
  } else if(x == 106){// is the j key
    jQuery('.keyspace').attr("src",'/static/filterapp/images/keys_on_11.jpg');
    jq='keyspace'; imgs='/static/filterapp/images/keys_11.jpg';
  } else if(x == 32){// is the spacebar
    jQuery('.keyj').attr("src",'/static/filterapp/images/keys_on_09.jpg');
    jq='keyj'; imgs='/static/filterapp/images/keys_09.jpg';
  }

    $('.'+jq).fadeOut(100, function() {
        $('.'+jq).attr("src",imgs);
        $('.'+jq).fadeIn(100);
    });

}
document.addEventListener('keypress', dokeypress);