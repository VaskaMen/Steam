$(document).ready(function() {
    $('form').on('submit', function(e){
        $.ajax({
            data: {
                link : $("#link").val()
            },
            type : 'POST',
            url : '/linkPrice',
            beforeSend : function () {
                $('.loader').css('display', 'flex');
            }
        }).done(function (data) {
            $('.loader').css('display', 'none');
            $('#big_name').css('color', '#C3CDD2');
            if (data.status == 0){
                document.querySelector("#name").textContent = `${data.name_game}`;
                document.querySelector("#big_name").textContent = `${data.name_game}`;
                $("#image").css('background-image', `url(${data.image})`);
    
                document.querySelector("#usa").textContent = `${data.poluchiUSD.final_formatted} /~ ${data.poluchiUSD.poluchiUSD_RUB}₽`;
                document.querySelector("#ru").textContent = `${data.poluchiRUB.final_formatted}₽`;
                document.querySelector("#try").textContent = `${data.poluchiTRY.final_formatted} /~ ${data.poluchiTRY.poluchiTRY_RUB}₽`;
                document.querySelector("#kzt").textContent = `${data.poluchiKZT.final_formatted} /~ ${data.poluchiKZT.poluchiKZT_RUB}₽`;
                if (data.poluchiUSD.dlc.lenght != 0)
                    send(data.poluchiUSD.dlc);
            }
            else{
                document.querySelector("#big_name").textContent = `Error, pleas try again`;
                $('#big_name').css('color', 'rgb(122, 32, 32)');
            }

          
           
        });
    
        e.preventDefault();
        console.log('1');
    });
});

function send(dlc_list){
    
    $.ajax({
        data: JSON.stringify({
                dlc: dlc_list
            }),

        contentType: 'application/json',
        type : 'POST',
        url : '/dlcPrice',
        beforeSend : function () {
            // $('.loader').css('display', 'flex');
        }
    }).done(function (data) {
        // $('.loader').css('display', 'none');
        $('#big_name').css('color', '#C3CDD2');
        if (data.status == 0){
            
        }
        else{
            document.querySelector("#big_name").textContent = `Error, pleas try again`;
            $('#big_name').css('color', 'rgb(122, 32, 32)');
        }
    });


}

