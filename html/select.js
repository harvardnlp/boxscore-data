var tab = ""
var word = ""
var total = {}
var ambi = {}
var order = {}



function tab_select(name) {
    if (word == "") return;

    if (name != "") {
        $("#" + name).addClass("sel_tab");
        if (tab != "") {
            $("#" + tab).removeClass("sel_tab");
        }
    }
    tab = name;
    if (word != "") {
        total[word] = tab;
        $("#show").text(JSON.stringify(total))
        $("#" + word).removeClass("sel_word");
        $("#" + word).addClass("fin_word");
        if (ambi[word]) {
            for (key in ambi[word]) {
                $("#" + ambi[word][key][0]).removeClass("ambi_tab");
                $("#" + ambi[word][key][1]).removeClass("ambi_row");
            }
        }
        old = word

        word = ""

        if (name != "") {
            $("#" + tab).removeClass("sel_tab");
            $("#" + tab).addClass("fin_tab");
            tab = ""
        }

        q = name
        while (true) {
            if (q != "") {
                row = $("#" + q).parent()
                table = row.parent()
                first_row = table.children()[1]
                $(row).insertBefore($(first_row))
            }
            old = order[old]
            if (ambi[old].length > 1) {
                break;
            } else {
                q = ambi[old][0][0];
            }
        }
        word_select(old)
    }
}

function word_select(name) {
    console.log(name)
    $("#" + name).addClass("sel_word");
    if (word != "") {
        $("#" + word).removeClass("sel_word");
        if (ambi[word]) {
            for (key in ambi[word]) {
                $("#" + ambi[word][key][0]).removeClass("ambi_tab");
                $("#" + ambi[word][key][1]).removeClass("ambi_row");
            }
        }
    }

    word = name;
    if (ambi[word]) {
        for (key in ambi[word]) {
            $("#" + ambi[word][key][0]).addClass("ambi_tab");
            $("#" + ambi[word][key][1]).addClass("ambi_row");
        }
    }

}


function init(d, am, ord) {
    total = d;
    $("#show").text(JSON.stringify(total))
    ambi = am
    for (key in ambi) {
        $("#" + key).addClass("ambi_word");
    }
    for (key in total) {
        $("#" + key).addClass("fin_word");
        $("#" + key).removeClass("ambi_word");
        $("#" + total[key][0]).addClass("fin_tab");
    }
    order = ord


    old = order[""]
    while (ambi[old].length == 1) {
        old = order[old]
    }
    word_select(old)
}
